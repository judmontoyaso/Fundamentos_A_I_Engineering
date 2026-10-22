"""
05 · Medir: BM25 vs. semántica vs. híbrida sobre un set etiquetado (manual §12).

Reutiliza la colección de 04 y las métricas del Módulo 2. Imprime la tabla
global y el desglose por consulta, para ver DÓNDE gana y pierde cada modo.

    Sin Docker: QDRANT_URL=:memory:
"""
from __future__ import annotations
import sys
import pathlib
from importlib import import_module
from statistics import mean

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.append(str(AQUI))
sys.path.append(str(AQUI.parents[1] / "modulo-02-embeddings-busqueda-semantica" / "code"))
hib = import_module("04_hibrida_qdrant")
met = import_module("11_eval_retrieval")

K = 3
# (consulta, ids relevantes, tipo). Etiquetado a mano sobre el CORPUS de 04.
SET = [
    ("ISO 27001", {4}, "exacta"),
    ("C#", {8}, "exacta"),
    ("Node.js", {2}, "exacta"),
    ("Terraform", {6}, "exacta"),
    ("AWS", {1, 6}, "exacta"),
    ("experiencia con streaming", {1}, "parafrasis"),
    ("especialista en aprendizaje automático", {7}, "parafrasis"),
    ("responsable de la hoja de ruta de un producto digital", {3}, "parafrasis"),
    ("certificaciones de seguridad informática", {4}, "mixta"),
    ("nube de Amazon con infraestructura automatizada", {6}, "mixta"),
    ("auditorías de calidad en fábricas", {5}, "mixta"),
]
MODOS = ("bm25", "semantica", "hibrida")

if __name__ == "__main__":
    client = hib.construir()
    filas = {m: {"recall": [], "rr": []} for m in MODOS}
    por_tipo = {m: {} for m in MODOS}

    print(f"{'consulta':52} {'tipo':10} " + " ".join(f"{m:>9}" for m in MODOS))
    for consulta, relevantes, tipo in SET:
        celdas = []
        for m in MODOS:
            ids = [h.id for h in hib.buscar(client, consulta, modo=m, k=K)]
            r = met.recall_at_k(ids, relevantes, K)
            filas[m]["recall"].append(r)
            filas[m]["rr"].append(met.reciprocal_rank(ids, relevantes))
            por_tipo[m].setdefault(tipo, []).append(r)
            celdas.append(f"{r:9.2f}")
        print(f"{consulta[:52]:52} {tipo:10} " + " ".join(celdas))

    print(f"\n{'':63}" + " ".join(f"{m:>9}" for m in MODOS))
    print(f"{'recall@' + str(K) + ' medio':63}" + " ".join(f"{mean(filas[m]['recall']):9.2f}" for m in MODOS))
    print(f"{'MRR':63}" + " ".join(f"{mean(filas[m]['rr']):9.2f}" for m in MODOS))
    for tipo in ("exacta", "parafrasis", "mixta"):
        print(f"{'recall@' + str(K) + ' en consultas ' + tipo:63}"
              + " ".join(f"{mean(por_tipo[m][tipo]):9.2f}" for m in MODOS))

    print("\nCómo leerlo: la híbrida no debería ser peor que la mejor de las dos en el total,")
    print("y cada modo gana en su tipo de consulta. Mira también las filas donde la híbrida")
    print("pierde: suelen apuntar al modelo de embeddings o al tokenizador (manual §12).")
