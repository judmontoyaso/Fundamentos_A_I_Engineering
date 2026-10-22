"""
05 · Map-reduce con Send: evaluar candidatos en paralelo (manual §6).

buscar (k candidatos) -> Send("evaluar", ...) uno por candidato -> ranking.
Las evaluaciones se acumulan con un reductor. El número de ramas lo decide el
estado (cuántos candidatos salieron), no el código.
"""
from __future__ import annotations
import operator
import sys
import pathlib
import time
from importlib import import_module
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")
par = import_module("03_paralelizacion")         # Encaje del Módulo 5


class Estado(TypedDict):
    vacante: str
    candidatos: list[dict]
    evaluaciones: Annotated[list[dict], operator.add]   # reduce: cada rama añade la suya
    ranking: list[str]


class Tarea(TypedDict):                                  # lo que recibe CADA rama: solo su porción
    vacante: str
    cv: dict


def buscar(s: Estado) -> dict:
    hits = c.buscar(s["vacante"], modo="hibrida", k=5)
    return {"candidatos": [{"nombre": h.payload["nombre"], "texto": h.payload["texto"]} for h in hits]}


def repartir(s: Estado) -> list[Send]:                   # map
    return [Send("evaluar", {"vacante": s["vacante"], "cv": cv}) for cv in s["candidatos"]]


def evaluar(t: Tarea) -> dict:
    inicio = time.time()
    e = c.llm(par.Encaje, f"Evalúa el CV contra esta vacante: {t['vacante']}. {c.INSTRUCCION_CV}",
              c.como_cv(t["cv"]["texto"]))
    return {"evaluaciones": [{"nombre": t["cv"]["nombre"], "puntaje": e.puntaje, "motivo": e.razonamiento,
                              "inicio": inicio, "fin": time.time()}]}


def ranking(s: Estado) -> dict:
    orden = sorted(s["evaluaciones"], key=lambda e: -e["puntaje"])
    return {"ranking": [f"{e['puntaje']}/5 {e['nombre']}" for e in orden]}


g = StateGraph(Estado)
g.add_node("buscar", buscar)
g.add_node("evaluar", evaluar)
g.add_node("ranking", ranking)
g.add_edge(START, "buscar")
g.add_conditional_edges("buscar", repartir, ["evaluar"])
g.add_edge("evaluar", "ranking")
g.add_edge("ranking", END)
app = g.compile()


if __name__ == "__main__":
    c.reiniciar_contador()
    vacante = "Líder técnico de datos en tiempo real: Kafka o similar, liderazgo de equipos, nube"
    t0 = time.time()
    final = app.invoke({"vacante": vacante, "candidatos": [], "evaluaciones": [], "ranking": []})
    reloj = time.time() - t0

    print(f"Vacante: {vacante}\n")
    for linea in final["ranking"]:
        print("  " + linea)
    evs = final["evaluaciones"]
    solapadas = max(e["inicio"] for e in evs) < min(e["fin"] for e in evs)
    fase = max(e["fin"] for e in evs) - min(e["inicio"] for e in evs)
    print(f"\n{len(evs)} ramas 'evaluar'. ¿Se ejecutaron a la vez? {'sí' if solapadas else 'no'} "
          "(todas empezaron antes de que terminara la primera)")
    print(f"Fase de evaluación: {fase:.1f} s de reloj · {c.resumen_costo()}")
    print(f"Reloj total, incluida la búsqueda: {reloj:.1f} s")
