"""
01 · Fase 1 del proyecto: conocer el sistema SIN leer su código. Corre las 10 ofertas y muestra cada salida.

El sistema es m12_vacantes.extraer_vacante(): texto de una oferta de empleo -> Vacante (cargo, nivel, años
mínimos, skills requeridas y deseables, modalidad, ciudad, salario). Lee las salidas como en el Módulo 2: una
nota por problema, con tus palabras, antes de pensar en métricas.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
sis = import_module("m12_vacantes")
ev = sis.ev

if __name__ == "__main__":
    ev.CACHE["activa"] = False
    with ev.tz.nueva_traza("proyecto final: conocer el sistema"):
        res = ev.tz.en_paralelo(lambda t: sis.extraer_vacante(t), [(t,) for t in sis.OFERTAS])
    for i, (t, v) in enumerate(zip(sis.OFERTAS, res), 1):
        print(f"#{i} {t}\n   -> {v.model_dump()}\n")
    print("Tu turno: escribe tus notas (codificación abierta) antes de seguir con la fase 2.")
