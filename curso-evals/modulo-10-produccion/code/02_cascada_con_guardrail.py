"""
02 · El chequeo sin referencia como guardrail: modelo barato, y el grande solo cuando salta una alerta (manual §6).

Tres políticas sobre el mismo tráfico (los 75 CVs de los tres días de 01):
  barato      : siempre el modelo barato.
  cascada     : el barato; si un chequeo sin referencia alerta, se repite con el modelo del .env.
  siempre caro: siempre el modelo del .env.
Para cada una: errores reales, llamadas al modelo grande y llamadas totales.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
mon = import_module("01_monitoreo_sin_referencia")
ev = mon.ev


def cascada(cv: dict) -> dict:
    f = ev.extraer(cv["texto"], mon.VERSION, mon.MODELO)
    caro = False
    if mon.alertas(cv["texto"], f):
        f, caro = ev.extraer(cv["texto"], mon.VERSION, None), True
    return {"error": not all(ev.comparar_ficha(f, cv["esperado"]).values()), "caro": caro}


def una_politica(cv: dict, modelo: str | None) -> dict:
    f = ev.extraer(cv["texto"], mon.VERSION, modelo)
    return {"error": not all(ev.comparar_ficha(f, cv["esperado"]).values()), "caro": modelo is None}


if __name__ == "__main__":
    ev.CACHE["activa"] = False
    cvs = [cv for d in mon.trafico().values() for cv in d]
    with ev.tz.nueva_traza("cascada"):
        politicas = {
            f"barato ({mon.MODELO})": ev.tz.en_paralelo(lambda cv: una_politica(cv, mon.MODELO), [(cv,) for cv in cvs]),
            "cascada": ev.tz.en_paralelo(cascada, [(cv,) for cv in cvs]),
            f"siempre caro ({ev.tz.MODELO})": ev.tz.en_paralelo(lambda cv: una_politica(cv, None), [(cv,) for cv in cvs]),
        }
    print(f"{len(cvs)} CVs (los tres días de 01)\n")
    print(f"{'política':30} {'errores reales':>15} {'llamadas al grande':>19} {'llamadas totales':>17}")
    for nombre, rs in politicas.items():
        caros = sum(r["caro"] for r in rs)
        total = len(rs) + (caros if nombre == "cascada" else 0)
        print(f"{nombre:30} {sum(r['error'] for r in rs):>12}/{len(rs)} {caros:>16}/{len(rs)} {total:>17}")
    print("\nLa cascada paga el modelo grande solo en los casos sospechosos. Solo arregla los errores que el chequeo")
    print("ve: los plausibles (12 años en vez de 13) pasan igual que con el modelo barato.")
