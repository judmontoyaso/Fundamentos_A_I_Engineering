"""
as_buscador.py — el buscador de partida del curso (la línea base) y las métricas para medirlo.

Tres modos sobre el texto completo de los 119 CVs, con las piezas de AI Engineering:
  bm25    : léxico (Módulo 4).
  densa   : embeddings (Módulo 2), similitud coseno.
  hibrida : RRF (k = 60) de los dos rankings.
Métricas por consulta: nDCG@10 (usa la relevancia graduada 2/1), recall@10 (de los relevantes con rel 2) y MRR
(puesto del primer CV con rel 2). Los módulos siguientes cambian piezas y comparan contra esto.
"""
from __future__ import annotations
import math
from functools import lru_cache
from importlib import import_module

import numpy as np

ac = import_module("as_comun")


@lru_cache(maxsize=1)
def indice():
    cvs = ac.cvs()
    ids = [cv["id"] for cv in cvs]
    textos = [cv["texto"] for cv in cvs]
    m = ac.embed(textos)
    return ids, m / np.linalg.norm(m, axis=1, keepdims=True), ac.bm25.BM25(textos)


def ranking(consulta: str, modo: str = "hibrida", profundidad: int = 50) -> list[int]:
    ids, densos, lexico = indice()
    if modo in ("densa", "hibrida"):
        q = ac.embed([consulta])[0]
        rank_d = [ids[i] for i in np.argsort(-(densos @ (q / np.linalg.norm(q))))[:profundidad]]
        if modo == "densa":
            return rank_d
    rank_b = [ids[i] for i, _ in lexico.buscar(consulta, profundidad)]
    if modo == "bm25":
        return rank_b
    puntos: dict[int, float] = {}
    for r in (rank_d, rank_b):
        for puesto, i in enumerate(r, 1):
            puntos[i] = puntos.get(i, 0.0) + 1 / (60 + puesto)
    return sorted(puntos, key=lambda i: -puntos[i])


def ndcg(rank: list[int], rel: dict[int, int], k: int = 10) -> float:
    dcg = sum((2 ** rel.get(d, 0) - 1) / math.log2(p + 2) for p, d in enumerate(rank[:k]))
    ideal = sorted(rel.values(), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(p + 2) for p, r in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def recall(rank: list[int], rel: dict[int, int], k: int = 10) -> float:
    buenos = {d for d, r in rel.items() if r == 2}
    return len(buenos & set(rank[:k])) / len(buenos) if buenos else 0.0


def rr(rank: list[int], rel: dict[int, int]) -> float:
    return next((1 / p for p, d in enumerate(rank, 1) if rel.get(d) == 2), 0.0)


def medir(buscar, consultas, rels) -> list[dict]:
    """buscar(texto) -> ranking. Devuelve una fila por consulta con sus tres métricas."""
    filas = []
    for (tipo, texto, _), rel in zip(consultas, rels):
        r = buscar(texto)
        filas.append({"tipo": tipo, "consulta": texto, "ranking": r[:10],
                      "ndcg": ndcg(r, rel), "recall": recall(r, rel), "rr": rr(r, rel)})
    return filas
