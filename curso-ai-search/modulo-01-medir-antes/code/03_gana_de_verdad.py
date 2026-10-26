"""
03 · ¿La híbrida le gana de verdad a BM25? Comparación pareada por consulta (manual §6). Sin LLM.

Las dos se miden sobre las MISMAS 41 consultas, así que se compara consulta a consulta:
  - victorias, derrotas y empates;
  - un intervalo bootstrap del 95 % para la diferencia media de nDCG (remuestreando consultas);
  - lo mismo por tipo, para ver si un promedio parecido esconde tipos que van en direcciones opuestas.
"""
from __future__ import annotations
import pathlib
import random
import sys
from importlib import import_module
from statistics import mean

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")

B = 5000


def comparar(a: list[float], b: list[float], rnd: random.Random) -> tuple[float, float, float]:
    d = [y - x for x, y in zip(a, b)]
    boot = sorted(mean(rnd.choice(d) for _ in d) for _ in range(B))
    return mean(d), boot[int(0.025 * B)], boot[int(0.975 * B) - 1]


if __name__ == "__main__":
    filas = ac.leer_jsonl("linea_base.jsonl")
    por = {m: [f for f in filas if f["modo"] == m] for m in ("bm25", "densa", "hibrida")}
    rnd = random.Random(1)
    for a, b in (("bm25", "hibrida"), ("bm25", "densa"), ("densa", "hibrida")):
        xa, xb = [f["ndcg"] for f in por[a]], [f["ndcg"] for f in por[b]]
        gana = sum(y > x + 1e-9 for x, y in zip(xa, xb))
        pierde = sum(y < x - 1e-9 for x, y in zip(xa, xb))
        m, lo, hi = comparar(xa, xb, rnd)
        veredicto = "mejor" if lo > 0 else "peor" if hi < 0 else "no se distingue"
        print(f"{b} contra {a}: gana {gana}, pierde {pierde}, empata {len(xa) - gana - pierde} · diferencia media "
              f"{m:+.3f}  IC95 [{lo:+.3f}, {hi:+.3f}] -> {veredicto}")
    print("\nHíbrida contra BM25, por tipo (diferencia media de nDCG@10):")
    tipos = list(dict.fromkeys(f["tipo"] for f in por["bm25"]))
    for t in tipos:
        xa = [f["ndcg"] for f in por["bm25"] if f["tipo"] == t]
        xb = [f["ndcg"] for f in por["hibrida"] if f["tipo"] == t]
        print(f"  {t:14} {mean(y - x for x, y in zip(xa, xb)):+.2f}  (n={len(xa)})")
