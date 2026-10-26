"""
01 · El sistema del proyecto: un EMPAREJADOR que recibe una vacante entera y devuelve los 10 mejores candidatos.

La versión de hoy (la "antes") busca con el texto completo de la vacante en la híbrida del Módulo 1. Este archivo
trae también el arnés con el que se mide todo el proyecto:
  DEV, HOLDOUT : 15 y 15 vacantes (partición fija). Se itera en DEV; HOLDOUT se mira UNA vez, al final.
  medir()      : nDCG@10, recall@10 y MRR por vacante, contra la relevancia calculada desde los hechos.
  comparar()   : diferencia pareada con intervalo bootstrap (curso de Evals, Módulo 6).
Al correrlo: la línea base en DEV, por estilo de vacante, y las tres peores para empezar a leer.
"""
from __future__ import annotations
import pathlib
import random
import sys
from importlib import import_module
from statistics import mean

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
av = import_module("as_vacantes")
ev = ac.ev

VACANTES = {v["id"]: v for v in av.vacantes()}
REL = dict(zip(VACANTES, av.relevancias(ac.cvs())))
_orden = sorted(VACANTES)
random.Random(10).shuffle(_orden)
DEV, HOLDOUT = sorted(_orden[:15]), sorted(_orden[15:])
H = {cv["id"]: cv["hechos"] for cv in ac.cvs()}


def emparejar_base(texto: str) -> list[int]:
    """El sistema de hoy: la vacante entera como consulta."""
    return bs.ranking(texto, "hibrida", 119)


def medir(emparejar, ids: list[int], hilos: int = 4) -> dict[int, dict]:
    rankings = ev.tz.en_paralelo(lambda i: emparejar(VACANTES[i]["texto"]), [(i,) for i in ids], hilos=hilos)
    return {i: {"ranking": r[:10], "ndcg": bs.ndcg(r, REL[i]), "recall": bs.recall(r, REL[i]), "rr": bs.rr(r, REL[i])}
            for i, r in zip(ids, rankings)}


def resumen(res: dict[int, dict]) -> str:
    return " · ".join(f"{m} {mean(x[m] for x in res.values()):.3f}" for m in ("ndcg", "recall", "rr"))


def comparar(a: dict[int, dict], b: dict[int, dict], metrica: str = "ndcg", n: int = 5000) -> str:
    """b contra a, pareado por vacante: diferencia media, IC 95% bootstrap y cuántas gana/pierde."""
    ids = sorted(a)
    d = [b[i][metrica] - a[i][metrica] for i in ids]
    rnd = random.Random(0)
    medias = sorted(mean(rnd.choice(d) for _ in d) for _ in range(n))
    return (f"{metrica}: {mean(d):+.3f}  IC95 [{medias[int(0.025 * n)]:+.3f}, {medias[int(0.975 * n)]:+.3f}]  "
            f"gana {sum(x > 0 for x in d)} · pierde {sum(x < 0 for x in d)} · empata {sum(x == 0 for x in d)}")


if __name__ == "__main__":
    print(f"{len(VACANTES)} vacantes · DEV {len(DEV)} · HOLDOUT {len(HOLDOUT)} (no lo mires hasta el final)")
    print(f"Candidatos que cumplen todo (relevancia 2) por vacante: "
          f"{mean(sum(r == 2 for r in REL[i].values()) for i in VACANTES):.1f} de media")
    base = medir(emparejar_base, DEV)
    print(f"\nLínea base en DEV · {resumen(base)}")
    print("\nPor estilo de vacante (DEV):")
    estilos = sorted({VACANTES[i]["hechos"]["estilo"] for i in DEV})
    for e in estilos:
        ids = [i for i in DEV if VACANTES[i]["hechos"]["estilo"] == e]
        print(f"  {e[:58]:58} n={len(ids)}  nDCG {mean(base[i]['ndcg'] for i in ids):.3f}")
    print("\nLas tres peores (para leer): vacante -> rol de los 5 primeros que devuelve")
    for i in sorted(DEV, key=lambda i: base[i]["ndcg"])[:3]:
        v = VACANTES[i]["hechos"]
        print(f"  #{i} {v['rol']} · requiere {', '.join(v['requeridas'])} · {v['anios_min']}+ años · "
              f"{v['ciudad'] or 'remoto'}  (nDCG {base[i]['ndcg']:.2f})")
        print("     -> " + " | ".join(f"{H[c]['rol']} (rel {REL[i].get(c, 0)})" for c in base[i]["ranking"][:5]))
