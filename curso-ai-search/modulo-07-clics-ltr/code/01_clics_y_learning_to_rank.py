"""
01 · Simular clics con sesgo de posición, aprender a ordenar de ellos, y no aprender el sesgo (manual §2-§6).

1. PRODUCCIÓN: el buscador que los reclutadores usan hoy es la híbrida base (Módulo 1). Muestra 10 resultados.
2. CLICS (modelo basado en la posición): el reclutador MIRA el resultado k con probabilidad θ_k (mucho arriba, poco
   abajo) y, si lo mira, hace clic según la relevancia (2 -> 0.8, 1 -> 0.35, 0 -> 0.08). Así son los logs reales:
   un clic dice "lo vio y le gustó", y lo de abajo casi nunca se ve.
3. LEARNING TO RANK: un modelo lineal sobre features (BM25, densa, MaxSim, posición en producción y los filtros del
   parser) aprende a puntuar pares (consulta, CV) a partir de:
     ingenuo : la tasa de clics de cada par (aprende también el sesgo de posición)
     IPS     : cada clic pesado por 1/θ_k (corrige que lo de abajo se mire poco)
     oráculo : la relevancia verdadera (el techo de estas features)
4. Se evalúa en consultas que NO estaban en los logs, con la relevancia verdadera, y contra un oráculo entrenado
   con TODOS los CVs (no solo los mostrados): la distancia entre los dos oráculos es el sesgo de selección.
"""
from __future__ import annotations
import pathlib
import random
import sys
from collections import defaultdict
from importlib import import_module
from statistics import mean

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
en = import_module("as_entender")
fx = import_module("as_fichas")
q = import_module("as_consultas")
sys.path.append(str(ac.CURSO / "modulo-04-retrieval" / "code"))
li = import_module("02_late_interaction")
ev = ac.ev

THETA = [0.95 / (k ** 0.9) for k in range(1, 11)]          # probabilidad de mirar el resultado en la posición k
ATRACCION = {2: 0.8, 1: 0.35, 0: 0.08}
SESIONES = 60                                              # sesiones por consulta de entrenamiento
FEATURES = ["bm25", "densa", "maxsim", "1/posicion_produccion", "frac_requisitos", "rol_coincide"]


def produccion(texto: str) -> list[int]:
    """Lo que ve el reclutador hoy: el top 10 de la híbrida del Módulo 1 (fusión de las dos listas completas)."""
    return bs.ranking(texto, "hibrida", 119)[:10]


def features_de(texto: str, p, cvs, docs_tok, fichas) -> dict[int, list[float]]:
    ids, densos, lexico = bs.indice()
    qv = ac.embed([texto])[0]
    dens = dict(zip(ids, densos @ (qv / np.linalg.norm(qv))))
    b = dict((ids[i], s) for i, s in lexico.buscar(texto, 119))
    bmax = max(b.values(), default=1) or 1
    qt = li.tokens([texto])[0][1:-1]
    ms = {i: float((qt @ d.T).max(axis=1).sum()) / max(len(qt), 1) for i, d in zip(ids, docs_tok)}
    prod = {i: k for k, i in enumerate(bs.ranking(texto, "hibrida", 119), 1)}
    out = {}
    for i in ids:
        req = en.requisitos(fichas[i], p)
        out[i] = [b.get(i, 0) / bmax, float(dens[i]), ms[i], 1 / prod.get(i, 120),
                  (sum(req) / len(req)) if req else 0.0, float(bool(p.roles) and fichas[i]["rol"] in p.roles)]
    return out


def simular(ranking: list[int], rel: dict[int, int], rnd: random.Random) -> list[tuple[int, int, int]]:
    """Una sesión: (cv, posición, clic) para los 10 mostrados."""
    return [(i, k, int(rnd.random() < THETA[k - 1] and rnd.random() < ATRACCION[rel.get(i, 0)]))
            for k, i in enumerate(ranking[:10], 1)]


def correr(semilla: int, cvs, rels, fichas, feats, parseos, mostrar: bool = False,
           propension: list[float] | None = None, semilla_clics: int | None = None) -> dict[str, float]:
    """Una partición entreno/prueba: simula logs, entrena los modelos y mide nDCG@10 en prueba.
    propension: la θ que usa IPS para corregir (por defecto la verdadera; el lab 02 la estima).
    semilla_clics: para cambiar los clics sin cambiar la partición (por defecto, la misma semilla)."""
    propension = propension or THETA
    rnd = random.Random(semilla)
    indices = list(range(len(q.CONSULTAS)))
    rnd.shuffle(indices)
    if semilla_clics is not None:
        rnd = random.Random(semilla_clics)
    entreno, prueba = sorted(indices[:26]), sorted(indices[26:])
    impresiones = defaultdict(lambda: [0, 0, 0.0])          # (consulta, cv) -> [mostrado, clics, clics/θ]
    clics_por_pos = defaultdict(lambda: [0, 0])
    for k in entreno:
        mostrado = produccion(q.CONSULTAS[k][1])
        for _ in range(SESIONES):
            for i, pos, c in simular(mostrado, rels[k], rnd):
                d = impresiones[(k, i)]
                d[0] += 1
                d[1] += c
                d[2] += c / propension[pos - 1]
                clics_por_pos[pos][0] += 1
                clics_por_pos[pos][1] += c
    X = np.array([feats[k][i] for (k, i) in impresiones])
    objetivos = {"ingenuo": np.array([v[1] / v[0] for v in impresiones.values()]),
                 "IPS": np.array([v[2] / v[0] for v in impresiones.values()]),
                 "oráculo": np.array([rels[k].get(i, 0) for (k, i) in impresiones])}
    escala = StandardScaler().fit(X)
    modelos = {n: Ridge(alpha=1.0).fit(escala.transform(X), y) for n, y in objetivos.items()}
    # Fuera del alcance de cualquier log: la relevancia de TODOS los CVs de las consultas de entreno, no solo de los
    # 10 que producción mostró. Separa lo que cuesta el sesgo de posición de lo que cuesta el de SELECCIÓN.
    todos = [(k, i) for k in entreno for i in feats[k]]
    modelos["oráculo (todos)"] = Ridge(alpha=1.0).fit(escala.transform(np.array([feats[k][i] for k, i in todos])),
                                                      np.array([rels[k].get(i, 0) for k, i in todos]))
    if mostrar:
        print(f"Logs (partición {semilla}): {len(entreno)} consultas × {SESIONES} sesiones · "
              f"{sum(v[1] for v in impresiones.values())} clics")
        print("Tasa de clic por posición: " + " ".join(f"{p}:{v[1] / v[0]:.0%}" for p, v in sorted(clics_por_pos.items())))
        print(f"\nPesos aprendidos (features estandarizadas):\n{'':24}" + "".join(f"{n:>17}" for n in modelos))
        for j, f in enumerate(FEATURES):
            print(f"{f:24}" + "".join(f"{m.coef_[j]:>17.3f}" for m in modelos.values()))

    def ranking_ltr(k, modelo):
        ids = list(feats[k])
        s = modelo.predict(escala.transform(np.array([feats[k][i] for i in ids])))
        return [ids[j] for j in np.argsort(-s)]

    res = {"producción (híbrida)": [], "filtros suaves (Módulo 2)": []} | {f"LTR {n}": [] for n in modelos}
    for k in prueba:
        texto, rel = q.CONSULTAS[k][1], rels[k]
        res["producción (híbrida)"].append(bs.ndcg(bs.ranking(texto, "hibrida", 119), rel))
        res["filtros suaves (Módulo 2)"].append(bs.ndcg(en.buscar(texto, "suaves", parseos[k]), rel))
        for n, m in modelos.items():
            res[f"LTR {n}"].append(bs.ndcg(ranking_ltr(k, m), rel))
    return {n: mean(v) for n, v in res.items()}


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    cvs = ac.cvs()
    rels = q.relevancias(cvs)
    fichas = fx.fichas()
    docs_tok = li.tokens([cv["texto"] for cv in cvs])
    parseos = ev.tz.en_paralelo(lambda t: en.parsear(t), [(t,) for _, t, _ in q.CONSULTAS])
    feats = {k: features_de(t, parseos[k], cvs, docs_tok, fichas) for k, (_, t, _) in enumerate(q.CONSULTAS)}
    PARTICIONES = 10
    tabla = [correr(s, cvs, rels, fichas, feats, parseos, mostrar=(s == 0)) for s in range(PARTICIONES)]
    print(f"\nnDCG@10 en las 15 consultas que NO estaban en los logs, {PARTICIONES} particiones distintas:")
    for n in tabla[0]:
        v = [t[n] for t in tabla]
        print(f"  {n:28} media {mean(v):.2f}  (de {min(v):.2f} a {max(v):.2f})")
    ips_gana = sum(t["LTR IPS"] > t["LTR ingenuo"] for t in tabla)
    print(f"\nIPS supera al ingenuo en {ips_gana} de {PARTICIONES} particiones.")
