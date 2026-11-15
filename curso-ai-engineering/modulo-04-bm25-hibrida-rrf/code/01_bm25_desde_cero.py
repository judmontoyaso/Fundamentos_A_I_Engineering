"""
01 · BM25 desde cero: tokenizador en español, IDF, saturación y longitud.

Sin dependencias externas. Además de la demo, este archivo es la librería BM25
que usan los demás scripts del módulo (tokenizar, BM25, vectores dispersos).

    python 01_bm25_desde_cero.py
"""
from __future__ import annotations
import math
import re
import unicodedata
import zlib
from collections import Counter

STOPWORDS = set("""
a al algo ante con contra de del desde durante e el en entre era es esta este esto fue ha han hasta la las le
lo los mas me mi muy no o otra otro para pero por que se ser si sin sobre su sus tambien te tiene u un una uno y ya
""".split())

# Términos técnicos que el corte por puntuación destruiría.
EXCEPCIONES = {".net": "dotnet", "c#": "csharp", "c++": "cpp", "f#": "fsharp"}

_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.]*[a-z0-9+#]|[a-z0-9]")


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def tokenizar(texto: str) -> list[str]:
    """Minúsculas, sin tildes, respeta términos técnicos y quita stopwords.
    La consulta y los documentos DEBEN pasar por esta misma función."""
    t = _sin_tildes(texto.lower())
    for original, canonico in EXCEPCIONES.items():
        t = t.replace(original, f" {canonico} ")
    return [tok for tok in _TOKEN.findall(t) if tok not in STOPWORDS]


class BM25:
    """BM25 clásico (Robertson et al.) sobre una colección en memoria."""

    def __init__(self, documentos: list[str], k1: float = 1.2, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenizar(d) for d in documentos]
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(self.N, 1)
        self.tf = [Counter(d) for d in self.docs]
        df = Counter(t for d in self.docs for t in set(d))
        self.idf = {t: math.log((self.N - n + 0.5) / (n + 0.5) + 1) for t, n in df.items()}

    def factor_tf(self, f: int, largo: int) -> float:
        """Aporte de un término que aparece f veces en un documento de `largo` tokens."""
        return f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * largo / self.avgdl))

    def puntaje(self, consulta: str, i: int, detalle: bool = False):
        aportes = {}
        for q in tokenizar(consulta):
            f = self.tf[i].get(q, 0)
            if f:
                aportes[q] = self.idf[q] * self.factor_tf(f, len(self.docs[i]))
        total = sum(aportes.values())
        return (total, aportes) if detalle else total

    def buscar(self, consulta: str, k: int = 5) -> list[tuple[int, float]]:
        res = [(i, self.puntaje(consulta, i)) for i in range(self.N)]
        return sorted([r for r in res if r[1] > 0], key=lambda r: -r[1])[:k]


# ---------- BM25 como vector disperso (para Qdrant, §9) ----------
def indice_termino(termino: str) -> int:
    """Índice estable entre ejecuciones. Ojo: hash() de Python cambia en cada proceso."""
    return zlib.crc32(termino.encode("utf-8")) & 0x7FFFFFFF


def vector_documento(texto: str, avgdl: float, k1: float = 1.2, b: float = 0.75) -> dict:
    """Valores = factor de frecuencia de BM25. La base de datos aplica el IDF."""
    toks = tokenizar(texto)
    largo = len(toks)
    tf = Counter(toks)
    valores = {indice_termino(t): f * (k1 + 1) / (f + k1 * (1 - b + b * largo / avgdl)) for t, f in tf.items()}
    return {"indices": list(valores), "values": list(valores.values())}


def vector_consulta(texto: str) -> dict:
    """Cada término de la consulta pesa 1: el producto punto suma IDF × factor_tf = BM25."""
    idx = sorted({indice_termino(t) for t in tokenizar(texto)})
    return {"indices": idx, "values": [1.0] * len(idx)}


if __name__ == "__main__":
    print("== Tokenizador ==")
    ejemplo = "Desarrolladora .NET y C#; experiencia en Node.js, Python 3.12 y programación en AWS."
    print(f"  {ejemplo}\n  -> {tokenizar(ejemplo)}\n")

    cvs = [
        "Tech Lead de datos: pipelines con Apache Kafka y Flink en tiempo real. Migración a AWS.",
        "Arquitecto cloud certificado en Amazon Web Services. Terraform, Kubernetes y Python.",
        "Auditor líder ISO 27001 en banca. Seguridad de la información.",
        "Coordinadora de calidad ISO 9001. Auditorías internas en manufactura.",
        "Desarrollador .NET y C# con SQL Server. Python, Python, Python, Python y Python.",
    ]
    bm25 = BM25(cvs)

    print("== IDF: los términos raros pesan más ==")
    for t in ("iso", "27001", "python", "aws"):
        print(f"  {t:8} aparece en {sum(t in d for d in bm25.docs)} doc(s)  ->  IDF = {bm25.idf.get(t, 0):.2f}")

    print("\n== Saturación (k1=1.2, documento de largo medio) ==")
    for f in (1, 2, 5, 10, 100):
        print(f"  f={f:<3}  aporte = {bm25.factor_tf(f, bm25.avgdl):.2f}")

    for consulta in ("ISO 27001", "aws kafka", "python"):
        print(f"\n== Consulta: {consulta!r} ==")
        for i, s in bm25.buscar(consulta, k=3):
            _, aportes = bm25.puntaje(consulta, i, detalle=True)
            desglose = ", ".join(f"{t}={a:.2f}" for t, a in aportes.items())
            print(f"  {s:5.2f}  doc {i}  [{desglose}]  {cvs[i][:55]}")
    # Observa en 'ISO 27001': el doc de ISO 9001 también suma por 'iso', pero '27001'
    # (raro) decide. Y en 'python': el doc que lo repite 5 veces no gana 5 veces más.
