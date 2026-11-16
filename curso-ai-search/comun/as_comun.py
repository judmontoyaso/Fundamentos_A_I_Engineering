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
CURSO_EVALS = RAIZ / "curso-evals"
if not CURSO_EVALS.exists() and (CURSO / "_base" / "curso-evals").exists():
    CURSO_EVALS = CURSO / "_base" / "curso-evals"
CURSO_IA = RAIZ / "curso-ai-engineering"
if not CURSO_IA.exists() and (CURSO / "_base" / "curso-ai-engineering").exists():
    CURSO_IA = CURSO / "_base" / "curso-ai-engineering"
for p in (CURSO_EVALS / "comun", CURSO_IA / "modulo-02-embeddings-busqueda-semantica" / "code", COMUN):
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


# Qué script genera cada archivo intermedio de salida/, para avisar con claridad si todavía no existe.
PRODUCTORES = {
    "linea_base.jsonl": "modulo-01-medir-antes/code/01_linea_base.py",
    "m2_estrategias.jsonl": "modulo-02-query-understanding/code/01_entender_y_filtrar.py",
    "parseos.json": "modulo-03-parsing/code/02_tres_formas_de_parsear.py",
}


def requerir(nombre: str) -> pathlib.Path:
    """Devuelve la ruta de un archivo de salida/ o termina con un mensaje que dice qué script lo genera."""
    ruta = SALIDA / nombre
    if not ruta.exists():
        origen = PRODUCTORES.get(nombre, "el laboratorio anterior de este módulo")
        raise SystemExit(f"Falta salida/{nombre}. Lo genera {origen} (curso de AI Search); córrelo primero.")
    return ruta


def leer_jsonl(nombre: str) -> list[dict]:
    return [json.loads(l) for l in requerir(nombre).read_text(encoding="utf-8").splitlines() if l.strip()]
