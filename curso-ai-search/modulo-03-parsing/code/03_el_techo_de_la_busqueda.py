"""
03 · El techo: con cada forma de parsear, se extraen las fichas y se busca. ¿Cuánto se pierde? (manual §6-§7)

Para cada pipeline del laboratorio 02 y para el texto de REFERENCIA (la ingesta perfecta):
  1. se extrae la ficha de los 119 textos (el mismo extractor del Módulo 2; con caché);
  2. se mide la ficha contra los hechos, por formato de documento;
  3. se construye el índice con esos textos y esas fichas, y se mide la búsqueda "suaves" del Módulo 2.
El parser de consultas es el mismo y está en caché: la única diferencia entre filas es la ingesta.
Requiere salida/parseos.json (laboratorio 02).
"""
from __future__ import annotations
import json
import pathlib
import sys
from importlib import import_module
from statistics import mean

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
tp = import_module("02_tres_formas_de_parsear")
dd, ac, ev = tp.dd, tp.ac, tp.ev
bs = import_module("as_buscador")
fx = import_module("as_fichas")
en = import_module("as_entender")
q = import_module("as_consultas")

CAMPOS = ["rol", "anios", "ciudad", "remoto", "ingles", "skills"]


def ficha_ok(f: dict, h: dict) -> dict[str, bool]:
    return {"rol": f["rol"] == h["rol"], "anios": f["anios"] == h["anios"],
            "ciudad": ev.norm(f["ciudad"] or "") == ev.norm(h["ciudad"]), "remoto": f["remoto"] == h["remoto"],
            "ingles": f["ingles"] == h["ingles"],
            "skills": all(any(ev.norm(s) in ev.norm(x) for x in f["skills"]) for s in h["skills"])}


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    parseos = json.loads((ac.SALIDA / "parseos.json").read_text(encoding="utf-8"))
    referencia = json.loads((dd.DOCS / "referencia.json").read_text(encoding="utf-8"))
    corpus = {"referencia": {i: r["texto"] for i, r in referencia.items()}, **parseos}
    hechos = {cv["id"]: cv["hechos"] for cv in ac.cvs()}
    rels = q.relevancias(ac.cvs())
    with ev.tz.nueva_traza("el techo de la búsqueda"):
        parseos_q = ev.tz.en_paralelo(lambda t: en.parsear(t), [(t,) for _, t, _ in q.CONSULTAS])
        resultados = {}
        for nombre, textos in corpus.items():
            textos = {int(i): t for i, t in textos.items()}
            fichas = dict(zip(textos, ev.tz.en_paralelo(lambda t: fx.extraer({"texto": t or "(documento vacío)"}),
                                                        [(t,) for t in textos.values()], hilos=12)))
            idx = bs.construir({i: t or "(documento vacío)" for i, t in textos.items()})
            nd = [bs.ndcg(en.buscar(texto, "suaves", p, idx=idx, fichas=fichas), rel)
                  for ((_, texto, _), rel), p in zip(zip(q.CONSULTAS, rels), parseos_q)]
            resultados[nombre] = (fichas, nd)
    print("Fichas correctas por campo, por formato del documento (aciertos / CVs):\n")
    for formato in ["texto", "dos columnas", "escaneado"]:
        ids = [i for i in hechos if dd.formato(i) == formato]
        print(f"  {formato} ({len(ids)} CVs)")
        for nombre, (fichas, _) in resultados.items():
            oks = [ficha_ok(fichas[i], hechos[i]) for i in ids]
            print(f"    {nombre:13}" + " ".join(f"{c} {sum(o[c] for o in oks):>2}" for c in CAMPOS))
    print("\nBúsqueda (estrategia 'suaves' del Módulo 2) con el índice de cada ingesta:")
    for nombre, (_, nd) in resultados.items():
        print(f"  {nombre:13} nDCG@10 {mean(nd):.2f}")
