"""
02 · Un usuario simulado: un LLM con un objetivo y un requisito oculto conversa con el asistente (manual §6-§7).

El guion fijo solo prueba lo que escribiste. Un usuario simulado reacciona a lo que responde el asistente,
así que explora conversaciones que no previste. Dos cosas se comprueban con código:
  - el asistente: ¿al final recomienda a alguien aceptable para el objetivo?
  - el SIMULADOR: ¿se comportó como su persona (reveló su requisito, no inventó otro objetivo)? Si no,
    la conversación no probó lo que querías, igual que un CV sintético que no tiene lo que pediste (Módulo 3).
"""
from __future__ import annotations
import pathlib
import re
import sys
import uuid
from importlib import import_module

from pydantic import BaseModel, Field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
cg = import_module("01_conversaciones_con_guion")
ev, S = cg.ev, cg.S

MAX_TURNOS = 4
CORRIDAS = 2

# (nombre, objetivo, requisito oculto, patrón que debe aparecer en sus mensajes, candidatos aceptables)
PERSONAS = [
    ("seguridad en banca", "cubrir una vacante de seguridad de la información en un banco",
     "solo si el asistente propone a alguien, añade que la persona necesita una certificación de auditoría",
     r"certifica", ["andres"]),
    ("datos con inglés", "contratar a alguien senior que lidere un equipo de datos en tiempo real",
     "en tu segundo mensaje dices que el equipo trabaja en inglés y que exiges inglés fluido o nativo",
     r"ingles", ["lucia"]),
    ("pedido vago", "encontrar a alguien de infraestructura cloud",
     "empiezas pidiendo 'alguien bueno' sin decir para qué; das el área solo si te lo preguntan o te proponen algo que no encaja",
     r"cloud|nube|infraestructura", ["diego"]),
]


class Mensaje(BaseModel):
    pensamiento: str = Field(description="qué quieres conseguir con este mensaje")
    mensaje: str = Field(description="lo que le escribes al asistente, en una o dos frases")
    terminar: bool = Field(description="True si ya tienes un candidato que te sirve o te das por vencido")


def simulador(persona: tuple, historia: list[tuple[str, str]]) -> Mensaje:
    nombre, objetivo, oculto, _, _ = persona
    system = (f"Eres un reclutador que conversa con un asistente de selección. Tu objetivo: {objetivo}. "
              f"Regla de tu personaje: {oculto}. Escribe como una persona real, breve. No inventes otro objetivo.")
    conversacion = "\n".join(f"{q}: {t}" for q, t in historia) or "(todavía no has escrito nada)"
    return ev.tz.llm_trazado(Mensaje, system, f"Conversación hasta ahora:\n{conversacion}\n\nTu siguiente mensaje:",
                             nombre="usuario simulado")


def conversar(persona: tuple) -> dict:
    s = S.sistema()
    usuario = f"sim-{uuid.uuid4().hex[:6]}"
    historia: list[tuple[str, str]] = []
    ultima_respuesta = ""
    for _ in range(MAX_TURNOS):
        m = simulador(persona, historia)
        if m.terminar and historia:
            break
        historia.append(("Reclutador", m.mensaje))
        r = s.consultar(usuario, m.mensaje)
        ultima_respuesta = r["respuesta"]
        historia.append(("Asistente", " ".join(ultima_respuesta.split())))
    mensajes = " ".join(ev.norm(t) for q, t in historia if q == "Reclutador")
    return {"persona": persona[0], "historia": historia, "turnos": sum(q == "Reclutador" for q, _ in historia),
            "objetivo_ok": any(n in ev.norm(ultima_respuesta) for n in persona[4]),
            "simulador_ok": bool(re.search(persona[3], mensajes))}


if __name__ == "__main__":
    S.sistema()
    with ev.tz.nueva_traza("usuario simulado"):
        res = ev.tz.en_paralelo(conversar, [(p,) for p in PERSONAS for _ in range(CORRIDAS)], hilos=6)
    for p in PERSONAS:
        rs = [r for r in res if r["persona"] == p[0]]
        print(f"== {p[0]}: objetivo conseguido {sum(r['objetivo_ok'] for r in rs)}/{len(rs)} · simulador fiel a su "
              f"persona {sum(r['simulador_ok'] for r in rs)}/{len(rs)} · turnos {[r['turnos'] for r in rs]}")
        for r in rs:
            if not (r["objetivo_ok"] and r["simulador_ok"]):
                for q, t in r["historia"]:
                    print(f"     {q:10} {t[:140]}")
                print()
    validas = [r for r in res if r["simulador_ok"]]
    print(f"Conversaciones donde el simulador hizo su papel: {len(validas)}/{len(res)} · de ellas, objetivo conseguido "
          f"{sum(r['objetivo_ok'] for r in validas)}/{len(validas)}")
    print("Las conversaciones con un simulador infiel no cuentan para evaluar al asistente: no probaron lo que debían.")
