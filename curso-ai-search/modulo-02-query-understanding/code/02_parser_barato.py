"""
02 · El precio de entender: el parser es una llamada al LLM en CADA búsqueda (manual §6).

Se repite la estrategia "suaves" con el parser en tres modelos, SIN caché (para medir la latencia real y la
variación): nDCG@10 total y por tipo, y latencia del parser (p50 y p95). La búsqueda sin parser tarda ~15 ms.
"""
from __future__ import annotations
import pathlib
import sys
import time
from importlib import import_module
from statistics import mean

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
ef = import_module("01_entender_y_filtrar")
ac, bs, q, en, ev = ef.ac, ef.bs, ef.q, ef.en, ef.ev

MODELOS = [None, "gpt-4.1-mini", ev.MODELO_BARATO]


def percentil(v: list[float], p: float) -> float:
    v = sorted(v)
    return v[max(0, int(round(p / 100 * len(v) + 0.5)) - 1)]


if __name__ == "__main__":
    ev.CACHE["activa"] = False
    rels = q.relevancias(ac.cvs())
    tipos = list(dict.fromkeys(t for t, _, _ in q.CONSULTAS))
    tabla = {}
    with ev.tz.nueva_traza("parser barato"):
        for modelo in MODELOS:
            def uno(texto):
                t = time.time()
                p = en.parsear(texto, modelo)
                return p, time.time() - t
            pares = ev.tz.en_paralelo(uno, [(t,) for _, t, _ in q.CONSULTAS])
            nd = [bs.ndcg(en.buscar(texto, "suaves", p), rel) for ((_, texto, _), rel), (p, _) in zip(zip(q.CONSULTAS, rels), pares)]
            tabla[modelo or ev.tz.MODELO] = (nd, [s for _, s in pares])
    print(f"{'parser':14} {'nDCG@10':>8} {'p50 s':>7} {'p95 s':>7}")
    for m, (nd, seg) in tabla.items():
        print(f"{m:14} {mean(nd):>8.2f} {percentil(seg, 50):>7.1f} {percentil(seg, 95):>7.1f}")
    print("\nPor tipo:")
    print(f"{'tipo':14}" + "".join(f"{m:>15}" for m in tabla))
    for t in tipos:
        idx = [i for i, (tt, _, _) in enumerate(q.CONSULTAS) if tt == t]
        print(f"{t:14}" + "".join(f"{mean(tabla[m][0][i] for i in idx):>15.2f}" for m in tabla))
