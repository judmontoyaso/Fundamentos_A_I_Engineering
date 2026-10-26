"""
as_comun.py — lo que comparten los laboratorios del curso de AI search.

Reutiliza las piezas de los cursos anteriores en vez de copiarlas:
  ev   : ev_comun del curso de Evals (trazador, llm_cache con caché, norm, HOY).
  c    : 00_comun del Módulo 5 de AI Engineering (INSTRUCCION_CV, como_cv).
  bm25 : el BM25 desde cero del Módulo 4 de AI Engineering.
  embed: el embedder del Módulo 2 de AI Engineering (local con EMB_BACKEND=local).
Los datos del curso (120 CVs y sus hechos) viven en as_cvs.json; los genera as_generar.py una sola vez.
"""
from __future__ import annotations
import json
import pathlib
import sys
from functools import lru_cache
from importlib import import_module

COMUN = pathlib.Path(__file__).resolve().parent
CURSO = COMUN.parent
RAIZ = CURSO.parent
for p in (RAIZ / "curso-evals" / "comun", RAIZ / "modulo-02-embeddings-busqueda-semantica" / "code", COMUN):
    if str(p) not in sys.path:
        sys.path.append(str(p))

ev = import_module("ev_comun")
c, tz = ev.c, ev.tz
bm25 = import_module("01_bm25_desde_cero")
SALIDA = CURSO / "salida"


def embed(textos: list[str]):
    return import_module("06_embeddings_reales").embed(textos)


@lru_cache(maxsize=1)
def cvs() -> list[dict]:
    """Los 120 CVs del curso: id, texto y hechos (los hechos son la verdad; el texto, lo que ve el sistema)."""
    return json.loads((COMUN / "as_cvs.json").read_text(encoding="utf-8"))


def guardar_jsonl(nombre: str, filas: list[dict]) -> pathlib.Path:
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / nombre
    ruta.write_text("\n".join(json.dumps(f, ensure_ascii=False, default=str) for f in filas) + "\n", encoding="utf-8")
    return ruta


def leer_jsonl(nombre: str) -> list[dict]:
    return [json.loads(l) for l in (SALIDA / nombre).read_text(encoding="utf-8").splitlines() if l.strip()]
