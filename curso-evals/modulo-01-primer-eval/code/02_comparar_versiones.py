"""
02 · ¿Mejoró de verdad? Comparar v1 y v2 caso por caso, con repeticiones (manual §6-§7).

La exactitud global de dos versiones puede ser igual y esconder casos arreglados y casos rotos.
Por eso se clasifica CADA caso: siempre bien, arreglado, roto, inestable o siempre mal.
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
pe = import_module("01_primer_eval")
ev = pe.ev

MODELO = ev.MODELO_BARATO       # el candidato barato; prueba también con el de tu .env
REPETICIONES = 2                # el mismo caso puede salir distinto: hay que verlo más de una vez


def pasadas(version: str) -> dict[int, list[bool]]:
    """id -> [caso perfecto en la pasada 1, en la 2, ...]"""
    res: dict[int, list[bool]] = {}
    for _ in range(REPETICIONES):
        for f in pe.correr(version, MODELO):
            res.setdefault(f["id"], []).append(all(f["ok"].values()))
    return res


def clasificar(antes: list[bool], despues: list[bool]) -> str:
    if all(antes) and all(despues):
        return "siempre bien"
    if not any(antes) and all(despues):
        return "arreglado"
    if all(antes) and not any(despues):
        return "roto"
    if not any(antes) and not any(despues):
        return "siempre mal"
    return "inestable"


if __name__ == "__main__":
    v1, v2 = pasadas("v1"), pasadas("v2")
    tipos = {cv["id"]: cv["tipo"] for cv in pe.datos.CVS}
    clases = {i: clasificar(v1[i], v2[i]) for i in v1}
    n = len(v1)
    print(f"Modelo {MODELO} · {n} casos · {REPETICIONES} pasadas por versión")
    print(f"  casos perfectos por pasada  v1: {[sum(p[k] for p in v1.values()) for k in range(REPETICIONES)]}"
          f"  v2: {[sum(p[k] for p in v2.values()) for k in range(REPETICIONES)]}")
    print(f"  clasificación: {dict(Counter(clases.values()))}")
    for i, cl in clases.items():
        if cl != "siempre bien":
            print(f"    #{i:<3} {tipos[i]:18} {cl:12} v1 {v1[i]}  v2 {v2[i]}")
    rotos = [i for i, cl in clases.items() if cl == "roto"]
    print("\nDecisión:", "v2 rompe casos que v1 resolvía: revísalos antes de cambiar." if rotos else
          "v2 no rompe nada que v1 resolviera." + (" Los inestables necesitan más pasadas."
                                                    if "inestable" in clases.values() else ""))
