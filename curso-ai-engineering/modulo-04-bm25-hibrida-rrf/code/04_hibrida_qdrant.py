"""
04 · Búsqueda híbrida de punta a punta en Qdrant: denso + BM25 disperso + RRF.

Cada CV guarda dos vectores con nombre ("denso" y "bm25"). La consulta híbrida
hace un prefetch por buscador y fusiona con RRF (manual §9-§10).

    Con servidor: docker run -p 6333:6333 qdrant/qdrant
    Sin Docker:   QDRANT_URL=:memory:
    pip install qdrant-client numpy   (+ embedder del Módulo 2)
"""
from __future__ import annotations
import os
import sys
import pathlib
from importlib import import_module
from qdrant_client import QdrantClient, models

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.append(str(AQUI))
sys.path.append(str(AQUI.parents[1] / "modulo-02-embeddings-busqueda-semantica" / "code"))
bm25lib = import_module("01_bm25_desde_cero")
embed = import_module("06_embeddings_reales").embed  # type: ignore

COL = "cvs_hibrida"

CORPUS = [
    {"id": 1, "nombre": "Laura Gómez", "nivel": "senior", "texto":
        "Tech Lead de datos. Lideró un equipo de 6 ingenieros construyendo pipelines con Apache Kafka y Flink "
        "para procesar eventos al instante. Migración de la plataforma a AWS."},
    {"id": 2, "nombre": "Juan Ríos", "nivel": "junior", "texto":
        "Desarrollador junior. APIs REST en Node.js y Express, despliegues con Docker en Heroku."},
    {"id": 3, "nombre": "Marta Sol", "nivel": "senior", "texto":
        "Product Manager con 8 años lanzando productos SaaS. Define el roadmap, métricas de producto y análisis "
        "de datos de uso con SQL y Tableau."},
    {"id": 4, "nombre": "Andrés Pardo", "nivel": "senior", "texto":
        "Auditor líder ISO 27001. Implementó sistemas de gestión de seguridad de la información y controles de "
        "acceso en banca."},
    {"id": 5, "nombre": "Sofía León", "nivel": "semi-senior", "texto":
        "Coordinadora de calidad ISO 9001. Gestión de procesos, auditorías internas y mejora continua en "
        "manufactura."},
    {"id": 6, "nombre": "Diego Ruiz", "nivel": "senior", "texto":
        "Arquitecto cloud certificado en Amazon Web Services. Infraestructura como código con Terraform y "
        "Kubernetes."},
    {"id": 7, "nombre": "Valentina Cruz", "nivel": "semi-senior", "texto":
        "Científica de datos. Modelos de machine learning en Python con scikit-learn y PyTorch; visualización "
        "de resultados para negocio."},
    {"id": 8, "nombre": "Camilo Herrera", "nivel": "semi-senior", "texto":
        "Desarrollador .NET y C# con SQL Server. Mantenimiento de sistemas ERP y facturación electrónica."},
]


def construir(corpus: list[dict] = CORPUS) -> QdrantClient:
    client = QdrantClient(location=os.getenv("QDRANT_URL", "http://localhost:6333"))
    textos = [c["texto"] for c in corpus]
    densos = embed(textos)
    # avgdl de la colección: lo necesita el factor de frecuencia de BM25 (§3).
    avgdl = sum(len(bm25lib.tokenizar(t)) for t in textos) / len(textos)

    if client.collection_exists(COL):
        client.delete_collection(COL)
    client.create_collection(
        COL,
        vectors_config={"denso": models.VectorParams(size=densos.shape[1], distance=models.Distance.COSINE)},
        # Modifier.IDF: Qdrant calcula el IDF de cada término con la colección.
        sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    client.upsert(COL, points=[
        models.PointStruct(
            id=c["id"],
            payload={k: v for k, v in c.items() if k != "id"},
            vector={
                "denso": densos[i].tolist(),
                "bm25": models.SparseVector(**bm25lib.vector_documento(c["texto"], avgdl)),
            },
        )
        for i, c in enumerate(corpus)
    ])
    return client


def buscar(client: QdrantClient, consulta: str, modo: str = "hibrida", k: int = 5,
           nivel: str | None = None, candidatos: int = 20):
    """modo: 'bm25' | 'semantica' | 'hibrida' (RRF, k=60)."""
    filtro = models.Filter(must=[models.FieldCondition(key="nivel", match=models.MatchValue(value=nivel))]) \
        if nivel else None
    denso = embed([consulta])[0].tolist()
    disperso = bm25lib.vector_consulta(consulta)
    tiene_terminos = bool(disperso["indices"])  # una consulta solo de stopwords no tiene vector BM25

    if modo == "semantica":
        return client.query_points(COL, query=denso, using="denso", query_filter=filtro, limit=k).points
    if modo == "bm25":
        if not tiene_terminos:
            return []
        return client.query_points(COL, query=models.SparseVector(**disperso), using="bm25",
                                   query_filter=filtro, limit=k).points

    prefetch = [models.Prefetch(query=denso, using="denso", filter=filtro, limit=candidatos)]
    if tiene_terminos:
        prefetch.append(models.Prefetch(query=models.SparseVector(**disperso), using="bm25",
                                        filter=filtro, limit=candidatos))
    return client.query_points(COL, prefetch=prefetch, query=models.RrfQuery(rrf=models.Rrf(k=60)),
                               limit=k).points


if __name__ == "__main__":
    client = construir()

    print("== Control: el BM25 de Qdrant coincide con el BM25 hecho a mano (01) ==")
    ref = bm25lib.BM25([c["texto"] for c in CORPUS])
    for h in buscar(client, "ISO 27001 auditorías", modo="bm25", k=3):
        i = [c["id"] for c in CORPUS].index(h.id)
        print(f"  {h.payload['nombre']:15} Qdrant={h.score:.4f}  a mano={ref.puntaje('ISO 27001 auditorías', i):.4f}")

    for consulta in ("AWS", "experiencia con streaming"):
        print(f"\n== {consulta!r} ==")
        for modo in ("bm25", "semantica", "hibrida"):
            nombres = [h.payload["nombre"] for h in buscar(client, consulta, modo=modo, k=3)]
            print(f"  {modo:10} {nombres or '(sin resultados)'}")

    print("\n== Híbrida + filtro de metadata: 'datos', solo seniors ==")
    for h in buscar(client, "datos", modo="hibrida", k=3, nivel="senior"):
        print(f"  {h.score:.4f}  {h.payload['nombre']} [{h.payload['nivel']}]")
