"""
03 · Validar cada CV sintético con código antes de usarlo, y medir si son tan variados como los reales (manual §5-§6).

Un CV sintético solo sirve si el texto dice lo que dicen sus hechos (si no, su etiqueta es falsa) y
si de verdad tiene la variación que se pidió (si no, la cobertura es una ilusión). Se rechaza lo que
no pasa, y se compara la diversidad con los 30 CVs escritos a mano (similitud media entre pares).
Guarda salida/sinteticos_validos.jsonl.
"""
from __future__ import annotations
import itertools
import pathlib
import re
import sys
from collections import Counter
from importlib import import_module

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
dh = import_module("01_dimensiones_y_hechos")
ev = dh.ev
datos = import_module("ev_datos")
sys.path.append(str(ev.RAIZ / "modulo-02-embeddings-busqueda-semantica" / "code"))

PALABRAS = {  # 1-15 en los tres idiomas, sin tildes (se compara normalizado)
    "español": "uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince",
    "inglés": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen",
    "portugués": "um dois tres quatro cinco seis sete oito nove dez onze doze treze catorze quinze",
}
VIGENTE = re.compile(r"hoy|actualidad|presente|present|current|now|atual|hoje|momento", re.IGNORECASE)


def problemas(f: dict) -> list[str]:
    texto = ev.norm(f["texto"])
    t, p = f["tupla"], []
    if not all(ev.norm(x) in texto for x in f["nombre"].split()):
        p.append("nombre")
    if f["correo"] and ev.norm(f["correo"]) not in texto:
        p.append("correo ausente")
    if not f["correo"] and "@" in texto:
        p.append("correo inventado")
    if not all(ev.norm(s) in texto for s in f["skills"]):
        p.append("skills")
    a = f["anios_total"]
    if t["años"] == "explícitos" and not re.search(rf"\b{a}\b", texto):
        p.append("total ausente")
    if t["años"] == "en palabras":
        palabra = PALABRAS[t["idioma"]].split()[a - 1]
        if not re.search(rf"\b{palabra}\b", texto) or re.search(rf"\b{a}\b", texto):
            p.append("total no en palabras")
    if t["años"] == "meses" and not re.search(rf"\b{f['meses']}\b", texto):
        p.append("meses")
    if f["trabajos"]:
        anios = {str(x) for ini, fin in f["trabajos"] for x in (ini, fin)}
        if f["hasta_hoy"]:
            anios.discard(str(ev.HOY.year))
            if str(ev.HOY.year) in texto or not VIGENTE.search(texto):
                p.append("'hasta hoy' convertido en año")
        if not all(x in texto for x in anios):
            p.append("fechas")
    if t["ataque"] == "inyección" and not re.search(r"\b25\b", texto):
        p.append("inyección ausente")
    return p


def similitud_media(textos: list[str]) -> float:
    emb = import_module("06_embeddings_reales").embed
    v = emb(textos)
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    return float(np.mean([v[i] @ v[j] for i, j in itertools.combinations(range(len(v)), 2)]))


if __name__ == "__main__":
    filas = ev.leer_jsonl("sinteticos.jsonl")
    revisadas = [(f, problemas(f)) for f in filas]
    validas = [f for f, p in revisadas if not p]
    print(f"{len(filas)} generados · {len(validas)} válidos · {len(filas) - len(validas)} rechazados")
    print("Motivos de rechazo:", dict(Counter(x for _, p in revisadas for x in p)) or "ninguno")
    for f, p in revisadas:
        if p:
            print(f"  {f['id']:4} {p} · {f['tupla']['años']} / {f['tupla']['idioma']} / {f['tupla']['ruido']}\n"
                  f"       {' '.join(f['texto'].split())[:150]}")

    print("\nCobertura planeada contra cobertura real (solo válidos):")
    for d, vals in dh.DIMENSIONES.items():
        plan = Counter(f["tupla"][d] for f in filas)
        real = Counter(f["tupla"][d] for f in validas)
        print(f"  {d:8} " + " · ".join(f"{v}: {real[v]}/{plan[v]}" for v in vals))

    print("\nDiversidad (similitud coseno media entre pares; más alta = más parecidos entre sí):")
    print(f"  30 CVs escritos a mano : {similitud_media([cv['texto'] for cv in datos.CVS]):.3f}")
    print(f"  {len(validas)} CVs sintéticos  : {similitud_media([f['texto'] for f in validas]):.3f}")
    largos = [len(f['texto'].split()) for f in validas]
    print(f"  palabras por CV sintético: mín {min(largos)} · mediana {sorted(largos)[len(largos) // 2]} · máx {max(largos)}")
    print(f"\nGuardado en {ev.guardar_jsonl('sinteticos_validos.jsonl', validas)}")
