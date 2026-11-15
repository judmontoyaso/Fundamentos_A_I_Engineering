"""
06 · Embeddings reales + Matryoshka (truncar dimensiones).

Genera embeddings con un proveedor (API) o localmente, y demuestra dos cosas:
  - La búsqueda léxica falla donde la semántica acierta (el caso de la §1).
  - Puedes TRUNCAR el vector (Matryoshka) y perder poca calidad -> ahorro de RAM.

Dos backends: 'openai' (API) o 'local' (sentence-transformers / BGE).
Elige con la variable de entorno EMB_BACKEND.

    pip install numpy
    # API:   pip install openai   ; export OPENAI_API_KEY=...
    # local: pip install sentence-transformers
"""
import os
from functools import lru_cache
import numpy as np

BACKEND = os.getenv("EMB_BACKEND", "openai")


@lru_cache(maxsize=2)
def _modelo_local(nombre: str):
    """Cargar un modelo local tarda segundos: se hace una sola vez por proceso."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(nombre)


def embed(textos: list[str]) -> np.ndarray:
    if BACKEND == "openai":
        from openai import OpenAI
        client = OpenAI()
        modelo = os.getenv("EMB_MODEL", "text-embedding-3-small")  # 1536 dims, soporta Matryoshka
        resp = client.embeddings.create(model=modelo, input=textos)
        return np.array([d.embedding for d in resp.data], dtype=float)
    else:
        m = _modelo_local(os.getenv("EMB_MODEL", "BAAI/bge-m3"))
        return np.asarray(m.encode(textos, normalize_embeddings=True), dtype=float)


def coseno(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def truncar(v: np.ndarray, dims: int) -> np.ndarray:
    """Matryoshka: usa las primeras `dims` componentes y re-normaliza."""
    t = v[:dims]
    return t / np.linalg.norm(t)


if __name__ == "__main__":
    query = "experiencia en procesamiento de datos en streaming"
    docs = [
        "4 años construyendo pipelines con Apache Kafka y Flink en tiempo real",  # relevante, 0 palabras en común
        "diseñador gráfico experto en Photoshop e Illustrator",                   # irrelevante
        "desarrollador backend con PostgreSQL y APIs REST",                       # algo relacionado
    ]

    vecs = embed([query] + docs)
    q, dvecs = vecs[0], vecs[1:]

    print("== Semántica: el candidato de Kafka/Flink gana pese a no compartir palabras ==")
    for doc, dv in sorted(zip(docs, dvecs), key=lambda x: -coseno(q, x[1])):
        print(f"  {coseno(q, dv):+.3f}  {doc[:60]}")

    print("\n== Matryoshka: truncar dimensiones ==")
    print("   Solo es fiable en modelos ENTRENADOS para ello (text-embedding-3-*, bge-m3, nomic).")
    print("   En otros (p. ej. MiniLM) truncar puede degradar el ranking sin avisar.")
    full_dim = vecs.shape[1]
    for d in sorted({full_dim, *[x for x in (512, 256, 128) if x < full_dim]}, reverse=True):
        qt = truncar(q, d)
        rank = [doc for doc, dv in sorted(zip(docs, dvecs),
                                          key=lambda x: -coseno(qt, truncar(x[1], d)))]
        print(f"  dims={d:>5}: 1º -> {rank[0][:50]}")
