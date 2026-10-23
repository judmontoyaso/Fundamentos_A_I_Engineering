"""
asistente.py — el sistema del Módulo 9 servido como una página de la app.

Usa el mismo código que el laboratorio (modulo-09-proyecto-integrador/code/00_sistema.py):
guardrails de entrada, memoria por reclutador, búsqueda híbrida, evaluación en paralelo,
guardrail de salida y trazas. La primera consulta construye el índice (unos segundos y
una llamada al modelo por CV); las siguientes lo reutilizan.
"""
from __future__ import annotations
import sys
import threading
import time
from importlib import import_module

from .content import COURSE_ROOT

_M9 = COURSE_ROOT / "modulo-09-proyecto-integrador" / "code"
_lock = threading.Lock()
_S = None          # el módulo 00_sistema, cargado una vez


def _modulo():
    global _S
    if _S is None:
        if str(_M9) not in sys.path:
            sys.path.append(str(_M9))
        _S = import_module("00_sistema")
    return _S


def listo() -> bool:
    return _S is not None and _S.sistema.cache_info().currsize > 0


def sistema():
    with _lock:                          # dos primeras consultas a la vez no deben ingestar dos veces
        return _modulo().sistema()


def estado() -> dict:
    if not listo():
        return {"listo": False, "cvs": [], "modelo": None}
    s = sistema()
    return {"listo": True, "modelo": _S.c.MODELO,
            "cvs": [{"nombre": v["nombre"], "nivel": v["nivel"], "areas": v["areas"], "revisar": v["revisar"]}
                    for v in s.cvs.values()]}


def _uso(trace_id: str) -> dict:
    llm = [x["atributos"] for x in _S.tz.spans(trace_id)
           if x["atributos"].get("tipo") == "llm" and "tokens_entrada" in x["atributos"]]
    return {"llamadas": len(llm),
            "tokens_entrada": sum(a["tokens_entrada"] for a in llm),
            "tokens_salida": sum(a["tokens_salida"] for a in llm),
            "tokens_razonamiento": sum(a["tokens_razonamiento"] for a in llm)}


def consultar(usuario: str, pedido: str) -> dict:
    s = sistema()
    t = time.time()
    r = s.consultar(usuario, pedido)
    return {
        "respuesta": r["respuesta"],
        "bloqueado": r["bloqueado"],
        "estado_salida": r.get("estado_salida", ""),
        "recuerdos": r.get("recuerdos", []),
        "candidatos": [{"nombre": x["cv"]["nombre"], "nivel": x["cv"]["nivel"], "evidencia": x["evidencia"]}
                       for x in r.get("candidatos", [])],
        "evaluaciones": sorted(({"nombre": e["nombre"], "puntaje": e["puntaje"], "motivo": e["motivo"],
                                 "revisar": e["revisar"]} for e in r.get("evaluaciones", [])),
                               key=lambda e: -e["puntaje"]),
        "trace_id": r["trace_id"],
        "arbol": _S.tz.arbol(r["trace_id"]),
        "uso": _uso(r["trace_id"]),
        "segundos": round(time.time() - t, 1),
    }


def memoria(usuario: str) -> list[dict]:
    if not listo():
        return []
    return [{"id": i, "texto": texto} for i, texto in sistema().memoria.listar(usuario)]


def olvidar(usuario: str, recuerdo_id: str) -> None:
    s = sistema()
    with s._lock_memoria:
        s.memoria.olvidar(usuario, recuerdo_id)
