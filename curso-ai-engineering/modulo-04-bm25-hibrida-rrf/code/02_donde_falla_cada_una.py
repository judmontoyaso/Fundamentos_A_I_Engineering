"""
02 · Dónde falla cada búsqueda: BM25 vs. semántica, consulta por consulta.

Mismos documentos, mismas consultas, dos buscadores. No está amañado: mira
qué gana cada uno y por qué (manual §1 y §5).

    pip install numpy   (+ sentence-transformers o openai, según EMB_BACKEND)
"""
from __future__ import annotations
import sys
import pathlib
from importlib import import_module

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.append(str(AQUI))
sys.path.append(str(AQUI.parents[1] / "modulo-02-embeddings-busqueda-semantica" / "code"))
bm25lib = import_module("01_bm25_desde_cero")
embed = import_module("06_embeddings_reales").embed  # type: ignore

DOCS = [
    "Auditor líder ISO 27001 en banca: seguridad de la información y controles de acceso.",
    "Coordinadora de calidad ISO 9001: auditorías internas y mejora continua en manufactura.",
    "Tech Lead de datos: pipelines con Apache Kafka y Flink para procesar eventos al instante.",
    "Arquitecto cloud certificado en Amazon Web Services, con Terraform y Kubernetes.",
    "Desarrollador .NET y C# con SQL Server para facturación electrónica.",
]

# (consulta, índice del documento correcto, qué tipo de consulta es)
CONSULTAS = [
    ("ISO 27001", 0, "código exacto"),
    ("C#", 4, "término técnico"),
    ("experiencia con streaming", 2, "paráfrasis"),
    ("nube de Amazon", 3, "mixta"),
    ("gestión de la calidad en fábricas", 1, "paráfrasis"),
]


def top_semantica(consulta: str, vdocs) -> int:
    q = embed([consulta])[0]
    sims = vdocs @ q / ((vdocs ** 2).sum(axis=1) ** 0.5 * (q @ q) ** 0.5)
    return int(sims.argmax())


if __name__ == "__main__":
    bm25 = bm25lib.BM25(DOCS)
    vdocs = embed(DOCS)
    gana = {"BM25": 0, "Semántica": 0}

    print(f"{'consulta':36} {'tipo':16} {'BM25':6} {'Semántica':9}")
    for consulta, correcto, tipo in CONSULTAS:
        hits = bm25.buscar(consulta, k=1)
        b = hits[0][0] if hits else None          # BM25 puede no devolver nada
        s = top_semantica(consulta, vdocs)
        marca = lambda x: "✓" if x == correcto else ("—" if x is None else "✗")
        gana["BM25"] += b == correcto
        gana["Semántica"] += s == correcto
        print(f"{consulta:36} {tipo:16} {marca(b):6} {marca(s):9}")

    print(f"\nAciertos en el top-1: {gana}")
    print("— = BM25 no encontró ningún término en común (no puede devolver nada).")
    print("Lo que importa no es quién gana más, sino que fallan en consultas DISTINTAS:")
    print("esa es la razón para combinarlas (manual §5-§7).")
