"""
02 · Medir cada versión en DESARROLLO (donde se miraron los fallos) y en un HOLDOUT que nadie miró (manual §4-§5).

  desarrollo : los 30 CVs escritos a mano (Módulo 1). Todas las versiones nacieron de leer sus fallos.
  holdout    : los CVs sintéticos del Módulo 3 (salida/sinteticos_validos.jsonl), con otra mezcla de formatos
               e idiomas. Ninguna versión se escribió mirándolos.
Una mejora que aparece en desarrollo y no en el holdout es una mejora para esos 30 casos, no para el sistema.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ve = import_module("01_versiones_del_extractor")
ev = ve.ev
datos = import_module("ev_datos")

MODELO = ev.MODELO_BARATO
VERSIONES = ["v1", "v2", "v3", "v4", "v5"]

if __name__ == "__main__":
    ev.CACHE["activa"] = False
    desarrollo = datos.CVS
    holdout = [{"id": f["id"], "texto": f["texto"], "esperado": f["esperado"], "tupla": f["tupla"]}
               for f in ev.leer_jsonl("sinteticos_validos.jsonl")]
    resultados = {}
    with ev.tz.nueva_traza("desarrollo y holdout", modelo=MODELO):
        for v in VERSIONES:
            resultados[v] = (ve.evaluar(desarrollo, v, MODELO), ve.evaluar(holdout, v, MODELO))
    print(f"Modelo {MODELO} · un caso cuenta como bien si sale perfecto en las 2 repeticiones\n")
    print(f"{'versión':8} {'desarrollo (30)':>16} {'holdout (' + str(len(holdout)) + ')':>14}   fallan en desarrollo")
    for v, (d, h) in resultados.items():
        print(f"{v:8} {sum(d.values()):>13}/30 {sum(h.values()):>11}/{len(holdout)}   {[i for i, ok in d.items() if not ok]}")
    print("\nHoldout por tipo de años (casos perfectos):")
    tipos = sorted({c["tupla"]["años"] for c in holdout})
    print(f"{'versión':8} " + " ".join(f"{t[:14]:>15}" for t in tipos))
    for v, (_, h) in resultados.items():
        celdas = []
        for t in tipos:
            ids = [c["id"] for c in holdout if c["tupla"]["años"] == t]
            celdas.append(f"{sum(h[i] for i in ids)}/{len(ids)}")
        print(f"{v:8} " + " ".join(f"{x:>15}" for x in celdas))
