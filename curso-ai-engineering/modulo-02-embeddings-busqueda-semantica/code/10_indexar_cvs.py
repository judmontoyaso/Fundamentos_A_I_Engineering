"""
10 · Indexar los CVs estructurados del Módulo 1 en Qdrant.

Conecta los dos módulos: toma objetos CV (estructura del Módulo 1), construye
un TEXTO DISEÑADO para embedear, lo sube a Qdrant con payload = campos del CV,
y expone buscar(). El texto que embedeas decide qué se puede encontrar.

    docker run -p 6333:6333 qdrant/qdrant
    pip install qdrant-client numpy openai
"""
import os
import sys
import pathlib
from dataclasses import dataclass, field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

sys.path.append(str(pathlib.Path(__file__).parent))
from importlib import import_module
embed = import_module("06_embeddings_reales").embed  # type: ignore

COLECCION = "cvs"


# CV mínimo para el ejemplo (en el proyecto real usa el modelo Pydantic del Módulo 1).
@dataclass
class CV:
    nombre_completo: str
    nivel: str
    areas: list[str]
    skills: list[str]
    cargos: list[str] = field(default_factory=list)


def texto_para_embedding(cv: CV) -> str:
    """El 'documento' que se indexa: concatena lo semánticamente relevante
    para buscar. NO es el PDF crudo; es un texto que tú diseñas."""
    return (
        f"{cv.nombre_completo}. Nivel {cv.nivel}. "
        f"Áreas: {', '.join(cv.areas)}. "
        f"Skills: {', '.join(cv.skills)}. "
        f"Experiencia: {'; '.join(cv.cargos)}."
    )


def indexar(cvs: list[CV]) -> QdrantClient:
    client = QdrantClient(location=os.getenv("QDRANT_URL", "http://localhost:6333"))
    textos = [texto_para_embedding(cv) for cv in cvs]
    vecs = embed(textos)
    if client.collection_exists(COLECCION):
        client.delete_collection(COLECCION)
    client.create_collection(
        COLECCION, vectors_config=VectorParams(size=vecs.shape[1], distance=Distance.COSINE)
    )
    client.upsert(COLECCION, points=[
        PointStruct(id=i, vector=vecs[i].tolist(), payload={
            "nombre": cv.nombre_completo, "nivel": cv.nivel,
            "areas": cv.areas, "skills": cv.skills,
        }) for i, cv in enumerate(cvs)
    ])
    return client


def buscar(client: QdrantClient, consulta: str, k: int = 5):
    qv = embed([consulta])[0].tolist()
    return client.query_points(COLECCION, query=qv, limit=k).points


if __name__ == "__main__":
    cvs = [
        CV("Laura Gómez", "senior", ["datos"], ["kafka", "flink", "python", "aws"],
           ["Tech Lead en Globex", "Backend en Acme"]),
        CV("Juan Ríos", "junior", ["ingenieria"], ["node.js", "rest", "docker"],
           ["Dev junior en Startup X"]),
        CV("Marta Sol", "senior", ["producto", "datos"], ["sql", "tableau", "roadmap"],
           ["PM en SaaS Co"]),
    ]
    client = indexar(cvs)

    # Consulta SIN las palabras exactas del CV de Laura:
    hits = buscar(client, "experto en streaming de datos en tiempo real", k=3)
    for h in hits:
        print(f"{h.score:.3f}  {h.payload['nombre']:14} {h.payload['areas']}")

    margen = hits[0].score - hits[1].score
    print(f"\nMargen entre el 1º y el 2º: {margen:.3f}")
    if margen < 0.05:
        print("Empate técnico. Mira el texto indexado: Marta lleva 'datos' en sus áreas y la")
        print("consulta dice 'datos', mientras que Laura dice 'kafka, flink' y el modelo tiene que")
        print("saber que eso es streaming. Un modelo pequeño lo sabe a medias. Qué hacer:")
        print("  - medir con recall@k (11_eval_retrieval.py) en vez de fiarte de un ejemplo,")
        print("  - probar otro texto_para_embedding o un modelo mejor (bge-m3, text-embedding-3),")
        print("  - combinar con búsqueda léxica (BM25): la búsqueda híbrida del Módulo 4.")
