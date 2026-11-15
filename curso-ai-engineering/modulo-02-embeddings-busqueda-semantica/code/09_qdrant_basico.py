"""
09 · Qdrant en la práctica: crear colección, upsert y search.

Con servidor (Docker):
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
Sin Docker: QDRANT_URL=:memory:  (Qdrant embebido en el proceso, se borra al salir)

    pip install qdrant-client numpy openai   (o sentence-transformers para local)
"""
import os
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Reutilizamos el embedder del script 06
from importlib import import_module
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).parent))
embed = import_module("06_embeddings_reales").embed  # type: ignore

COLECCION = "cvs_demo"


def main() -> None:
    # location acepta una URL de servidor o ":memory:" (modo embebido, sin Docker)
    client = QdrantClient(location=os.getenv("QDRANT_URL", "http://localhost:6333"))

    docs = [
        ("Laura", "senior", ["datos"],      "Tech Lead con Kafka, Flink y streaming en tiempo real"),
        ("Juan",  "junior", ["ingenieria"], "Desarrollador junior de APIs REST en Node.js"),
        ("Marta", "senior", ["producto"],   "Product manager con 8 años lanzando productos SaaS"),
    ]
    textos = [d[3] for d in docs]
    vecs = embed(textos)
    dim = vecs.shape[1]

    # 1. Crear colección (métrica COSINE para casar con el embedder)
    if client.collection_exists(COLECCION):
        client.delete_collection(COLECCION)
    client.create_collection(
        collection_name=COLECCION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    # 2. Upsert: id + vector + payload (metadata filtrable)
    client.upsert(COLECCION, points=[
        PointStruct(id=i, vector=vecs[i].tolist(),
                    payload={"nombre": d[0], "nivel": d[1], "areas": d[2], "resumen": d[3]})
        for i, d in enumerate(docs)
    ])

    # 3. Search semántico
    consulta = "quién sabe de procesamiento de datos en tiempo real"
    qv = embed([consulta])[0].tolist()
    hits = client.query_points(COLECCION, query=qv, limit=3).points

    print(f"Consulta: {consulta!r}\n")
    for h in hits:
        print(f"  {h.score:.3f}  {h.payload['nombre']:6}  [{h.payload['nivel']}]  {h.payload['resumen'][:45]}")


if __name__ == "__main__":
    main()
