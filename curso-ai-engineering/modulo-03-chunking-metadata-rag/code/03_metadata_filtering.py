"""
03 · Metadata filtering en Qdrant: búsqueda vectorial + filtro, en una query.

Demuestra el PRE-filtrado (Módulo 3 §6): "parecido a esto Y senior Y del área de
datos". Qdrant combina el filtro de payload con la búsqueda vectorial de forma
nativa, reduciendo el espacio antes de comparar vectores.

    docker run -p 6333:6333 qdrant/qdrant
    pip install qdrant-client numpy   (+ embedder del Módulo 2)
"""
from __future__ import annotations
import os
import sys
import pathlib
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny,
)

M2 = pathlib.Path(__file__).resolve().parents[2] / "modulo-02-embeddings-busqueda-semantica" / "code"
sys.path.append(str(M2))
from importlib import import_module
embed = import_module("06_embeddings_reales").embed  # type: ignore

COL = "cv_chunks"


def indexar(chunks: list[dict]) -> QdrantClient:
    client = QdrantClient(location=os.getenv("QDRANT_URL", "http://localhost:6333"))
    vecs = embed([c["texto"] for c in chunks])
    if client.collection_exists(COL):
        client.delete_collection(COL)
    client.create_collection(COL, vectors_config=VectorParams(size=vecs.shape[1], distance=Distance.COSINE))
    client.upsert(COL, points=[
        PointStruct(id=i, vector=vecs[i].tolist(), payload=chunks[i]) for i in range(len(chunks))
    ])
    # Índices de payload: filtros rápidos a escala. Solo tienen efecto en el servidor
    # Qdrant; en modo embebido (:memory:) se filtra recorriendo los puntos.
    if not os.getenv("QDRANT_URL", "").startswith(":memory:"):
        for campo in ("nivel", "areas", "seccion"):
            client.create_payload_index(COL, field_name=campo, field_schema="keyword")
    return client


def buscar(client, pregunta: str, nivel: str | None = None, area: str | None = None, k: int = 5):
    condiciones = []
    if nivel:
        condiciones.append(FieldCondition(key="nivel", match=MatchValue(value=nivel)))
    if area:
        condiciones.append(FieldCondition(key="areas", match=MatchAny(any=[area])))
    filtro = Filter(must=condiciones) if condiciones else None
    qv = embed([pregunta])[0].tolist()
    return client.query_points(COL, query=qv, query_filter=filtro, limit=k).points


if __name__ == "__main__":
    chunks = [
        {"cv_id": 1, "candidato": "Laura", "nivel": "senior", "areas": ["datos"], "seccion": "Experiencia",
         "texto": "Tech Lead: pipelines con Kafka y Flink para streaming en tiempo real; migración a AWS."},
        {"cv_id": 2, "candidato": "Juan", "nivel": "junior", "areas": ["ingenieria"], "seccion": "Experiencia",
         "texto": "Dev junior: APIs REST en Node.js y despliegues con Docker."},
        {"cv_id": 3, "candidato": "Marta", "nivel": "senior", "areas": ["producto"], "seccion": "Experiencia",
         "texto": "Product Manager: roadmap y métricas de productos SaaS."},
    ]
    client = indexar(chunks)

    print("== Sin filtro: 'procesamiento de datos en tiempo real' ==")
    for h in buscar(client, "procesamiento de datos en tiempo real"):
        print(f"  {h.score:.3f}  {h.payload['candidato']} [{h.payload['nivel']}]")

    print("\n== Con filtro nivel=senior, area=datos ==")
    for h in buscar(client, "procesamiento de datos en tiempo real", nivel="senior", area="datos"):
        print(f"  {h.score:.3f}  {h.payload['candidato']} [{h.payload['nivel']}]")
