"""
02 · Tu emparejador. Escribe emparejar(texto) -> lista de ids de CV (el mejor primero) y córrelo.

Compara contra la línea base EN DEV, pareado por vacante, con intervalo bootstrap. Itera aquí todo lo que quieras.
Cuando hayas decidido tu versión final (y no antes), corre con HOLDOUT=1: es la única medición que vale para el
informe, y se hace una vez. Si después de mirar el holdout cambias algo, ya no sirve para medir ese cambio.

Piezas que puedes usar (todas del curso):
  en.parsear / en.requisitos / en.buscar ·  fx.fichas() ·  bs.ranking ·  el reranker del Módulo 4 ·
  el contexto del Módulo 5 ·  la base SQL del Módulo 6 ·  pm.visibles() del Módulo 8 ·  ev.llm_cache
"""
from __future__ import annotations
import os
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
em = import_module("01_el_emparejador")
ac, bs, ev = em.ac, em.bs, em.ev
en = import_module("as_entender")
fx = import_module("as_fichas")


def emparejar(texto: str) -> list[int]:
    # TODO: tu sistema. Mientras tanto, es la línea base.
    return em.emparejar_base(texto)


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    ids = em.HOLDOUT if os.getenv("HOLDOUT") == "1" else em.DEV
    nombre = "HOLDOUT" if ids is em.HOLDOUT else "DEV"
    base, tuyo = em.medir(em.emparejar_base, ids), em.medir(emparejar, ids)
    print(f"{nombre} · línea base · {em.resumen(base)}")
    print(f"{nombre} · el tuyo    · {em.resumen(tuyo)}")
    print(f"  {em.comparar(base, tuyo)}")
    print(f"  {em.comparar(base, tuyo, 'rr')}")
    print("\nVacantes donde el tuyo pierde contra la base:")
    for i in ids:
        if tuyo[i]["ndcg"] < base[i]["ndcg"]:
            print(f"  #{i} {tuyo[i]['ndcg']:.2f} contra {base[i]['ndcg']:.2f} · {em.VACANTES[i]['hechos']['rol']}")
