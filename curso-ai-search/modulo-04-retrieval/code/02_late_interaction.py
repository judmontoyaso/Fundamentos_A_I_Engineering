"""
02 · Late interaction (la idea de ColBERT): comparar token a token en vez de un vector por documento (manual §4).

La búsqueda densa resume cada CV en UN vector (el promedio de sus tokens): un CV con diez tecnologías queda en
el "centro" de todas. Late interaction guarda el vector de CADA token y puntúa con MaxSim: para cada token de la
consulta, el token más parecido del CV; la nota es la suma. Aquí con el mismo MiniLM (sus embeddings por token),
sin entrenar ni descargar nada: no es ColBERT (que se entrena para esto), es su idea medida en nuestro corpus.
Sin LLM. Compara: densa, MaxSim, y la híbrida con cada una.
"""
from __future__ import annotations
import os
import pathlib
import sys
import time
from importlib import import_module
from statistics import mean

import numpy as np

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
q = import_module("as_consultas")
emb = import_module("06_embeddings_reales")


def tokens(textos: list[str]) -> list[np.ndarray]:
    m = emb._modelo_local(os.getenv("EMB_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"))
    out = m.encode(textos, output_value="token_embeddings")
    return [(t / np.linalg.norm(t, axis=1, keepdims=True)).astype(np.float32) for t in (x.cpu().numpy() for x in out)]


def maxsim_ranking(consulta: str, ids: list[int], docs: list[np.ndarray]) -> list[int]:
    qv = tokens([consulta])[0][1:-1]                     # sin los tokens especiales de inicio y fin
    puntos = [float((qv @ d.T).max(axis=1).sum()) for d in docs]
    return [ids[i] for i in np.argsort(-np.array(puntos))]


def rrf(*rankings: list[int]) -> list[int]:
    p: dict[int, float] = {}
    for r in rankings:
        for puesto, i in enumerate(r, 1):
            p[i] = p.get(i, 0.0) + 1 / (60 + puesto)
    return sorted(p, key=lambda i: -p[i])


if __name__ == "__main__":
    cvs = ac.cvs()
    ids = [cv["id"] for cv in cvs]
    t = time.time()
    docs = tokens([cv["texto"] for cv in cvs])
    print(f"Embeddings por token de {len(docs)} CVs en {time.time() - t:.1f} s · "
          f"{sum(len(d) for d in docs)} vectores (contra {len(docs)} de la densa)\n")
    rels = q.relevancias(cvs)
    filas = {k: [] for k in ("densa", "maxsim", "híbrida (densa)", "híbrida (maxsim)")}
    for (tipo, texto, _), rel in zip(q.CONSULTAS, rels):
        d = bs.ranking(texto, "densa", 119)
        m = maxsim_ranking(texto, ids, docs)
        b = bs.ranking(texto, "bm25", 119)
        for k, r in (("densa", d), ("maxsim", m), ("híbrida (densa)", rrf(d[:50], b[:50])), ("híbrida (maxsim)", rrf(m[:50], b[:50]))):
            filas[k].append((tipo, bs.ndcg(r, rel)))
    tipos = list(dict.fromkeys(t for t, _, _ in q.CONSULTAS))
    print(f"{'tipo':14}" + "".join(f"{k:>18}" for k in filas))
    for tp in tipos:
        print(f"{tp:14}" + "".join(f"{mean(v for tt, v in filas[k] if tt == tp):>18.2f}" for k in filas))
    print(f"{'TOTAL':14}" + "".join(f"{mean(v for _, v in filas[k]):>18.2f}" for k in filas))

    # ¿Y con el parser del Módulo 2 encima? Filtros suaves sobre la híbrida contra filtros suaves sobre MaxSim.
    en = import_module("as_entender")
    fx = import_module("as_fichas")
    ac.ev.CACHE["activa"] = True
    fichas = fx.fichas()
    nd_h, nd_m = [], []
    for (_, texto, _), rel in zip(q.CONSULTAS, rels):
        p = en.parsear(texto)
        nd_h.append(bs.ndcg(en.buscar(texto, "suaves", p), rel))
        orden = maxsim_ranking(p.texto_busqueda, ids, docs)
        nd_m.append(bs.ndcg(sorted(orden, key=lambda i: -sum(en.requisitos(fichas[i], p))), rel))
    d = [b - a for a, b in zip(nd_h, nd_m)]
    print(f"\nCon el parser: suaves sobre la híbrida {mean(nd_h):.2f} · suaves sobre MaxSim {mean(nd_m):.2f} · "
          f"gana {sum(x > 1e-9 for x in d)}, pierde {sum(x < -1e-9 for x in d)}")
    t = time.time()
    for _ in range(20):
        maxsim_ranking("ingeniero de datos senior", ids, docs)
    print(f"MaxSim: {(time.time() - t) / 20 * 1000:.0f} ms por consulta sobre {len(ids)} CVs")
