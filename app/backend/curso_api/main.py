"""
main.py — API del curso (solo API: el frontend vive en su propio proyecto).

Arranca desde la carpeta backend/:
    python run.py
o:
    uvicorn curso_api.main:app --host 127.0.0.1 --port 8000 --reload

Escucha solo en 127.0.0.1: el kernel ejecuta Python en tu máquina.
"""
from __future__ import annotations
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# backend/.env -> variables de entorno (API keys que usan los ejercicios del kernel).
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Las barras de progreso (descargas, carga de modelos) ensucian la salida de las celdas.
os.environ.setdefault("TQDM_DISABLE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import asistente, content, kernel, db

# Orígenes del frontend autorizados a llamar a la API (separados por coma).
FRONTEND_ORIGINS = [
    o.strip() for o in os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if o.strip()
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init()
    yield


app = FastAPI(title="Curso AI Engineering · API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- modelos de request ----------
class RunReq(BaseModel):
    session_id: str
    code: str
    file: str | None = None  # ruta del script de laboratorio -> __file__ en el kernel


class EditReq(BaseModel):
    nb_id: str
    cell_idx: int
    source: str = ""


class ProgressReq(BaseModel):
    nb_id: str
    done: bool


class ConsultaReq(BaseModel):
    usuario: str
    pedido: str


class OlvidarReq(BaseModel):
    usuario: str
    recuerdo_id: str


# ---------- API ----------
@app.get("/api/health")
def health():
    return {"ok": True, "course_root": str(content.COURSE_ROOT)}


@app.get("/api/modules")
def modules():
    return {"courses": [{"id": c["id"], "title": c["titulo"]} for c in content.cursos()],
            "nav": content.nav_tree(), "progress": db.get_progress()}


@app.get("/api/notebook/{nb_id}")
def notebook(nb_id: str):
    nb = content.notebook(nb_id)
    if nb is None:
        raise HTTPException(404, "notebook no encontrado")
    # mezclar las ediciones guardadas del usuario sobre las celdas de código
    edits = db.get_edits(nb_id)
    for cell in nb["cells"]:
        if cell["idx"] in edits:
            cell["source"] = edits[cell["idx"]]
            cell["edited"] = True
    return nb


@app.post("/api/run")
def run(req: RunReq):
    res = kernel.run(req.session_id, req.code, file=req.file)
    ok = not res["stderr"] and not res["timed_out"]
    db.log_run(req.session_id, -1, ok)
    return res


@app.post("/api/session/{session_id}/reset")
def reset(session_id: str):
    kernel.reset(session_id)
    return {"ok": True}


@app.post("/api/cell/save")
def cell_save(req: EditReq):
    if not content.exists(req.nb_id):
        raise HTTPException(404, "notebook no encontrado")
    db.save_edit(req.nb_id, req.cell_idx, req.source)
    return {"ok": True}


@app.post("/api/cell/reset")
def cell_reset(req: EditReq):
    db.clear_edit(req.nb_id, req.cell_idx)
    return {"ok": True}


@app.post("/api/progress")
def progress(req: ProgressReq):
    db.set_progress(req.nb_id, req.done)
    return {"ok": True}


@app.get("/api/quiz/{nb_id}")
def quiz(nb_id: str):
    q = content.quiz(nb_id)
    if q is None:
        raise HTTPException(404, "autoevaluación no encontrada")
    return q


# ---------- Asistente del Módulo 9 ----------
@app.get("/api/asistente/estado")
def asistente_estado():
    return asistente.estado()


@app.post("/api/asistente/consultar")
def asistente_consultar(req: ConsultaReq):
    pedido = req.pedido.strip()
    if not pedido or not req.usuario.strip():
        raise HTTPException(400, "faltan el usuario o el pedido")
    try:
        return asistente.consultar(req.usuario.strip().lower(), pedido)
    except Exception as e:          # sin API key, sin dependencias del Módulo 9...
        raise HTTPException(500, f"{type(e).__name__}: {str(e)[:300]}")


@app.get("/api/asistente/memoria/{usuario}")
def asistente_memoria(usuario: str):
    return {"recuerdos": asistente.memoria(usuario.strip().lower())}


@app.post("/api/asistente/olvidar")
def asistente_olvidar(req: OlvidarReq):
    asistente.olvidar(req.usuario.strip().lower(), req.recuerdo_id)
    return {"ok": True}
