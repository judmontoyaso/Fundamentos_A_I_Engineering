"""
run.py — arranca la API del curso. Desde la carpeta backend/:
    python run.py
API en http://127.0.0.1:8000  (documentación interactiva en /docs)
"""
import os
import uvicorn

if __name__ == "__main__":
    # solo localhost: el kernel ejecuta Python en tu máquina
    uvicorn.run(
        "curso_api.main:app",
        host="127.0.0.1",
        port=int(os.getenv("API_PORT", "8000")),
        # Recarga apagada por defecto: en Windows, con PyTorch cargado en el kernel, el
        # proceso viejo no termina de cerrarse y el nuevo nunca arranca. Los módulos del
        # curso se descubren solos (content.py), así que no hace falta reiniciar para verlos.
        reload=os.getenv("API_RELOAD", "0") == "1",
    )
