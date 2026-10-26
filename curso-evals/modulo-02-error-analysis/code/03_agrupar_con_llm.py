"""
03 · ¿Puede un LLM hacer la codificación axial? Agrupar las notas y comparar con la de una persona (manual §5).

El LLM recibe SOLO las notas (lo que escribió quien leyó), no las salidas: agrupar es su tarea;
leer, no. Se compara con la agrupación manual con el índice de Rand: de todos los pares de notas,
qué fracción tratan igual las dos agrupaciones (juntas en ambas, o separadas en ambas).
"""
from __future__ import annotations
import itertools
import pathlib
import sys
from collections import defaultdict
from importlib import import_module

from pydantic import BaseModel, Field

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
m2 = import_module("m2_notas")


class Grupo(BaseModel):
    nombre: str = Field(description="nombre corto del tipo de fallo")
    notas: list[int] = Field(description="números de las notas que pertenecen a este grupo")


class Agrupacion(BaseModel):
    grupos: list[Grupo] = Field(description="entre 4 y 8 grupos; cada nota en exactamente un grupo")


PROMPT = ("Eres un analista de calidad. Recibes notas que una persona escribió al revisar las salidas de un "
          "pipeline que extrae datos de CVs, clasifica el nivel del candidato y redacta un perfil. Agrupa las notas "
          "por TIPO DE FALLO (la causa, no el caso). Cada nota va en exactamente un grupo.")


def rand(a: dict[int, str], b: dict[int, str]) -> float:
    pares = list(itertools.combinations(sorted(a), 2))
    return sum((a[x] == a[y]) == (b[x] == b[y]) for x, y in pares) / len(pares)


if __name__ == "__main__":
    lista = [(i, j, t) for i, ns in m2.NOTAS.items() for j, t in enumerate(ns)]
    texto = "\n".join(f"{k}. {t}" for k, (_, _, t) in enumerate(lista, 1))
    with ev.tz.nueva_traza("agrupar notas con LLM"):
        r = ev.tz.llm_trazado(Agrupacion, PROMPT, texto, nombre="agrupar")

    llm = {}
    for g in r.grupos:
        for k in g.notas:
            llm.setdefault(k, g.nombre)              # si repite una nota, vale el primer grupo
    faltan = [k for k in range(1, len(lista) + 1) if k not in llm]
    manual = {k: m2.NOTA_A_CATEGORIA[(i, j)] for k, (i, j, _) in enumerate(lista, 1)}
    for k in faltan:
        llm[k] = "(sin grupo)"
    print(f"{len(lista)} notas · el LLM propuso {len(r.grupos)} grupos"
          + (f" · dejó sin grupo las notas {faltan}" if faltan else ""))

    print("\nCómo repartió el LLM cada categoría manual:")
    for c in m2.CATEGORIAS:
        ks = [k for k, v in manual.items() if v == c]
        reparto = defaultdict(int)
        for k in ks:
            reparto[llm[k]] += 1
        print(f"  {c:30} -> {dict(reparto)}")
    print(f"\nÍndice de Rand con la agrupación manual: {rand(manual, llm):.2f} (1 = idénticas)")
    print("Léelo así: el LLM ahorra el trabajo mecánico de agrupar, pero sus nombres y sus fronteras son")
    print("decisiones. Revisa cada grupo antes de contarlo, y nunca le dejes la lectura de las salidas.")
