"""
03 · Sobreajustar a propósito: un prompt con pistas de los casos de desarrollo (manual §6).

"v-trampa" es v2 más reglas escritas para los casos concretos que fallaban en desarrollo: es lo que pasa,
sin querer, cuando se itera muchas veces sobre el mismo set mirando sus fallos. Se mide en desarrollo y en
el holdout. Si sube en desarrollo y no en el holdout, la mejora es de esos casos, no del sistema.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
dh = import_module("02_desarrollo_y_holdout")
ve, ev, datos = dh.ve, dh.ev, dh.datos

ev.PROMPTS_EXTRACTOR["v-trampa"] = ev.PROMPTS_EXTRACTOR["v2"] + (
    "\nCasos a tener en cuenta: un consultor freelance de 2015 a 2020 que fue líder técnico de 2018 a 2022 tiene 7 "
    "años; quien trabaja desde 2019 hasta la fecha cuenta hasta hoy; si el CV dice 'SAS, R', las skills son 'sas' y "
    "'r'; un mesero de 2012 a 2015 que luego fue desarrollador de 2015 a 2023 tiene 11 años; una ingeniera graduada en "
    "2010 que trabaja de 2016 a 2024 tiene 8 años.")

if __name__ == "__main__":
    ev.CACHE["activa"] = False
    holdout = [{"id": f["id"], "texto": f["texto"], "esperado": f["esperado"]} for f in ev.leer_jsonl("sinteticos_validos.jsonl")]
    with ev.tz.nueva_traza("sobreajustar a propósito", modelo=dh.MODELO):
        filas = {v: (ve.evaluar(datos.CVS, v, dh.MODELO), ve.evaluar(holdout, v, dh.MODELO)) for v in ("v2", "v-trampa")}
    print(f"{'versión':9} {'desarrollo':>11} {'holdout':>9}")
    for v, (d, h) in filas.items():
        print(f"{v:9} {sum(d.values()):>8}/30 {sum(h.values()):>6}/{len(holdout)}")
    print("\nSi 'v-trampa' sube en desarrollo y no en el holdout, has visto el sobreajuste a un set de evaluación.")
    print("Con iteraciones honestas pasa lo mismo, solo que más despacio: por eso el holdout no se mira al iterar.")
