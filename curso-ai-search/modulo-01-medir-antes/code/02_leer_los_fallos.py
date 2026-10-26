"""
02 · Leer los fallos de la línea base: los 5 primeros resultados de las peores consultas (manual §5). Sin LLM.

Un nDCG bajo dice que la consulta falla; no dice por qué. Para cada tipo, la peor consulta de la búsqueda
híbrida, con sus 5 primeros CVs, la relevancia de cada uno y los hechos que lo explican.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
q = import_module("as_consultas")

if __name__ == "__main__":
    filas = [f for f in ac.leer_jsonl("linea_base.jsonl") if f["modo"] == "hibrida"]
    rels = dict(zip([t for _, t, _ in q.CONSULTAS], q.relevancias(ac.cvs())))
    hechos = {cv["id"]: cv["hechos"] for cv in ac.cvs()}
    vistos = set()
    for f in sorted(filas, key=lambda f: f["ndcg"]):
        if f["tipo"] in vistos or f["ndcg"] > 0.6:
            continue
        vistos.add(f["tipo"])
        rel = rels[f["consulta"]]
        print(f"[{f['tipo']}] «{f['consulta']}» · nDCG@10 {f['ndcg']:.2f} · relevantes (rel 2) en el corpus: "
              f"{sum(v == 2 for v in rel.values())}")
        for p, i in enumerate(f["ranking"][:5], 1):
            h = hechos[i]
            print(f"   {p}. #{i:<3} rel {rel.get(i, 0)} · {h['rol']}, {h['anios']} años ({h['nivel']}), {h['ciudad']}"
                  f"{', remoto' if h['remoto'] else ''}, inglés {h['ingles']}, skills {h['skills']}")
        print()
