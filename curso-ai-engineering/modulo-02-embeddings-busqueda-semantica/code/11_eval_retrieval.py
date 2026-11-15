"""
11 · Eval de retrieval: recall@k, precision@k y MRR.

Sin un set etiquetado, "mejorar la búsqueda" es opinión. Esto convierte la
calidad de tu buscador en un número que puedes defender y seguir en el tiempo.

Independiente de la vector DB: le pasas, por cada consulta, los IDs que tu
buscador devolvió (rankeados) y los IDs realmente relevantes (etiquetados a mano).

    pip install numpy
"""
from statistics import mean


def recall_at_k(recuperados: list, relevantes: set, k: int) -> float:
    if not relevantes:
        return 0.0
    top = set(recuperados[:k])
    return len(top & relevantes) / len(relevantes)


def precision_at_k(recuperados: list, relevantes: set, k: int) -> float:
    if k == 0:
        return 0.0
    top = recuperados[:k]
    return sum(1 for r in top if r in relevantes) / k


def reciprocal_rank(recuperados: list, relevantes: set) -> float:
    for i, r in enumerate(recuperados, start=1):
        if r in relevantes:
            return 1.0 / i
    return 0.0


def evaluar(casos: list[dict], k: int = 5) -> dict:
    """casos = [{'query': str, 'recuperados': [ids...], 'relevantes': {ids...}}, ...]"""
    recalls = [recall_at_k(c["recuperados"], c["relevantes"], k) for c in casos]
    precs = [precision_at_k(c["recuperados"], c["relevantes"], k) for c in casos]
    mrrs = [reciprocal_rank(c["recuperados"], c["relevantes"]) for c in casos]
    return {f"recall@{k}": mean(recalls), f"precision@{k}": mean(precs), "mrr": mean(mrrs)}


if __name__ == "__main__":
    # Mini set etiquetado de ejemplo: IDs de CVs relevantes marcados a mano.
    casos = [
        {"query": "streaming de datos",     "recuperados": [1, 3, 2, 5, 4], "relevantes": {1}},
        {"query": "product manager saas",   "recuperados": [3, 1, 4, 2, 5], "relevantes": {3}},
        {"query": "backend junior",         "recuperados": [4, 2, 1, 3, 5], "relevantes": {2}},
    ]
    metricas = evaluar(casos, k=5)
    for nombre, valor in metricas.items():
        print(f"{nombre:>12} = {valor:.3f}")
    print("\nInterpretación: recall@5 alto = el relevante casi siempre está en el top 5.")
    print("MRR alto = además sale arriba. Sigue estos números al cambiar modelo o chunking.")
