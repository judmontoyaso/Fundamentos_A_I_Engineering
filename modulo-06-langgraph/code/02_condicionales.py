"""
02 · Aristas condicionales: enrutamiento y puertas como grafo (manual §4).

A) Enrutador sin LLM (la regla que empató con el LLM en el Módulo 5): cada
   consulta va al modo de búsqueda que le corresponde.
B) La cadena con puerta del Módulo 5 como grafo: extraer -> puerta -> resumir o
   revisión humana. Reutiliza DatosCV, Perfil y puerta() del Módulo 5.
"""
from __future__ import annotations
import sys
import pathlib
from importlib import import_module
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")
cad = import_module("01_encadenamiento")          # DatosCV, Perfil, puerta() del Módulo 5


# ---------- A) Enrutamiento ----------
class Busqueda(TypedDict):
    consulta: str
    modo: str
    nombres: list[str]


def clasificar(s: Busqueda) -> dict:
    return {"modo": "bm25" if len(s["consulta"].split()) <= 2 else "hibrida"}


def buscador(modo: str):
    def nodo(s: Busqueda) -> dict:
        return {"nombres": [h.payload["nombre"] for h in c.buscar(s["consulta"], modo=modo, k=3)]}
    return nodo


ra = StateGraph(Busqueda)
ra.add_node("clasificar", clasificar)
ra.add_node("buscar_bm25", buscador("bm25"))
ra.add_node("buscar_hibrida", buscador("hibrida"))
ra.add_edge(START, "clasificar")
ra.add_conditional_edges("clasificar", lambda s: s["modo"],
                         {"bm25": "buscar_bm25", "hibrida": "buscar_hibrida"})
ra.add_edge("buscar_bm25", END)
ra.add_edge("buscar_hibrida", END)
enrutador = ra.compile()


# ---------- B) Encadenamiento con puerta ----------
class Cadena(TypedDict):
    texto: str
    datos: dict | None
    problemas: list[str]
    perfil: str | None


def extraer(s: Cadena) -> dict:
    d = c.llm(cad.DatosCV, f"Extrae los datos del CV. {c.INSTRUCCION_CV} No inventes.", c.como_cv(s["texto"]))
    return {"datos": d.model_dump(), "problemas": cad.puerta(d, s["texto"])}


def resumir(s: Cadena) -> dict:
    p = c.llm(cad.Perfil, "Redacta un perfil profesional breve y factual, solo con estos datos.", str(s["datos"]))
    return {"perfil": p.resumen}


def revision_humana(s: Cadena) -> dict:
    return {"perfil": f"PENDIENTE DE REVISIÓN: {', '.join(s['problemas'])}"}


rb = StateGraph(Cadena)
rb.add_node("extraer", extraer)
rb.add_node("resumir", resumir)
rb.add_node("revision_humana", revision_humana)
rb.add_edge(START, "extraer")
rb.add_conditional_edges("extraer", lambda s: "revision_humana" if s["problemas"] else "resumir",
                         ["resumir", "revision_humana"])
rb.add_edge("resumir", END)
rb.add_edge("revision_humana", END)
cadena = rb.compile()


if __name__ == "__main__":
    c.reiniciar_contador()
    print("== A) Enrutador: qué camino toma cada consulta ==")
    for q in ("ISO 27001", "experiencia con streaming", "C#"):
        ruta, nombres = [], []
        # Una sola ejecución: stream da la ruta y los cambios de cada nodo a la vez.
        for paso in enrutador.stream({"consulta": q, "modo": "", "nombres": []}, stream_mode="updates"):
            for nodo, cambios in paso.items():
                ruta.append(nodo)
                nombres = cambios.get("nombres", nombres)
        print(f"  {q:28} ruta={' -> '.join(ruta):28} {nombres}")

    print("\n== B) Cadena con puerta ==")
    cvs = {
        "CV completo": "Laura Gómez · laura.gomez@mail.com · 9 años de experiencia en ingeniería de datos. "
                       "Kafka, Flink, Python y AWS.",
        "CV sin contacto": "Juan Ríos. Desarrollador con 2 años de experiencia en Node.js y Docker.",
    }
    for etiqueta, texto in cvs.items():
        ruta = []
        for paso in cadena.stream({"texto": texto, "datos": None, "problemas": [], "perfil": None},
                                   stream_mode="updates"):
            for nodo, cambios in paso.items():
                ruta.append(nodo)
                if "perfil" in cambios:
                    resultado = cambios["perfil"]
        print(f"  {etiqueta:16} ruta={' -> '.join(ruta)}\n  {'':16} {resultado}")

    print("\n" + c.resumen_costo("Costo: "))
    print("\nDiagrama de la cadena:\n" + cadena.get_graph().draw_mermaid())
