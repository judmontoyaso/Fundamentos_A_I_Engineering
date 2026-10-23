"""
12 · Elegir el modelo de embeddings MIDIENDO, no por el ranking de moda (manual §6).

Cinco configuraciones sobre los 10 CVs del proyecto integrador (Módulo 9) y 10
consultas SOLO de paráfrasis (sin palabras en común con el CV correcto):
  - MiniLM multilingüe (el que usa el curso por defecto)
  - E5-small multilingüe SIN prefijos
  - E5-small multilingüe CON prefijos "query:" / "passage:" (como fue entrenado)
  - text-embedding-3-small y -large de OpenAI (API; solo si hay OPENAI_API_KEY)
Una configuración que no se puede cargar (sin red, sin clave) se salta.
Se mide recall@1, recall@3, MRR, dimensión y tiempo.

    pip install sentence-transformers numpy openai
"""
from __future__ import annotations
import os
import pathlib
import sys
import time
from importlib import import_module

import numpy as np

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-09-proyecto-integrador" / "code"))
CVS = import_module("00_datos_cvs").CVS
NOMBRES = [cv.splitlines()[0].split("·")[0].split("—")[0].strip().title() for cv in CVS]

# (consulta sin palabras en común con el CV, nombres correctos)
CONSULTAS = [
    ("procesamiento de flujos de eventos en vivo", {"Laura Gómez", "Lucía Torres"}),
    ("orquestación de contenedores e infraestructura declarativa", {"Diego Ruiz"}),
    ("aprendizaje profundo para predicciones", {"Valentina Cruz"}),
    ("cumplimiento normativo de seguridad informática en entidades financieras", {"Andrés Pardo"}),
    ("gestión de la calidad en una planta industrial", {"Sofía León"}),
    ("dirección de producto de software por suscripción", {"Marta Sol"}),
    ("desarrollo en el ecosistema de Microsoft para contabilidad", {"Camilo Herrera"}),
    ("programador principiante de servicios web en JavaScript", {"Juan Ríos"}),
    ("consultas a bases de datos relacionales, nivel inicial", {"Pedro Malo"}),
    ("líder de ingeniería de datos con inglés fluido", {"Lucía Torres"}),
]


def local(nombre: str, prefijo_q: str = "", prefijo_d: str = ""):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(nombre)
    return (lambda textos: m.encode([prefijo_q + t for t in textos], normalize_embeddings=True),
            lambda textos: m.encode([prefijo_d + t for t in textos], normalize_embeddings=True))


def openai_emb(nombre: str):
    from openai import OpenAI
    cliente = OpenAI()

    def f(textos):
        v = np.array([d.embedding for d in cliente.embeddings.create(model=nombre, input=textos).data])
        return v / np.linalg.norm(v, axis=1, keepdims=True)
    return f, f


def evaluar(emb_consulta, emb_doc) -> dict:
    t = time.time()
    docs = emb_doc(CVS)
    consultas = emb_consulta([q for q, _ in CONSULTAS])
    seg = time.time() - t
    r1 = r3 = rr = 0.0
    fallos = []
    for (q, correctos), qv in zip(CONSULTAS, consultas):
        orden = [NOMBRES[i] for i in np.argsort(-(docs @ qv))]
        r1 += bool(correctos & set(orden[:1]))
        r3 += len(correctos & set(orden[:3])) / len(correctos)
        rr += 1 / (1 + min(orden.index(n) for n in correctos))
        if not correctos & set(orden[:1]):
            fallos.append(f"«{q}» -> {orden[0]}")
    n = len(CONSULTAS)
    return {"recall@1": r1 / n, "recall@3": r3 / n, "MRR": rr / n, "dim": docs.shape[1], "seg": seg,
            "fallos": fallos}


if __name__ == "__main__":
    configs = {
        "MiniLM multilingüe": lambda: local("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        "E5-small sin prefijos": lambda: local("intfloat/multilingual-e5-small"),
        "E5-small con prefijos": lambda: local("intfloat/multilingual-e5-small", "query: ", "passage: "),
    }
    if os.getenv("OPENAI_API_KEY"):
        configs["text-embedding-3-small (API)"] = lambda: openai_emb("text-embedding-3-small")
        configs["text-embedding-3-large (API)"] = lambda: openai_emb("text-embedding-3-large")

    print(f"{len(CVS)} CVs · {len(CONSULTAS)} consultas de paráfrasis\n")
    print(f"{'modelo':30} {'recall@1':>9} {'recall@3':>9} {'MRR':>6} {'dim':>5} {'seg':>6}")
    fallos = {}
    for nombre, crear in configs.items():
        try:
            r = evaluar(*crear())
        except Exception as e:                  # sin red, sin clave o sin el modelo descargado
            print(f"{nombre:30} no disponible ({type(e).__name__})")
            continue
        fallos[nombre] = r["fallos"]
        print(f"{nombre:30} {r['recall@1']:9.2f} {r['recall@3']:9.2f} {r['MRR']:6.2f} {r['dim']:5} {r['seg']:6.1f}")
    print("\nConsultas cuyo primer resultado es incorrecto:")
    for nombre, f in fallos.items():
        print(f"  {nombre}: {f or 'ninguna'}")
    print("\nLa primera ejecución de un modelo local incluye su descarga en 'seg'. Con 10 consultas, una diferencia")
    print("de 0.1 es una sola consulta: mira cuáles falla cada modelo antes de cambiar el del sistema.")
