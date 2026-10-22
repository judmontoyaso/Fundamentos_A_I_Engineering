"""
01 · Las familias de chunking, sin dependencias externas.

Implementa de cero: tamaño fijo (con y sin overlap) y recursivo/estructural.
Verlas por dentro te hace entender el trade-off tamaño/precisión mejor que
cualquier librería.

    python 01_chunking_estrategias.py
"""
from __future__ import annotations
import re


def chunk_fijo(texto: str, tam: int = 280, overlap: int = 0) -> list[str]:
    """Corta cada `tam` caracteres. overlap repite los últimos N al inicio del
    siguiente (tejado de tejas) para no partir ideas en la frontera."""
    chunks, i = [], 0
    paso = max(1, tam - overlap)
    while i < len(texto):
        chunks.append(texto[i:i + tam])
        i += paso
    return chunks


def chunk_recursivo(texto: str, tam: int = 280) -> list[str]:
    """Respeta fronteras naturales: intenta párrafos; si un trozo es muy grande,
    frases; si aún es grande, palabras. Los cortes caen donde el texto 'respira'."""
    separadores = ["\n\n", ". ", " "]

    def _split(t: str, nivel: int) -> list[str]:
        if len(t) <= tam or nivel >= len(separadores):
            return [t]
        sep = separadores[nivel]
        partes, buffer = [], ""
        for pieza in t.split(sep):
            cand = (buffer + sep + pieza) if buffer else pieza
            if len(cand) <= tam:
                buffer = cand
            else:
                if buffer:
                    partes.append(buffer)
                partes.extend(_split(pieza, nivel + 1) if len(pieza) > tam else [pieza])
                buffer = ""
        if buffer:
            partes.append(buffer)
        return partes

    return [c.strip() for c in _split(texto, 0) if c.strip()]


def chunk_por_secciones(texto: str) -> list[dict]:
    """Document-aware para CVs: un chunk por sección (encabezados en MAYÚSCULAS
    o líneas tipo 'Experiencia:'). Devuelve chunks con su sección como metadata."""
    lineas = texto.splitlines()
    secciones, actual, titulo = [], [], "General"
    es_titulo = re.compile(r"^\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ \t]{2,}|[A-ZÁÉÍÓÚÑ][\w ]+:)\s*$")
    for ln in lineas:
        if es_titulo.match(ln):
            if actual:
                secciones.append({"seccion": titulo, "texto": "\n".join(actual).strip()})
            titulo, actual = ln.strip().rstrip(":"), []
        else:
            actual.append(ln)
    if actual:
        secciones.append({"seccion": titulo, "texto": "\n".join(actual).strip()})
    return [s for s in secciones if s["texto"]]


if __name__ == "__main__":
    cv = (
        "EXPERIENCIA\n"
        "Tech Lead en Globex (2020-presente). Lidera un equipo de 6. Pipelines con Kafka y Flink "
        "para procesamiento en tiempo real. Migración a AWS.\n"
        "Backend Developer en Acme (2016-2020). APIs en Python y PostgreSQL.\n\n"
        "EDUCACION\n"
        "Ingeniería de Sistemas, Universidad Nacional, 2016.\n\n"
        "SKILLS\n"
        "python, go, kafka, flink, aws, postgresql, liderazgo de equipos."
    )

    print("== Fijo (tam=120, sin overlap) ==")
    for c in chunk_fijo(cv, 120):
        print("  |", repr(c[:60]))

    print("\n== Fijo (tam=120, overlap=30) — fíjate en el texto repetido ==")
    for c in chunk_fijo(cv, 120, overlap=30):
        print("  |", repr(c[:60]))

    print("\n== Recursivo (tam=160) — cortes en fronteras naturales ==")
    for c in chunk_recursivo(cv, 160):
        print("  |", repr(c[:70]))

    print("\n== Por secciones (document-aware) — el mejor para CVs ==")
    for s in chunk_por_secciones(cv):
        print(f"  [{s['seccion']}] {s['texto'][:60]!r}")
