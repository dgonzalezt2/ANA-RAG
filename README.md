# ANA-RAG — Guía de ejecución

Este README explica paso a paso cómo instalar y ejecutar la aplicación (frontend Next.js + backend FastAPI), cómo regenerar la base vectorial FAISS y cómo resolver errores comunes en Windows (PowerShell).

## Requisitos mínimos
- Windows (PowerShell) — instrucciones con comandos para PowerShell.
- Node.js 18+ y npm (o pnpm) para el frontend.
- Python 3.10+ (en tu sistema se detectó Python 3.12) y pip.
- Conexión a Internet para descargar modelos (si no están cacheados).

## Archivos relevantes
- `package.json` — scripts y dependencias del frontend Next.js.
- `api.py` — backend FastAPI que carga `vector_index.faiss`, `docs.pkl` y usa Hugging Face.
- `build_vector_db.py` — script para generar `vector_index.faiss` y `docs.pkl` a partir de `analisis.csv`.
- `analisis.csv` — datos de entrada (debe contener la columna `analisis`).
- `vector_index.faiss`, `docs.pkl` — artefactos generados por `build_vector_db.py`.

---

## 1) Preparar el entorno Python (backend)
1. Abre PowerShell en la carpeta del proyecto (ej. `D:\Datos\Documents\GitHub\ANA-RAG`).
2. Recomiendo crear un entorno virtual (opcional pero recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instala dependencias Python. Si el repositorio tiene `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Si no, instala las dependencias necesarias (ejemplo mínimo):

```powershell
pip install fastapi uvicorn faiss-cpu sentence-transformers pandas numpy huggingface-hub pydantic
```

Nota: en Windows, `faiss-cpu` suele funcionar; si tienes problemas busca la rueda compatible con tu Python/arquitectura.

4. Establece la variable de entorno `HF_TOKEN` (token de Hugging Face) antes de arrancar la API:

```powershell
$env:HF_TOKEN = "tu_token_aqui"
```

Sustituye `tu_token_aqui` por tu token real. Alternativamente, puedes exportarla permanentemente en las variables de entorno del sistema.

---

## 2) Generar (o regenerar) la base FAISS
Si todavía no existen `vector_index.faiss` y `docs.pkl`, o si al arrancar `api.py` recibes un error tipo:

```
Error: 'idxf->codes.size() == idxf->ntotal * idxf->code_size' failed
```

significa que el archivo `.faiss` está corrupto o incompatible. Para generar/regenear:

1. Comprueba que `analisis.csv` exista y tenga la columna `analisis`:

```powershell
python - <<'PY'
import pandas as pd
df = pd.read_csv('analisis.csv')
print('Columnas:', df.columns.tolist())
print('Filas:', len(df))
PY
```

2. (Opcional) elimina archivos viejos corruptos:

```powershell
Remove-Item .\vector_index.faiss, .\docs.pkl -ErrorAction SilentlyContinue
```

3. Ejecuta el generador:

```powershell
python build_vector_db.py
```

- Este script usa `sentence-transformers` para generar embeddings y guarda `vector_index.faiss` y `docs.pkl`.
- Si la descarga del modelo falla por falta de red, revisa conexión o descarga el modelo manualmente.

---

## 3) Ejecutar el backend (API)
Tras instalar dependencias y generar la base vectorial, inicia la API:

```powershell
# Con uvicorn (recomendado para desarrollo)
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# O ejecutando el script (usa uvicorn internamente)
python api.py
```

Comprueba el endpoint de salud en el navegador o con curl:

```powershell
Invoke-WebRequest http://localhost:8000/health | Select-Object -ExpandProperty Content
```

Endpoints principales:
- `GET /` — información básica.
- `GET /health` — estado y si los recursos (index, docs, embedder, data) están cargados.
- `POST /ask` — enviar JSON con `{ \"question\": \"...\" }` y recibir respuesta.

---

## 4) Ejecutar el frontend (Next.js)
1. Instala dependencias Node (desde la raíz del repo):

```powershell
# Si usas npm
npm install --legacy-peer-deps
# O si prefieres pnpm y tienes pnpm instalado
pnpm install
```

Notas:
- En este proyecto hubo un conflicto de peer-deps con `react@19` vs un paquete (`vaul`) que no declaraba compatibilidad, por eso `--legacy-peer-deps` fue necesario.

2. Arranca el dev server de Next:

```powershell
npm run dev
```

Abre en el navegador `http://localhost:3000` (o el puerto que indique la salida del servidor).

---

## 5) Diagnóstico rápido de errores comunes

A) Error: \"'next' no se reconoce como un comando...\"
- Causa: no se instalaron las dependencias Node o `node_modules/.bin` no contiene `next`.
- Solución: ejecutar `npm install --legacy-peer-deps` o instalar con `pnpm`.

B) Error FAISS al leer índice (mensaje tipo `idxf->codes.size() == idxf->ntotal * idxf->code_size failed`)
- Causa: `vector_index.faiss` corrupto o incompatible con la versión de FAISS instalada.
- Solución:
  1. Elimina `vector_index.faiss` y `docs.pkl` y vuelve a generar con `python build_vector_db.py`.
  2. Asegúrate de instalar `faiss-cpu` compatible con tu Python.
  3. Si tienes una copia buena del `.faiss` (backup), usa esa en su lugar.

C) Conflictos de peer-deps al instalar con npm
- Solución rápida: `npm install --legacy-peer-deps`.
- Solución a largo plazo: alinear versiones de React y paquetes (por ejemplo bajar React a 18 o actualizar la dependencia conflictiva).

D) Problemas al cargar embeddings (sentence-transformers)
- Si `sentence-transformers` intenta descargar modelos y falla por firewall/red, instala el modelo en un entorno con internet o usa `local_files_only=True` cuando sea posible.

---

## 6) Comprobaciones útiles y comandos de diagnóstico
- Comprobar existencia y tamaño del índice:

```powershell
Test-Path .\\vector_index.faiss
Get-Item .\\vector_index.faiss | Select-Object Name, Length
```

- Intentar leer índice con Python (imprime error completo):

```powershell
python - <<'PY'
import faiss, os, traceback
p='vector_index.faiss'
print('exists', os.path.exists(p))
if os.path.exists(p):
	print('size', os.path.getsize(p))
try:
	idx = faiss.read_index(p)
	print('ntotal', idx.ntotal)
except Exception:
	traceback.print_exc()
PY
```

- Mostrar la salud del backend:

```powershell
Invoke-WebRequest http://localhost:8000/health | ConvertFrom-Json
```

---

## 7) Buenas prácticas y recomendaciones
- Mantén un entorno virtual para Python y un `node_modules` limpio por proyecto.
- Haz backup del archivo `vector_index.faiss` si lo regeneras con éxito.
- Para producción, considera usar un servicio de embeddings administrado o persistencia reproducible y versionada de los artefactos.

---

Si quieres, puedo:
- Añadir un script `diag_faiss.py` que ejecute comprobaciones automáticamente y lo deje en el repo.
- Modificar `api.py` para que falle de forma tolerante (arranque aunque `vector_index.faiss` esté corrupto) y permita operar en modo degradado.
- Ayudarte a alinear las versiones (React 19 vs dependencias) si prefieres corregir las dependencias en lugar de usar `--legacy-peer-deps`.

Dime cuál prefieres y lo implemento.
