"""
04 · Humano en el bucle: interrupt, Command(resume) y checkpointer (manual §7-§9).

elegir (buscar + evaluar) -> redactar (LLM) -> aprobar (PAUSA) -> enviar (simulado) | fin.
El grafo se detiene en 'aprobar' con el borrador; una persona aprueba, edita o
rechaza, y el grafo continúa justo ahí. Ningún envío ocurre sin aprobación.

Lecciones aprendidas al escribirlo:
- La primera versión elegía el primer resultado de la búsqueda y salió una Product
  Manager para una vacante de líder técnico de datos. Por eso 'elegir' evalúa a los
  3 primeros, guarda sus puntajes en el estado y aplica un UMBRAL antes de redactar.
- La evaluación daba 5/5 o 1/5 al mismo CV según la corrida, por un prompt ambiguo
  (manual §10). La traza y el umbral evitaron una invitación equivocada mientras tanto.
- La persona que aprueba debe LEER el borrador: es la última defensa, no un trámite.

En la app puedes partirlo en dos celdas: ejecuta hasta la pausa, y en la celda
libre reanuda tú con  app.invoke(Command(resume={...}), CONFIG).
"""
from __future__ import annotations
import sys
import pathlib
from importlib import import_module
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")
ev = import_module("04_evaluador_optimizador")   # Borrador del Módulo 5
par = import_module("03_paralelizacion")         # Encaje del Módulo 5

ENVIADOS: list[dict] = []          # "bandeja de salida" simulada: el efecto que no debe repetirse
EJECUCIONES_APROBAR = {"n": 0}     # para ver la trampa de interrupt (manual §8)


UMBRAL = 3   # por debajo de 3/5 no se invita a nadie


class Estado(TypedDict):
    vacante: str
    evaluaciones: list[str]        # traza de la elección: quién, con qué puntaje
    candidato: dict | None
    puntaje: int
    borrador: str
    aprobado: bool | None


def elegir(s: Estado) -> dict:
    """Buscar no basta: se evalúa a los 3 primeros contra la vacante y se elige el mejor."""
    mejores, traza = [], []
    for hit in c.buscar(s["vacante"], modo="hibrida", k=3, nivel="senior"):
        e = c.llm(par.Encaje, f"Evalúa el CV contra esta vacante: {s['vacante']}. {c.INSTRUCCION_CV}",
                  c.como_cv(hit.payload["texto"]))
        traza.append(f"{e.puntaje}/5 {hit.payload['nombre']}")
        mejores.append((e.puntaje, {"id": hit.id, "nombre": hit.payload["nombre"], "texto": hit.payload["texto"]}))
    puntaje, candidato = max(mejores, key=lambda x: x[0])
    return {"candidato": candidato, "puntaje": puntaje, "evaluaciones": traza}


def redactar(s: Estado) -> dict:
    cand = s["candidato"]
    b = c.llm(ev.Borrador, "Redactas mensajes de reclutamiento breves (máximo 60 palabras), cercanos y concretos.",
              f"Invita a {cand['nombre']} a una entrevista para: {s['vacante']}.\nSu perfil: {cand['texto']}")
    return {"borrador": b.mensaje}


def aprobar(s: Estado) -> dict:
    EJECUCIONES_APROBAR["n"] += 1                       # corre al pausar Y al reanudar
    respuesta = interrupt({"para": s["candidato"]["nombre"], "borrador": s["borrador"],
                           "opciones": "aprobado: true/false, edicion: texto opcional"})
    return {"aprobado": bool(respuesta.get("aprobado")), "borrador": respuesta.get("edicion") or s["borrador"]}


def enviar(s: Estado) -> dict:
    ENVIADOS.append({"para": s["candidato"]["nombre"], "mensaje": s["borrador"]})
    return {}


g = StateGraph(Estado)
for nombre, fn in [("elegir", elegir), ("redactar", redactar), ("aprobar", aprobar), ("enviar", enviar)]:
    g.add_node(nombre, fn)
g.add_edge(START, "elegir")
# Puerta: sin un candidato que pase el umbral, no se redacta ni se pide aprobación.
g.add_conditional_edges("elegir", lambda s: "redactar" if s["puntaje"] >= UMBRAL else END, ["redactar", END])
g.add_edge("redactar", "aprobar")
g.add_conditional_edges("aprobar", lambda s: "enviar" if s["aprobado"] else END, ["enviar", END])
g.add_edge("enviar", END)
app = g.compile(checkpointer=InMemorySaver())

CONFIG = {"configurable": {"thread_id": "vacante-datos-tiempo-real"}}
VACANTE = "Líder técnico de datos en tiempo real"


def hasta_la_pausa(config: dict) -> dict | None:
    r = app.invoke({"vacante": VACANTE, "evaluaciones": [], "candidato": None, "puntaje": 0,
                    "borrador": "", "aprobado": None}, config)
    print(f"  Evaluación de candidatos: {r['evaluaciones']}")
    if "__interrupt__" not in r:
        print(f"  Ninguno llegó a {UMBRAL}/5: el grafo terminó sin redactar ni pedir aprobación.")
        return None
    return r["__interrupt__"][0].value


if __name__ == "__main__":
    c.reiniciar_contador()

    print("== 1. Hilo A: ejecutar hasta la pausa ==")
    pausa = hasta_la_pausa(CONFIG)
    if pausa is None:
        raise SystemExit
    print(f"  El grafo se detuvo antes de enviar. Siguiente nodo: {app.get_state(CONFIG).next}")
    print(f"  Para: {pausa['para']}\n  Borrador: {pausa['borrador']}")
    print(f"  Enviados hasta ahora: {len(ENVIADOS)}")

    print("\n== 2. Hilo A: la persona LEE el borrador, añade la firma y aprueba ==")
    edicion = pausa["borrador"].rstrip() + "\n\nEquipo de Talento, Acme"
    final = app.invoke(Command(resume={"aprobado": True, "edicion": edicion}), CONFIG)
    print(f"  aprobado={final['aprobado']} · enviados={len(ENVIADOS)}")
    print("  Mensaje enviado:\n    " + ENVIADOS[-1]["mensaje"].replace("\n", "\n    "))

    print("\n== 3. Hilo B: otra ejecución, y esta vez la persona RECHAZA ==")
    config_b = {"configurable": {"thread_id": "vacante-datos-tiempo-real-B"}}
    if hasta_la_pausa(config_b) is not None:
        antes = len(ENVIADOS)
        app.invoke(Command(resume={"aprobado": False}), config_b)
        print(f"  Enviados antes: {antes} · después: {len(ENVIADOS)} -> rechazar no envía nada.")

    print(f"\n== 4. La trampa de interrupt: 'aprobar' se ejecutó {EJECUCIONES_APROBAR['n']} veces en 2 hilos ==")
    print("  Dos por hilo: una al pausar y otra al reanudar. Por eso elegir y redactar (las llamadas al LLM)")
    print("  están en OTROS nodos: si estuvieran antes del interrupt dentro de 'aprobar', se pagarían dos veces.")

    print("\n== 5. Historial del hilo A (del más reciente al más antiguo) ==")
    for snap in app.get_state_history(CONFIG):
        print(f"  paso={snap.metadata.get('step'):>2}  siguiente={str(snap.next):14} "
              f"aprobado={snap.values.get('aprobado')}")

    print("\n" + c.resumen_costo("Costo: "))
