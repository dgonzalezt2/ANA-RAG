import os
import sys
import traceback

print('Python executable:', sys.executable)
print('Python version:', sys.version)

path = 'vector_index.faiss'
print('\nComprobando archivo:', path)
print('exists:', os.path.exists(path))
if os.path.exists(path):
    print('size (bytes):', os.path.getsize(path))

try:
    import faiss
    print('\nFAISS module:', faiss)
    try:
        print('Attempting to read index...')
        idx = faiss.read_index(path)
        print('Índice leído OK: ntotal=', idx.ntotal)
        if hasattr(idx, 'd'):
            print('dimensión (d)=', idx.d)
    except Exception as e:
        print('Error al leer el índice:')
        traceback.print_exc()
except Exception as e:
    print('No se pudo importar faiss. Error:')
    traceback.print_exc()
