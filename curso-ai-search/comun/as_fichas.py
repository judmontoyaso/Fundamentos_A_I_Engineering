"""
as_fichas.py — los METADATOS del índice: una ficha por CV, extraída del TEXTO (no copiada de los hechos).

En producción nadie te da los hechos: los metadatos salen de extraer el texto del CV. Se extraen una vez con el
modelo del .env, con la técnica del Módulo 11 de Evals (el modelo copia trabajos y fechas; los años se suman en
código), y se guardan en as_fichas.json, que es parte del índice. El Módulo 3 mide cuánto se equivocó esta
extracción comparándola con los hechos.
Uso para regenerar: python as_fichas.py   (con el .env de la app cargado)
"""
from __future__ import annotations
import json
import sys
from functools import lru_cache
from importlib import import_module
from typing import Literal

from pydantic import BaseModel, Field

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
ac = import_module("as_comun")
ev = ac.ev

ROLES = Literal["ingeniero de datos", "científico de datos", "analista de datos", "desarrollador backend",
                "desarrollador python", "desarrollador frontend", "ingeniero devops", "arquitecto cloud",
                "qa automation", "desarrollador móvil", "analista de seguridad", "desarrollador .net", "otro"]


class Trabajo(BaseModel):
    cargo: str
    inicio: int | None = None
    fin: int | None = Field(default=None, description="null si sigue vigente")


class FichaIndice(BaseModel):
    rol: ROLES = Field(description="el rol principal del candidato")
    skills: list[str] = Field(description="tecnologías y herramientas, en minúscula, tal como aparecen")
    trabajos: list[Trabajo]
    ciudad: str | None = None
    remoto: bool = Field(description="True si dice que acepta trabajo remoto")
    ingles: Literal["básico", "B1", "B2", "C1", "nativo"] | None = None
    certificaciones: list[str] = Field(default_factory=list)


PROMPT = (f"Extrae la ficha del CV. {ev.c.INSTRUCCION_CV} No inventes. Copia cada trabajo con su cargo y sus años "
          "tal como aparecen (fin null si sigue vigente); no sumes años.")


def anios(f: FichaIndice) -> int:
    cubiertos = set()
    for t in f.trabajos:
        if t.inicio:
            cubiertos |= set(range(t.inicio, t.fin or ev.HOY.year))
    return len(cubiertos)


def nivel(a: int) -> str:
    return "senior" if a >= 7 else "semi-senior" if a >= 3 else "junior"


@lru_cache(maxsize=1)
def fichas() -> dict[int, dict]:
    """id -> ficha extraída, con 'anios', 'nivel' y 'lidera' calculados en código."""
    datos = json.loads((ac.COMUN / "as_fichas.json").read_text(encoding="utf-8"))
    return {int(k): v for k, v in datos.items()}


def extraer(cv: dict) -> dict:
    """cv: {"texto": ...}. Usa la caché del curso de Evals: el mismo texto no se vuelve a extraer."""
    f = ev.llm_cache(FichaIndice, PROMPT, ev.c.como_cv(cv["texto"]), nombre="ficha del índice")
    a = anios(f)
    return {**f.model_dump(), "anios": a, "nivel": nivel(a),
            "lidera": any(ev.norm(t.cargo).startswith(("lider", "lead")) for t in f.trabajos)}


if __name__ == "__main__":
    cvs = ac.cvs()
    with ev.tz.nueva_traza("fichas del índice"):
        res = ev.tz.en_paralelo(extraer, [(cv,) for cv in cvs])
    (ac.COMUN / "as_fichas.json").write_text(json.dumps({cv["id"]: f for cv, f in zip(cvs, res)}, ensure_ascii=False,
                                                        indent=1), encoding="utf-8")
    print(f"{len(res)} fichas guardadas en as_fichas.json (modelo {ev.tz.MODELO})")
