"""
03 · Reciprocal Rank Fusion desde cero, y por qué sumar puntajes es frágil.

Sin dependencias externas.

    python 03_rrf.py
"""
from __future__ import annotations


def rrf(rankings: list[list[str]], k: int = 60, pesos: list[float] | None = None) -> list[tuple[str, float]]:
    """rankings: listas de ids ordenadas de mejor a peor (puesto 1 = primero).
    RRF(d) = Σ peso_r / (k + puesto_r(d))."""
    pesos = pesos or [1.0] * len(rankings)
    total: dict[str, float] = {}
    for ranking, w in zip(rankings, pesos):
        for puesto, doc in enumerate(ranking, start=1):
            total[doc] = total.get(doc, 0.0) + w / (k + puesto)
    return sorted(total.items(), key=lambda x: -x[1])


def minmax(puntajes: dict[str, float]) -> dict[str, float]:
    lo, hi = min(puntajes.values()), max(puntajes.values())
    return {d: (s - lo) / (hi - lo) if hi > lo else 1.0 for d, s in puntajes.items()}


def fusion_por_puntaje(a: dict[str, float], b: dict[str, float], alpha: float = 0.5) -> list[tuple[str, float]]:
    """α·minmax(a) + (1−α)·minmax(b); un doc ausente en una lista aporta 0 en ella."""
    na, nb = minmax(a), minmax(b)
    docs = set(a) | set(b)
    return sorted(((d, alpha * na.get(d, 0) + (1 - alpha) * nb.get(d, 0)) for d in docs), key=lambda x: -x[1])


if __name__ == "__main__":
    bm25 = ["A", "B", "C"]
    semantica = ["C", "A", "D"]

    print("== RRF (k=60): el ejemplo del manual §7 ==")
    for d, s in rrf([bm25, semantica]):
        print(f"  {d}  {s:.5f}")

    print("\n== Efecto de k: con k pequeño el primer puesto pesa mucho más ==")
    for k in (1, 60):
        print(f"  k={k:<3} ->", ", ".join(f"{d}:{s:.4f}" for d, s in rrf([bm25, semantica], k=k)))

    print("\n== Por qué la suma normalizada es frágil ==")
    p_bm25 = {"A": 12.4, "B": 3.1, "C": 2.9}
    p_cos = {"C": 0.82, "A": 0.80, "D": 0.79}
    print("  coseno crudo     :", p_cos)
    print("  coseno min-max   :", {d: round(v, 2) for d, v in minmax(p_cos).items()},
          "<- una diferencia de 0.03 se volvió de 1.0")
    for alpha in (0.3, 0.5, 0.7):
        orden = [d for d, _ in fusion_por_puntaje(p_bm25, p_cos, alpha)]
        print(f"  suma con α={alpha}  : {orden}")
    print("  RRF (sin α)      :", [d for d, _ in rrf([bm25, semantica])])
    print("\nCon la suma, el orden depende de α y de la forma de las distribuciones.")
    print("RRF solo mira los puestos: nada que calibrar.")
