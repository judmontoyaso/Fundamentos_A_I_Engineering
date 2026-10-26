"""
02 · Fase 3 del proyecto: tu eval. Escribe TUS reglas y TUS etiquetas aquí, y córrelo.

1. Escribe las reglas de las etiquetas en REGLAS, antes de etiquetar (¿qué pasa con un rango de años? ¿y si la
   oferta no dice el nivel?).
2. Rellena ETIQUETAS para las 10 ofertas (o para las que quieras; las demás se saltan).
3. Corre: compara cada campo con REPETICIONES corridas y lista los fallos por campo y por oferta.
Mientras ETIQUETAS esté vacío, solo imprime una plantilla para copiar.
"""
from __future__ import annotations
import json
import pathlib
import sys
from collections import Counter
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
sis = import_module("m12_vacantes")
ev = sis.ev

REPETICIONES = 2
REGLAS = """
(escribe aquí tus reglas, antes de etiquetar)
"""
# oferta (1-10) -> {"nivel": ..., "anios_minimos": ..., "skills_requeridas": [...], "skills_deseables": [...],
#                   "modalidad": ..., "ciudad": ..., "salario_mensual_cop": ...}
ETIQUETAS: dict[int, dict] = {}


def comparar(v, e: dict) -> dict[str, bool]:
    r = {}
    for campo, esperado in e.items():
        obtenido = getattr(v, campo)
        if isinstance(esperado, list):                      # cada skill esperada dentro de alguna extraída
            r[campo] = all(any(ev.norm(x) in ev.norm(o) for o in obtenido) for x in esperado)
        elif isinstance(esperado, str):
            r[campo] = obtenido is not None and ev.norm(obtenido) == ev.norm(esperado)
        else:
            r[campo] = obtenido == esperado
    return r


if __name__ == "__main__":
    if not ETIQUETAS:
        plantilla = {i: {"nivel": "", "anios_minimos": None, "skills_requeridas": [], "skills_deseables": [],
                         "modalidad": "", "ciudad": None, "salario_mensual_cop": None} for i in range(1, 11)}
        print("ETIQUETAS está vacío. Copia esta plantilla en ETIQUETAS y rellénala con tus reglas:\n")
        print(json.dumps(plantilla, ensure_ascii=False, indent=1))
    else:
        ev.CACHE["activa"] = False
        ids = sorted(ETIQUETAS)
        fallos = Counter()
        with ev.tz.nueva_traza("proyecto final: tu eval"):
            for _ in range(REPETICIONES):
                res = ev.tz.en_paralelo(lambda i: (i, sis.extraer_vacante(sis.OFERTAS[i - 1])), [(i,) for i in ids])
                for i, v in res:
                    for campo, ok in comparar(v, ETIQUETAS[i]).items():
                        fallos[(i, campo)] += not ok
        print(f"{len(ids)} ofertas × {REPETICIONES} corridas")
        print("Fallos por campo:", dict(Counter(c for (_, c), n in fallos.items() for _ in range(n))))
        for (i, campo), n in sorted(fallos.items()):
            if n:
                print(f"  oferta {i:>2} · {campo:20} falla {n}/{REPETICIONES}")
