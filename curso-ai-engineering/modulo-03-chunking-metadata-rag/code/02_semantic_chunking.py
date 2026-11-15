"""
02 · Chunking semántico: cortar por SIGNIFICADO, no por longitud.

Embedea frase a frase y corta donde la similitud entre frases consecutivas cae
(señal de cambio de tema). Reutiliza el embedder del Módulo 2.

    pip install numpy   (+ openai o sentence-transformers según el backend)
    EMB_BACKEND=local  para correr sin API
"""
from __future__ import annotations
import os
import re
import sys
import pathlib
import numpy as np

# Reutiliza el embedder del Módulo 2 (ajusta la ruta si moviste las carpetas).
M2 = pathlib.Path(__file__).resolve().parents[2] / "modulo-02-embeddings-busqueda-semantica" / "code"
sys.path.append(str(M2))
from importlib import import_module
embed = import_module("06_embeddings_reales").embed  # type: ignore


def frases(texto: str) -> list[str]:
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto) if f.strip()]


def coseno(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def chunk_semantico(texto: str, umbral_percentil: int = 25, verbose: bool = False) -> list[str]:
    """Corta donde la similitud frase-a-frase está en el percentil dado o por debajo
    (los 'valles' = posibles cambios de tema)."""
    fs = frases(texto)
    if len(fs) <= 1:
        return fs
    vecs = embed(fs)
    sims = [coseno(vecs[i], vecs[i + 1]) for i in range(len(fs) - 1)]
    corte = np.percentile(sims, umbral_percentil)  # similitud baja = frontera

    if verbose:
        print(f"Perfil de similitud entre frases consecutivas (corte <= {corte:.3f}):")
        for i, s in enumerate(sims):
            marca = "  ✂ corte" if s <= corte else ""
            print(f"  {s:+.3f}  {fs[i][:34]!r} → {fs[i + 1][:34]!r}{marca}")
        print()

    chunks, actual = [], [fs[0]]
    for i, s in enumerate(sims):
        if s <= corte:
            chunks.append(" ".join(actual))
            actual = [fs[i + 1]]
        else:
            actual.append(fs[i + 1])
    if actual:
        chunks.append(" ".join(actual))
    return chunks


if __name__ == "__main__":
    texto = (
        "Lidera un equipo de seis ingenieros. Define la arquitectura de datos. "
        "Construyó pipelines con Kafka y Flink para streaming en tiempo real. "
        "En su tiempo libre practica fotografía de montaña. Ha expuesto en dos galerías locales. "
        "También es voluntario enseñando programación a jóvenes los sábados."
    )
    for i, c in enumerate(chunk_semantico(texto, verbose=True), 1):
        print(f"[chunk {i}] {c}")
    # Qué observar: el ideal sería separar trabajo / fotografía / voluntariado.
    # Con frases MUY cortas y un modelo pequeño (p. ej. MiniLM), la similitud entre
    # frases vecinas es ruidosa: frases del mismo tema pueden puntuar bajo y un cambio
    # de tema puede puntuar alto. Mira el perfil impreso arriba. Por eso:
    #   - el chunking semántico rinde mejor a nivel de PÁRRAFO que de frase corta,
    #   - un modelo mejor (bge-m3, text-embedding-3) separa los temas con más margen,
    #   - y el umbral se calibra con tu eval, no a ojo (Ejercicio 3).
