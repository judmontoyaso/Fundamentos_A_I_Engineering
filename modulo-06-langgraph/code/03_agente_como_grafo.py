"""
03 · El agente del Módulo 5 como grafo con un ciclo (manual §5).

decidir -> (¿terminar?) -> END, o actuar -> decidir. Mismas herramientas, misma
Decision y mismas instrucciones que en el Módulo 5: solo cambia la orquestación.
El tope de pasos es el recursion_limit, y se captura GraphRecursionError.
"""
from __future__ import annotations
import operator
import sys
import pathlib
import time
from importlib import import_module
from typing import Annotated, Any, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")
ag = import_module("05_agente_desde_cero")       # Decision, SYSTEM, ejecutar(), MAX_PASOS


class Estado(TypedDict):
    mensajes: Annotated[list[dict], operator.add]   # historial: se acumula
    decision: Any                                    # la última Decision (objeto Pydantic)
    respuesta: str | None


def decidir(s: Estado) -> dict:
    return {"decision": c.llm(ag.Decision, ag.SYSTEM, s["mensajes"])}


def actuar(s: Estado) -> dict:
    d = s["decision"]
    obs = ag.ejecutar(d)
    return {"mensajes": [{"role": "assistant", "content": d.model_dump_json(exclude_none=True)},
                         {"role": "user", "content": f"Observación de {d.herramienta}:\n{obs}"}]}


def responder(s: Estado) -> dict:
    return {"respuesta": s["decision"].respuesta or "(sin respuesta)"}


g = StateGraph(Estado)
g.add_node("decidir", decidir)
g.add_node("actuar", actuar)
g.add_node("responder", responder)
g.add_edge(START, "decidir")
g.add_conditional_edges("decidir", lambda s: "responder" if s["decision"].herramienta == "terminar" else "actuar",
                        ["actuar", "responder"])
g.add_edge("actuar", "decidir")
g.add_edge("responder", END)
app = g.compile()

# Cada vuelta del ciclo son 2 nodos (decidir + actuar): el límite equivale a MAX_PASOS pasos del Módulo 5.
LIMITE = 2 * ag.MAX_PASOS + 1


def ejecutar_agente(pedido: str, limite: int = LIMITE) -> str:
    entrada = {"mensajes": [{"role": "user", "content": f"Pedido: {pedido}"}], "decision": None, "respuesta": None}
    try:
        respuesta = None
        for paso in app.stream(entrada, {"recursion_limit": limite}, stream_mode="updates"):
            for nodo, cambios in paso.items():
                if nodo == "decidir":
                    d = cambios["decision"]
                    args = {k: v for k, v in d.model_dump().items()
                            if v is not None and k not in ("razonamiento", "herramienta", "respuesta")}
                    print(f"  decidir -> {d.herramienta} {args}")
                elif nodo == "actuar":
                    print("  actuar  -> " + cambios["mensajes"][1]["content"].splitlines()[1][:90])
                elif nodo == "responder":
                    respuesta = cambios["respuesta"]
        return respuesta or "(sin respuesta)"
    except GraphRecursionError:
        return f"Se alcanzó el recursion_limit ({limite}) sin respuesta: el agente no terminó a tiempo."


if __name__ == "__main__":
    c.reiniciar_contador()
    t = time.time()
    pedido = "Necesito a alguien senior para liderar un equipo de datos en tiempo real. ¿A quién entrevisto y por qué?"
    print(f"Pedido: {pedido}\n")
    print("\n== Respuesta ==\n" + ejecutar_agente(pedido))
    print(f"\n{c.resumen_costo('Costo: ')} · {time.time() - t:.1f} s de reloj")

    print("\n== Con recursion_limit=3 (no le alcanza ni para buscar y leer un CV) ==")
    print(ejecutar_agente(pedido, limite=3))
    print("\n" + app.get_graph().draw_mermaid())
