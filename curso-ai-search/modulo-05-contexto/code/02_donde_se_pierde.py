"""
02 · Con todo el corpus en el contexto, ¿qué candidatos se pierden y dónde estaban? (manual §6)

Tres preguntas de lista, con los 119 CVs en el contexto en un orden BARAJADO distinto cada vez (5 órdenes). Para
cada candidato que debía aparecer se anota si apareció y en qué posición relativa del contexto estaba
(0 = al principio, 1 = al final). Si se pierden más los del medio, es el efecto "lost in the middle".
"""
from __future__ import annotations
import pathlib
import random
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
qc = import_module("01_que_va_al_contexto")
ac, ev = qc.ac, qc.ev

ORDENES = 5
LISTAS = [p for p in qc.PREGUNTAS if p[2] is not None and len(p[2]) >= 4]


def una(pregunta: str, esperados: set[str], semilla: int) -> list[tuple[float, bool]]:
    cvs = ac.cvs()[:]
    random.Random(semilla).shuffle(cvs)
    pos = {cv["hechos"]["nombre"]: k / (len(cvs) - 1) for k, cv in enumerate(cvs)}
    ctx = "\n".join(f"<cv>{' '.join(cv['texto'].split())}</cv>" for cv in cvs)
    r = ev.c._cliente().chat.completions.create(
        model=ev.tz.MODELO, response_model=qc.Respuesta, max_retries=2,
        messages=[{"role": "system", "content": qc.PROMPT}, {"role": "user", "content": f"Candidatos:\n{ctx}\n\nPregunta: {pregunta}"}])
    vistos = {ev.norm(n) for n in r.nombres}
    return [(pos[n], ev.norm(n) in vistos) for n in esperados]


if __name__ == "__main__":
    trabajos = [(p, nombres, s) for p, _, nombres, _ in LISTAS for s in range(ORDENES)]
    with ev.tz.nueva_traza("dónde se pierde"):
        res = ev.tz.en_paralelo(una, trabajos, hilos=6)
    puntos = [x for r in res for x in r]
    print(f"{len(LISTAS)} preguntas de lista × {ORDENES} órdenes · {len(puntos)} candidatos esperados en total\n")
    for nombre, lo, hi in (("primer tercio", 0, 1 / 3), ("tercio del medio", 1 / 3, 2 / 3), ("último tercio", 2 / 3, 1.01)):
        sel = [ok for p, ok in puntos if lo <= p < hi]
        print(f"  {nombre:17} encontrados {sum(sel):>3}/{len(sel):<3} ({sum(sel) / len(sel):.0%})")
    print(f"\nRespuestas perfectas (lista exacta): {sum(all(ok for _, ok in r) for r in res)}/{len(res)}")
