"""
06 · Persistencia real (SQLite) y reanudar tras un fallo sin volver a pagar (manual §7).

evaluar (LLM) -> redactar (LLM) -> enviar (efecto simulado: escribe en una "bandeja").
El estado se guarda en SQLite después de cada paso. Tres escenarios:
  A) enviar falla ANTES del efecto: se "reinicia el proceso" y se reanuda desde enviar,
     sin volver a llamar al modelo.
  B) enviar se corta DESPUÉS del efecto, con clave de idempotencia: al reanudar no duplica.
  C) igual que B pero SIN idempotencia: el mensaje sale dos veces.

    pip install langgraph langgraph-checkpoint-sqlite
"""
from __future__ import annotations
import json
import pathlib
import sqlite3
import sys
from importlib import import_module
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")
par = import_module("03_paralelizacion")         # Encaje
ev = import_module("04_evaluador_optimizador")   # Borrador

SALIDA = pathlib.Path(__file__).resolve().parent / "salida"
DB = SALIDA / "checkpoints.db"
BANDEJA = SALIDA / "bandeja.jsonl"
FALLAS = {"antes": 0, "despues": 0}      # cuántas veces fallará enviar (lo controla cada escenario)
IDEMPOTENTE = {"activo": True}


class Estado(TypedDict):
    candidato: str
    puntaje: int
    borrador: str
    enviado: bool


def evaluar(s: Estado) -> dict:
    texto = next(cv["texto"] for cv in c.corpus() if cv["nombre"] == s["candidato"])
    e = c.llm(par.Encaje, f"Evalúa el CV para: Líder técnico de datos en tiempo real. {c.INSTRUCCION_CV}",
              c.como_cv(texto))
    return {"puntaje": e.puntaje}


def redactar(s: Estado) -> dict:
    b = c.llm(ev.Borrador, "Redactas invitaciones a entrevista de máximo 40 palabras.",
              f"Invita a {s['candidato']} a una entrevista para Líder técnico de datos.")
    return {"borrador": b.mensaje}


def bandeja() -> list[dict]:
    return [json.loads(l) for l in BANDEJA.read_text(encoding="utf-8").splitlines()] if BANDEJA.exists() else []


def enviar(s: Estado, config) -> dict:
    if FALLAS["antes"] > 0:
        FALLAS["antes"] -= 1
        raise ConnectionError("el servidor de correo no responde")
    clave = config["configurable"]["thread_id"]          # clave de idempotencia: un envío por hilo
    if not (IDEMPOTENTE["activo"] and any(m["clave"] == clave for m in bandeja())):
        with BANDEJA.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"clave": clave, "para": s["candidato"], "mensaje": s["borrador"]}) + "\n")
    if FALLAS["despues"] > 0:
        FALLAS["despues"] -= 1
        raise TimeoutError("la conexión se cortó justo después de enviar")
    return {"enviado": True}


def compilar(conexion: sqlite3.Connection):
    g = StateGraph(Estado)
    g.add_node("evaluar", evaluar)
    g.add_node("redactar", redactar)
    g.add_node("enviar", enviar)
    g.add_edge(START, "evaluar")
    g.add_edge("evaluar", "redactar")
    g.add_edge("redactar", "enviar")
    g.add_edge("enviar", END)
    return g.compile(checkpointer=SqliteSaver(conexion))


def escenario(nombre: str, hilo: str, antes: int = 0, despues: int = 0, idempotente: bool = True):
    FALLAS.update(antes=antes, despues=despues)
    IDEMPOTENTE["activo"] = idempotente
    cfg = {"configurable": {"thread_id": hilo}}
    print(f"\n== {nombre} ==")

    c.reiniciar_contador()
    app = compilar(sqlite3.connect(DB, check_same_thread=False))
    try:
        app.invoke({"candidato": "Laura Gómez", "puntaje": 0, "borrador": "", "enviado": False}, cfg)
    except Exception as e:
        print(f"  1ª ejecución: falló en «enviar» -> {type(e).__name__}: {e}")
    print(f"  llamadas al modelo pagadas: {c.contador['llamadas']} · siguiente paso guardado: {app.get_state(cfg).next}")

    # "Reinicio del proceso": conexión nueva y grafo nuevo, el estado sale de SQLite.
    c.reiniciar_contador()
    app = compilar(sqlite3.connect(DB, check_same_thread=False))
    final = app.invoke(None, cfg)                       # None = continuar donde se quedó
    envios = sum(m["clave"] == hilo for m in bandeja())
    print(f"  reanudado tras reinicio: enviado={final['enviado']} · llamadas al modelo al reanudar: "
          f"{c.contador['llamadas']} · veces que salió el mensaje: {envios}"
          + ("  ← DUPLICADO" if envios > 1 else ""))


if __name__ == "__main__":
    SALIDA.mkdir(exist_ok=True)
    DB.unlink(missing_ok=True)
    BANDEJA.unlink(missing_ok=True)
    escenario("A · falla antes del efecto", "vacante-A", antes=1)
    escenario("B · se corta después del efecto, CON idempotencia", "vacante-B", despues=1, idempotente=True)
    escenario("C · se corta después del efecto, SIN idempotencia", "vacante-C", despues=1, idempotente=False)
    print(f"\nEstado y bandeja en {SALIDA}. Un checkpointer evita repetir lo ya pagado; no evita repetir un efecto")
    print("que ocurrió y no llegó a registrarse. Para eso hace falta que la acción sea idempotente.")
