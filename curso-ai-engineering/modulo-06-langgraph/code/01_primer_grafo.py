"""
01 · Tu primer grafo: estado, nodos, aristas y reductores (manual §2-§3).

Sin ninguna llamada al modelo: normalizar la consulta -> buscar (Módulo 4) ->
formatear. Verás invoke, stream (la traza), el diagrama Mermaid y qué pasa
cuando dos nodos en paralelo escriben el mismo campo sin reductor.
"""
from __future__ import annotations
import operator
import sys
import pathlib
from importlib import import_module
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.errors import InvalidUpdateError

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")


class Estado(TypedDict):
    consulta: str
    resultados: list[str]                              # se REEMPLAZA en cada actualización
    bitacora: Annotated[list[str], operator.add]       # se ACUMULA (reductor)


def normalizar(s: Estado) -> dict:
    limpia = " ".join(s["consulta"].split()).strip()
    return {"consulta": limpia, "bitacora": [f"normalizar: {s['consulta']!r} -> {limpia!r}"]}


def buscar(s: Estado) -> dict:
    hits = c.buscar(s["consulta"], modo="hibrida", k=3)
    return {"resultados": [f"{h.payload['nombre']} ({h.payload['nivel']})" for h in hits],
            "bitacora": [f"buscar: {len(hits)} resultados"]}


def formatear(s: Estado) -> dict:
    return {"resultados": [f"{i}. {r}" for i, r in enumerate(s["resultados"], 1)],
            "bitacora": ["formatear: listo"]}


g = StateGraph(Estado)
g.add_node("normalizar", normalizar)
g.add_node("buscar", buscar)
g.add_node("formatear", formatear)
g.add_edge(START, "normalizar")
g.add_edge("normalizar", "buscar")
g.add_edge("buscar", "formatear")
g.add_edge("formatear", END)
app = g.compile()


if __name__ == "__main__":
    print("== invoke: el estado final ==")
    final = app.invoke({"consulta": "   experiencia   con  streaming  ", "resultados": [], "bitacora": []})
    print("  resultados:", final["resultados"])
    print("  bitácora (acumulada por el reductor):")
    for linea in final["bitacora"]:
        print("   -", linea)

    print("\n== stream: lo que devuelve cada nodo, a medida que termina (tu traza) ==")
    for paso in app.stream({"consulta": "ISO 27001", "resultados": [], "bitacora": []}, stream_mode="updates"):
        for nodo, cambios in paso.items():
            print(f"  {nodo:10} -> {list(cambios)}")

    print("\n== El diagrama (pégalo en un visor de Mermaid) ==")
    print(app.get_graph().draw_mermaid())

    print("== Dos nodos en paralelo escriben 'resultados' (sin reductor) ==")
    p = StateGraph(Estado)
    p.add_node("uno", lambda s: {"resultados": ["de uno"]})
    p.add_node("dos", lambda s: {"resultados": ["de dos"]})
    p.add_edge(START, "uno")
    p.add_edge(START, "dos")                 # dos aristas desde START: corren en el mismo paso
    p.add_edge("uno", END)
    p.add_edge("dos", END)
    try:
        p.compile().invoke({"consulta": "", "resultados": [], "bitacora": []})
        print("  sin error (inesperado)")
    except InvalidUpdateError as e:
        print("  InvalidUpdateError:", str(e).splitlines()[0])
        print("  LangGraph no elige en silencio cuál gana: o pones un reductor, o cambias el diseño.")
