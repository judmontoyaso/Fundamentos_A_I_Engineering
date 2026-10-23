"""
06 · Comparar modelos en calidad, tokens y latencia, tarea por tarea (Módulo 1 §6, manual §5 y §10).

"Empieza por el modelo más capaz y baja hasta encontrar el que ya no puede", medido:
  tarea 1 · extracción (dataset de 03): exactitud por campo
  tarea 2 · juez de fidelidad (casos de 04): acuerdo con la persona y falsos aprobados
Para cada modelo: calidad, tokens de entrada/salida/razonamiento y latencia (de las trazas).
MODELOS se puede cambiar por los que tenga tu cuenta.
"""
from __future__ import annotations
import math
import pathlib
import sys
import time
from importlib import import_module
from statistics import mean

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
tz = import_module("00_trazador")
ds = import_module("03_dataset_extraccion")
jz = import_module("04_llm_juez")

MODELOS = ["gpt-6-luna", "gpt-4.1-mini", "gpt-4.1-nano"]


def uso(trace_id: str) -> dict:
    llm = [s for s in tz.spans(trace_id) if s["atributos"].get("tipo") == "llm" and "tokens_entrada" in s["atributos"]]
    seg = sorted(s["seg"] for s in llm)
    return {"entrada": sum(s["atributos"]["tokens_entrada"] for s in llm) / len(llm),
            "salida": sum(s["atributos"]["tokens_salida"] for s in llm) / len(llm),
            "razon": sum(s["atributos"]["tokens_razonamiento"] for s in llm) / max(1, sum(s["atributos"]["tokens_salida"] for s in llm)),
            "p50": seg[math.ceil(len(seg) / 2) - 1]}


def extraccion(modelo: str) -> tuple[float, dict, list[str]]:
    with tz.nueva_traza(f"comparar extracción {modelo}") as raiz:
        res = tz.en_paralelo(lambda i, caso, texto, esp: (caso, ds.puntuar(
            tz.llm_trazado(ds.cad.DatosCV, ds.PROMPT_V1, ds.c.como_cv(texto), version_prompt=modelo), esp)),
            [(i, *d) for i, d in enumerate(ds.DATASET, 1)])
    exactitud = mean(mean(r.values()) for _, r in res)
    fallos = [f"{caso} ({campo})" for caso, r in res for campo, ok in r.items() if not ok]
    return exactitud, uso(raiz.trace_id), fallos


def juez(modelo: str) -> tuple[float, int, dict]:
    with tz.nueva_traza(f"comparar juez {modelo}") as raiz:
        res = tz.en_paralelo(lambda ctx, resp, humano, _: (jz.juzgar(ctx, resp).fiel, humano), list(jz.CASOS))
    acuerdo = mean(j == h for j, h in res)
    falsos_aprobados = sum(j and not h for j, h in res)
    return acuerdo, falsos_aprobados, uso(raiz.trace_id)


if __name__ == "__main__":
    filas = []
    original = tz.MODELO
    try:
        for modelo in MODELOS:
            tz.MODELO = modelo                  # el trazador usa esta variable en cada llamada
            t = time.time()
            try:
                ex, u1, fallos = extraccion(modelo)
                ac, fa, u2 = juez(modelo)
            except Exception as e:
                print(f"{modelo}: no disponible ({type(e).__name__}: {str(e)[:80]})")
                continue
            filas.append((modelo, ex, u1, ac, fa, u2, time.time() - t))
            print(f"{modelo}: fallos de extracción -> {fallos or 'ninguno'}")
    finally:
        # En la app, el kernel comparte este módulo con las demás celdas (y con el asistente del Módulo 9):
        # sin restaurarlo, todo lo que viniera después usaría el último modelo de la lista.
        tz.MODELO = original

    print(f"\n{'modelo':14} | {'EXTRACCIÓN exactitud':>20} {'tok sal':>8} {'razon.':>7} {'p50':>6} | "
          f"{'JUEZ acuerdo':>12} {'falsos aprob.':>13} {'p50':>6}")
    for m, ex, u1, ac, fa, u2, _ in filas:
        print(f"{m:14} | {ex:20.0%} {u1['salida']:8.0f} {u1['razon']:7.0%} {u1['p50']:5.1f}s | "
              f"{ac:12.0%} {fa:13} {u2['p50']:5.1f}s")

    print("\n== Recomendación por tarea (el más barato de la lista que no pierde calidad frente al mejor) ==")
    orden = {m: i for i, m in enumerate(MODELOS)}    # MODELOS va del más capaz al más barato
    mejor_ex = max(f[1] for f in filas)
    elegido_ex = max((f for f in filas if f[1] >= mejor_ex), key=lambda f: orden[f[0]])[0]
    seguros = [f for f in filas if f[4] == 0]
    mejor_j = max((f[3] for f in seguros), default=0)
    elegido_j = max((f for f in seguros if f[3] >= mejor_j), key=lambda f: orden[f[0]], default=None)
    print(f"  Extracción : {elegido_ex}")
    print(f"  Juez       : {elegido_j[0] if elegido_j else 'ninguno sin falsos aprobados'}  "
          "(en un juez, los falsos aprobados descalifican)")
    print("\nCon 10 casos por tarea, una diferencia de un caso es 10 puntos: repite antes de cambiar de modelo,")
    print("y fija la versión exacta del modelo elegido (los alias cambian sin aviso).")
