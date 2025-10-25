import faiss
import pandas as pd
import pickle
import os
import numpy as np

# === CONFIGURACIÓN ===
# Configurar token de Hugging Face
os.environ["HF_TOKEN"] = "hf_token"
# Archivo que contiene los análisis históricos.
# Puede ser CSV (con columna "analisis") o TXT (una línea por documento)
INPUT_FILE = "analisis.csv"   # o "analisis.txt"
VECTOR_INDEX_FILE = "vector_index.faiss"
DOCS_FILE = "docs.pkl"

# === LECTURA DE LOS ANÁLISIS ===
def load_documents(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
        if "analisis" not in df.columns:
            raise ValueError("El archivo CSV debe tener una columna llamada 'analisis'.")
        docs = df["analisis"].dropna().tolist()
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            docs = [line.strip() for line in f.readlines() if line.strip()]
    else:
        raise ValueError("El archivo debe ser .csv o .txt")
    
    if not docs:
        raise ValueError("No se encontraron análisis en el archivo.")
    return docs

# === CREAR BASE VECTORIAL ===
def build_vector_db(docs):
    print(f"Creando base vectorial con {len(docs)} documentos...")
    
    try:
        # Usar sentence-transformers directamente (más estable)
        from sentence_transformers import SentenceTransformer
        
        print("📥 Cargando modelo sentence-transformers...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Modelo cargado correctamente")
        
        print("Generando embeddings...")
        embeddings = model.encode(docs, show_progress_bar=True)
        
        print(f"✅ Embeddings generados: {embeddings.shape}")
        
        print("Creando índice FAISS...")
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        
        print("Guardando archivos...")
        faiss.write_index(index, VECTOR_INDEX_FILE)
        with open(DOCS_FILE, "wb") as f:
            pickle.dump(docs, f)
        
        print(f"✅ Base vectorial creada y guardada en '{VECTOR_INDEX_FILE}' con {len(docs)} análisis.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica que tengas instalado sentence-transformers:")
        print("   pip install sentence-transformers")
        raise e

if __name__ == "__main__":
    try:
        documentos = load_documents(INPUT_FILE)
        print(f"📄 Documentos cargados: {len(documentos)}")
        for i, doc in enumerate(documentos):
            print(f"  {i+1}. {doc[:50]}...")
        
        build_vector_db(documentos)
        print("\n🎉 ¡Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en el proceso: {e}")
        print("\n💡 Soluciones posibles:")
        print("   1. Instala las dependencias: pip install -r requirements.txt")
        print("   2. Verifica que el archivo analisis.csv existe")
        print("   3. Asegúrate de tener conexión a internet")
        print("   4. Verifica que tienes suficiente espacio en disco")
