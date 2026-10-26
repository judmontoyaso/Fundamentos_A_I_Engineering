"""
ev_rag.py — el RAG que evalúa el Módulo 6: búsqueda híbrida sobre los 30 CVs de ev_datos + respuesta citando.

Recuperación: densa (embedder del Módulo 2 de AI Engineering) y BM25 (Módulo 4), fusionadas con RRF.
Generación: responde SOLO con los CVs recibidos, cita sus números y dice si no hay información.
Las dos mitades se pueden llamar por separado: es lo que permite saber cuál falló.
"""
from __future__ import annotations
import sys
from functools import lru_cache
from importlib import import_module

import numpy as np
from pydantic import BaseModel, Field

ev = import_module("ev_comun")
datos = import_module("ev_datos")
sys.path.append(str(ev.RAIZ / "modulo-02-embeddings-busqueda-semantica" / "code"))
bm25 = import_module("01_bm25_desde_cero")

CVS = {cv["id"]: cv["texto"] for cv in datos.CVS}
IDS = list(CVS)


@lru_cache(maxsize=1)
def _indice():
    embed = import_module("06_embeddings_reales").embed
    m = embed([CVS[i] for i in IDS])
    return m / np.linalg.norm(m, axis=1, keepdims=True), bm25.BM25([CVS[i] for i in IDS])


def buscar(pregunta: str, k: int = 3, profundidad: int = 10) -> list[int]:
    """Ids de los k CVs más relevantes: RRF (k=60) de los rankings denso y BM25."""
    densos, lexico = _indice()
    embed = import_module("06_embeddings_reales").embed
    q = embed([pregunta])[0]
    q = q / np.linalg.norm(q)
    rank_denso = [IDS[i] for i in np.argsort(-(densos @ q))[:profundidad]]
    rank_bm25 = [IDS[i] for i, _ in lexico.buscar(pregunta, profundidad)]
    puntos: dict[int, float] = {}
    for ranking in (rank_denso, rank_bm25):
        for puesto, i in enumerate(ranking, start=1):
            puntos[i] = puntos.get(i, 0.0) + 1 / (60 + puesto)
    return sorted(puntos, key=lambda i: -puntos[i])[:k]


class Respuesta(BaseModel):
    respuesta: str
    cvs_citados: list[int] = Field(description="números de los CVs en los que se basa la respuesta")
    sin_informacion: bool = Field(description="True si los CVs recibidos no permiten responder")


PROMPT = ("Respondes preguntas de un reclutador usando SOLO los CVs que recibes, numerados. Cita los números de los "
          "CVs en los que te basas. Si los CVs no permiten responder, dilo y marca sin_informacion. "
          f"{ev.c.INSTRUCCION_CV.replace('El CV llega', 'Cada CV llega')}")


def responder(pregunta: str, ids: list[int], modelo: str | None = None) -> Respuesta:
    contexto = "\n".join(f"[{i}] {ev.c.como_cv(CVS[i])}" for i in ids) or "(ningún CV)"
    return ev.tz.llm_trazado(Respuesta, PROMPT, f"CVs:\n{contexto}\n\nPregunta: {pregunta}", nombre="rag responder",
                             modelo=modelo)


def rag(pregunta: str, k: int = 3, modelo: str | None = None) -> dict:
    with ev.tz.span("rag", pregunta=pregunta):
        ids = buscar(pregunta, k)
        r = responder(pregunta, ids, modelo)
    return {"recuperados": ids, **r.model_dump()}
