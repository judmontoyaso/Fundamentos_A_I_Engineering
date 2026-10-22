# Backend · API del curso (FastAPI)

API REST que sirve el contenido del curso como notebooks, ejecuta celdas de Python con estado por notebook, y
guarda progreso y ediciones en SQLite. **No sirve el frontend**: ese es otro proyecto (`../frontend`).

## Arrancar

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # y rellena tus API keys
python run.py
```

O doble clic en `iniciar-backend.bat`. La API queda en `http://127.0.0.1:8000` y su documentación interactiva
(Swagger) en `http://127.0.0.1:8000/docs`.

Para que los laboratorios que usan LLMs, embeddings o Qdrant funcionen, instala en este mismo venv las dependencias
de cada módulo:

```bash
pip install -r ../../modulo-01-datos-estructurados/code/requirements.txt
pip install -r ../../modulo-02-embeddings-busqueda-semantica/code/requirements.txt
pip install -r ../../modulo-03-chunking-metadata-rag/code/requirements.txt
```

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/health` | Estado y carpeta del curso que está leyendo |
| GET | `/api/modules` | Navegación (módulos y notebooks) + progreso |
| GET | `/api/notebook/{id}` | Celdas de un notebook (con tus ediciones aplicadas) |
| POST | `/api/run` | Ejecuta código en el kernel del notebook `{session_id, code}` |
| POST | `/api/session/{id}/reset` | Borra las variables del kernel de ese notebook |
| POST | `/api/cell/save` | Guarda tu edición de una celda |
| POST | `/api/cell/reset` | Devuelve una celda a su código original |
| POST | `/api/progress` | Marca un notebook como leído o no |

## Configuración (`.env`)

| Variable | Por defecto | Uso |
|---|---|---|
| `FRONTEND_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Orígenes permitidos por CORS |
| `COURSE_ROOT` | carpeta `REA/` | De dónde leer los módulos |
| `DB_PATH` | `data/curso.db` | Archivo SQLite |
| `API_PORT` / `API_RELOAD` | `8000` / `0` | Puerto y recarga automática (apagada: en Windows se cuelga con PyTorch cargado) |
| `OPENAI_API_KEY`, etc. | — | Llegan al kernel para los ejercicios |

## Módulos nuevos

La API **descubre los módulos sola**: cada carpeta `modulo-NN-*` de la raíz del curso con un `README.md` aparece en
la navegación, con su `ejercicios.md` y su laboratorio (`code/*.py`) si existen. El título del grupo es el primer
`# encabezado` del README. No hace falta tocar código ni reiniciar la API.

Si cambias el **código del backend** (`curso_api/*.py`), sí hay que reiniciarla.

## Estructura

```
backend/
  curso_api/
    main.py      # rutas FastAPI + CORS
    content.py   # .md y code/ -> notebooks (fragmentos y laboratorio)
    kernel.py    # ejecución de celdas con estado por notebook
    db.py        # SQLite: progreso, ediciones, historial de ejecuciones
  data/curso.db  # se crea sola
  run.py
```

## Seguridad

El kernel ejecuta Python arbitrario **en tu máquina**. La API escucha solo en `127.0.0.1` y el CORS solo admite al
frontend local. Es para uso personal, el mismo modelo de confianza que Jupyter: no la expongas a una red.
