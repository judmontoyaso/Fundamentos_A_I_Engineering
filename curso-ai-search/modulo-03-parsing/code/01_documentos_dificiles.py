"""
01 · Los CVs como llegan de verdad: PDF de texto, PDF a dos columnas y PDF escaneado (manual §2). Sin LLM.

Cada CV se maqueta desde sus hechos con dos bloques: a la izquierda nombre, rol, ciudad y experiencia; a la
derecha tecnologías, inglés y certificación. Un tercio de los PDFs tiene una columna, otro tercio dos (escritas
línea a línea, alternando columnas, como hacen muchas herramientas que generan CVs) y otro tercio es una imagen
sin capa de texto (un escaneo). El TEXTO DE REFERENCIA de cada documento (la columna izquierda y después la
derecha) se guarda aparte: es lo que una ingesta perfecta debería recuperar.
Guarda salida/docs/<id>.pdf y salida/docs/referencia.json.
"""
from __future__ import annotations
import json
import pathlib
import sys
from collections import Counter
from importlib import import_module

import pymupdf

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
DOCS = ac.SALIDA / "docs"
FORMATOS = {1: "texto", 2: "dos columnas", 0: "escaneado"}


def bloques(h: dict) -> tuple[list[str], list[str]]:
    izq = [h["nombre"], h["rol"].capitalize(), f"{h['ciudad']}{' · acepta remoto' if h['remoto'] else ''}", "Experiencia:"]
    izq += [f"{t['cargo'].capitalize()}, {t['empresa']} ({t['inicio']}-{t['fin'] or 'actualidad'})" for t in h["trabajos"]]
    if not h["trabajos"]:
        izq.append("Recién egresado")
    der = ["Tecnologías:"] + [s for s in h["skills"]] + [f"Inglés: {h['ingles'] or 'no indicado'}"]
    if h["certificacion"]:
        der.append(f"Certificación: {h['certificacion']}")
    return izq, der


def formato(cv_id: int) -> str:
    return FORMATOS[cv_id % 3]


def pdf(cv_id: int, h: dict) -> pymupdf.Document:
    izq, der = bloques(h)
    doc = pymupdf.open()
    pag = doc.new_page(width=595, height=842)
    f = formato(cv_id)
    if f == "dos columnas":
        for k in range(max(len(izq), len(der))):           # línea izquierda, línea derecha, siguiente fila...
            y = 60 + 16 * k
            if k < len(izq):
                pag.insert_text((40, y), izq[k], fontsize=10)
            if k < len(der):
                pag.insert_text((330, y), der[k], fontsize=10)
        return doc
    for k, linea in enumerate(izq + [""] + der):
        pag.insert_text((40, 60 + 16 * k), linea, fontsize=10)
    if f == "escaneado":                                    # se rasteriza: solo queda una imagen
        img = pag.get_pixmap(dpi=110)
        esc = pymupdf.open()
        p2 = esc.new_page(width=595, height=842)
        p2.insert_image(p2.rect, pixmap=img)
        return esc
    return doc


if __name__ == "__main__":
    DOCS.mkdir(parents=True, exist_ok=True)
    referencia = {}
    for cv in ac.cvs():
        izq, der = bloques(cv["hechos"])
        referencia[cv["id"]] = {"formato": formato(cv["id"]), "texto": "\n".join(izq + der)}
        pdf(cv["id"], cv["hechos"]).save(DOCS / f"{cv['id']}.pdf")
    (DOCS / "referencia.json").write_text(json.dumps(referencia, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(referencia)} PDFs en {DOCS} · {dict(Counter(r['formato'] for r in referencia.values()))}")
    ejemplo = next(i for i, r in referencia.items() if r["formato"] == "dos columnas")
    print(f"\nTexto de referencia del #{ejemplo} (dos columnas):\n{referencia[ejemplo]['texto']}")
