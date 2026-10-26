"""
01 · La línea base: los tres modos del buscador, por tipo de consulta (manual §2-§4). Sin LLM.

Para cada modo (BM25, densa, híbrida) y cada tipo de consulta: nDCG@10, recall@10 y MRR medios, y la latencia
media por consulta. Guarda salida/linea_base.jsonl (una fila por consulta y modo) para los módulos siguientes.
"""
from __future__ import annotations
import pathlib
import sys
import time
from collections import defaultdict
from importlib import import_module
from statistics import mean

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
q = import_module("as_consultas")

MODOS = ["bm25", "densa", "hibrida"]

if __name__ == "__main__":
    rels = q.relevancias(ac.cvs())
    bs.indice()                                            # el índice se construye una vez, fuera de la latencia
    todas = []
    resumen = {}
    for modo in MODOS:
        t = time.time()
        filas = bs.medir(lambda texto: bs.ranking(texto, modo), q.CONSULTAS, rels)
        resumen[modo] = (time.time() - t) / len(filas) * 1000
        todas += [{**f, "modo": modo} for f in filas]
    tipos = list(dict.fromkeys(t for t, _, _ in q.CONSULTAS))
    print(f"{len(q.CONSULTAS)} consultas · {len(ac.cvs())} CVs · nDCG@10 medio por tipo\n")
    print(f"{'tipo':14}" + "".join(f"{m:>10}" for m in MODOS) + "   n")
    for tipo in tipos:
        print(f"{tipo:14}" + "".join(f"{mean(f['ndcg'] for f in todas if f['modo'] == m and f['tipo'] == tipo):>10.2f}"
                                    for m in MODOS) + f"   {sum(t == tipo for t, _, _ in q.CONSULTAS)}")
    print(f"\n{'TOTAL':14}" + "".join(f"{mean(f['ndcg'] for f in todas if f['modo'] == m):>10.2f}" for m in MODOS))
    for metrica, nombre in (("recall", "recall@10"), ("rr", "MRR")):
        print(f"{nombre:14}" + "".join(f"{mean(f[metrica] for f in todas if f['modo'] == m):>10.2f}" for m in MODOS))
    print(f"{'ms/consulta':14}" + "".join(f"{resumen[m]:>10.1f}" for m in MODOS))
    print(f"\nGuardado en {ac.guardar_jsonl('linea_base.jsonl', todas)}")
