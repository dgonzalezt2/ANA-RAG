from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import pickle
import pandas as pd
import warnings
import os
import numpy as np
from typing import Optional
from huggingface_hub import InferenceClient

warnings.filterwarnings("ignore")

# === CONFIGURACIÓN ===
VECTOR_INDEX_FILE = "vector_index.faiss"
DOCS_FILE = "docs.pkl"
DATA_FILE = "produccion.csv"

# === MODELO HUGGING FACE (Nebius provider) ===
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("❌ No se encontró la variable de entorno HF_TOKEN para Hugging Face.")

# Usar exactamente el modelo y provider solicitados, apuntando al Router de HF
client = InferenceClient(
    model="openai/gpt-oss-120b",
    provider="nebius",
    token=HF_TOKEN,
)

# === MODELOS PYDANTIC ===
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    success: bool
    message: Optional[str] = None

# === INICIALIZACIÓN DE FASTAPI ===
app = FastAPI(
    title="ANA-RAG API",
    description="API para Sistema de Recuperación Aumentada por Generación",
    version="1.0.0"
)

# === VARIABLES GLOBALES ===
index = None
docs = None
embedder = None
data = None

# === FUNCIONES DE CARGA ===
def load_resources():
    """Carga todos los recursos necesarios al iniciar la API."""
    global index, docs, embedder, data
    
    print("🔹 Cargando base vectorial...")
    index = faiss.read_index(VECTOR_INDEX_FILE)
    with open(DOCS_FILE, "rb") as f:
        docs = pickle.load(f)

    print("🔹 Cargando modelo de embeddings...")
    try:
        from sentence_transformers import SentenceTransformer
        # Evitar bloqueos por descarga en entornos sin red; si no está en caché, seguimos sin embedder
        embedder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        print("✅ Modelo de embeddings cargado correctamente (modo local)")
    except Exception as e:
        print(f"❌ Error cargando embeddings: {e}")
        embedder = None

    print("🔹 Cargando datos de producción...")
    data = pd.read_csv(DATA_FILE)
    print("✅ Recursos cargados correctamente")

    # Sin fallback local: la generación será exclusivamente vía Hugging Face

# === FUNCIONES RAG ===
def retrieval(query: str, k: int = 3):
    """Recupera documentos relevantes desde la base vectorial FAISS."""
    if embedder is None:
        import random
        return random.sample(docs, min(k, len(docs)))
    
    try:
        q_emb = embedder.encode([query])
        q_emb_np = np.array(q_emb, dtype=np.float32)
        if q_emb_np.ndim == 1:
            q_emb_np = q_emb_np.reshape(1, -1)
        D, I = index.search(q_emb_np, k)
        return [docs[i] for i in I[0]]
    except Exception as e:
        print(f"⚠️  Error en retrieval: {e}")
        import random
        return random.sample(docs, min(k, len(docs)))

def validar_contexto_suficiente(query: str, retrieved_docs: list):
    """Valida si hay suficiente contexto para responder la pregunta."""
    if not retrieved_docs:
        return False
    
    palabras_agricultura = [
        'producción', 'cultivo', 'café', 'maíz', 'flores', 'banano', 'cacao',
        'agricultura', 'cosecha', 'sequía', 'plaga', 'fertilizantes', 'exportación',
        'rendimiento', 'climáticas', 'transporte', 'bajó', 'disminuyó', 'afectada',
        'aumentó', 'redujo', 'condiciones', 'bloqueos', 'costo'
    ]
    
    query_lower = query.lower()
    tiene_contexto_agricola = any(palabra in query_lower for palabra in palabras_agricultura)
    
    documentos_relevantes = sum(
        1 for doc in retrieved_docs if any(p in doc.lower() for p in palabras_agricultura)
    )
    return tiene_contexto_agricola and documentos_relevantes >= 1

def generar_respuesta_llm(query: str, contexto: str):
    """Genera una respuesta usando un modelo pequeño de Hugging Face."""
    system_prompt = (
        "Eres un asistente agrícola experto. si no tienes informacion suficiente, entonces inventa una respuesta basada en el contexto proporcionado y tu conocimeinto"
    )
    user_content = (
        f"=== CONTEXTO ===\n{contexto}\n\n=== PREGUNTA ===\n{query}\n\n=== RESPUESTA ==="
    )

    try:
        # Ruta principal: chat.completions (provider=nebius)
        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        )
        if chat and hasattr(chat, "choices") and chat.choices:
            msg = chat.choices[0].message
            content = getattr(msg, "content", "") if msg else ""
            if content:
                return content.strip()

        # Fallback: text_generation (por compatibilidad)
        response = client.text_generation(
            user_content,
            max_new_tokens=300,
            temperature=0.4,
            do_sample=False,
        )
        if isinstance(response, str):
            return response.strip()
        elif hasattr(response, "generated_text"):
            return response.generated_text.strip()
        elif isinstance(response, dict) and "generated_text" in response:
            return response["generated_text"].strip()
        else:
            return str(response).strip()

    except Exception as e:
        # Log detallado del error para diagnóstico
        try:
            import traceback
            print("⚠️ Error generando respuesta con Hugging Face:")
            print(f"   tipo: {type(e)}")
            print(f"   repr: {repr(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"   status: {getattr(e.response, 'status_code', None)}")
                    print(f"   body: {getattr(e.response, 'text', None)}")
                except Exception:
                    pass
            traceback.print_exc()
        except Exception:
            pass
        return "No pude generar una respuesta con el modelo remoto. Intenta nuevamente."



def ana_rag(query: str):
    """Pipeline completo RAG: Recuperación, Validación, Generación."""
    try:
        # 1) Recuperar top-k documentos relevantes
        retrieved_docs = retrieval(query, k=5)

        # 2) Construir contexto
        contexto = "\n".join([f"- {doc}" for doc in retrieved_docs])

        # 3) Preguntar al LLM con instrucciones para abstenerse si no hay suficiente contexto
        respuesta = generar_respuesta_llm(query, contexto)
        if isinstance(respuesta, str):
            text = respuesta.strip()
            if text.upper().startswith("NO_INFO") or "no tengo información suficiente" in text.lower():
                return "No tengo información suficiente para responder con precisión."
            return text
        return str(respuesta)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando la consulta: {str(e)}")

# === ENDPOINTS ===
@app.on_event("startup")
async def startup_event():
    """Carga los recursos al iniciar la API."""
    load_resources()

@app.get("/")
async def root():
    return {
        "message": "ANA-RAG API - Sistema de Recuperación Aumentada por Generación",
        "version": "1.0.0",
        "endpoints": {
            "POST /ask": "Enviar una pregunta y recibir respuesta",
            "GET /health": "Verificar estado de la API"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "API funcionando correctamente",
        "resources_loaded": {
            "vector_index": index is not None,
            "docs": docs is not None,
            "embedder": embedder is not None,
            "data": data is not None
        }
    }

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Endpoint principal para hacer preguntas al sistema RAG."""
    try:
        if not request.question.strip():
            return AnswerResponse(
                answer="",
                success=False,
                message="La pregunta no puede estar vacía"
            )
        
        answer = ana_rag(request.question)
        return AnswerResponse(answer=answer, success=True, message="Respuesta generada exitosamente")

    except Exception as e:
        return AnswerResponse(
            answer="",
            success=False,
            message=f"Error procesando la pregunta: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
