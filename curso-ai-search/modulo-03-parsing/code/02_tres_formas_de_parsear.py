"""
02 · Tres formas de parsear los mismos PDFs, y cuántos hechos sobreviven en cada una (manual §3-§5).

  ingenua       : page.get_text() y nada más.
  con OCR       : si la página no tiene texto, se le pasa la imagen a un modelo con visión.
  columnas+OCR  : además, si hay dos columnas, se leen por separado (izquierda entera y después derecha),
                  agrupando las líneas por su posición horizontal.
"Hechos que sobreviven": de las tecnologías, la ciudad, los años de cada trabajo y la certificación de cada CV,
qué fracción aparece en el texto parseado. Guarda salida/parseos.json para el laboratorio 03.
El OCR se guarda en salida/ocr.json: una segunda corrida no lo vuelve a pagar.
"""
from __future__ import annotations
import base64
import json
import pathlib
import sys
from collections import defaultdict
from importlib import import_module
from statistics import mean

import pymupdf
from pydantic import BaseModel

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
dd = import_module("01_documentos_dificiles")
ac = dd.ac
ev = ac.ev
OCR_CACHE = ac.SALIDA / "ocr.json"
PIPELINES = ["ingenua", "con OCR", "columnas+OCR"]


class TextoOCR(BaseModel):
    texto: str


def ocr(cv_id: int, pagina: pymupdf.Page) -> str:
    cache = json.loads(OCR_CACHE.read_text(encoding="utf-8")) if OCR_CACHE.exists() else {}
    if str(cv_id) in cache:
        return cache[str(cv_id)]
    png = base64.b64encode(pagina.get_pixmap(dpi=110).tobytes("png")).decode()
    with ev.tz.span("ocr", tipo="llm", cv=cv_id):
        r = ev.c._cliente().chat.completions.create(
            model=ev.tz.MODELO, response_model=TextoOCR, max_retries=2,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Transcribe el texto de esta página tal como aparece, línea por línea. "
                                         "No resumas ni corrijas."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}}]}])
    cache = json.loads(OCR_CACHE.read_text(encoding="utf-8")) if OCR_CACHE.exists() else {}
    cache[str(cv_id)] = r.texto
    OCR_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return r.texto


def por_columnas(pagina: pymupdf.Page) -> str:
    lineas = []
    for b in pagina.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            texto = "".join(s["text"] for s in l["spans"]).strip()
            if texto:
                lineas.append((l["bbox"][0], l["bbox"][1], texto))
    mitad = pagina.rect.width / 2
    if not any(x >= mitad for x, _, _ in lineas):          # una sola columna: tal cual
        return "\n".join(t for _, _, t in sorted(lineas, key=lambda l: l[1]))
    izq = [t for x, y, t in sorted(lineas, key=lambda l: l[1]) if x < mitad]
    der = [t for x, y, t in sorted(lineas, key=lambda l: l[1]) if x >= mitad]
    return "\n".join(izq + der)


def parsear(cv_id: int, pipeline: str) -> str:
    pagina = pymupdf.open(dd.DOCS / f"{cv_id}.pdf")[0]
    texto = pagina.get_text()
    if pipeline == "ingenua":
        return texto
    if not texto.strip():
        return ocr(cv_id, pagina)
    return texto if pipeline == "con OCR" else por_columnas(pagina)


def hechos_presentes(h: dict, texto: str) -> float:
    t = ev.norm(texto)
    items = h["skills"] + [h["ciudad"]] + [str(tr["inicio"]) for tr in h["trabajos"]]
    if h["certificacion"]:
        items.append(h["certificacion"])
    return sum(ev.norm(x) in t for x in items) / len(items)


if __name__ == "__main__":
    if not (dd.DOCS / "referencia.json").exists():
        raise SystemExit("Corre antes 01_documentos_dificiles.py")
    referencia = json.loads((dd.DOCS / "referencia.json").read_text(encoding="utf-8"))
    hechos = {cv["id"]: cv["hechos"] for cv in ac.cvs()}
    with ev.tz.nueva_traza("parsear documentos"):
        # El OCR primero, en paralelo (los escaneados), para no pagarlo dentro del bucle
        escaneados = [i for i in hechos if dd.formato(i) == "escaneado"]
        ev.tz.en_paralelo(lambda i: ocr(i, pymupdf.open(dd.DOCS / f"{i}.pdf")[0]), [(i,) for i in escaneados])
        parseos = {p: {i: parsear(i, p) for i in hechos} for p in PIPELINES}
    print(f"Hechos que sobreviven en el texto parseado (media por CV), por formato:\n")
    print(f"{'formato':14}" + "".join(f"{p:>15}" for p in PIPELINES) + f"{'referencia':>13}")
    for f in ["texto", "dos columnas", "escaneado"]:
        ids = [i for i in hechos if dd.formato(i) == f]
        fila = [mean(hechos_presentes(hechos[i], parseos[p][i]) for i in ids) for p in PIPELINES]
        ref = mean(hechos_presentes(hechos[i], referencia[str(i)]["texto"]) for i in ids)
        print(f"{f:14}" + "".join(f"{v:>15.0%}" for v in fila) + f"{ref:>13.0%}")
    ejemplo = next(i for i in hechos if dd.formato(i) == "escaneado")
    print(f"\nOCR del #{ejemplo} (escaneado):\n{parseos['con OCR'][ejemplo][:300]}")
    (ac.SALIDA / "parseos.json").write_text(json.dumps(parseos, ensure_ascii=False), encoding="utf-8")
