"""
02 · IPS necesita θ, y en producción nadie te la da: estimarla intercambiando resultados (manual §5-§6).

1. INTERVENCIÓN: en algunas sesiones se intercambian el resultado 1 y el k. Con tantas sesiones normales como
   intercambiadas, los dos documentos pasan el mismo tiempo en cada posición, así que
       clics en k / clics en 1  =  θ_k / θ_1
   sin saber nada de la relevancia. IPS solo necesita la θ relativa (escalarla no cambia el ranking aprendido).
2. EL COSTO: durante el intercambio el reclutador ve una lista peor. Se mide cuánto.
3. IPS con distintas θ: la verdadera, la estimada, una plana (= el modelo ingenuo) y una equivocada (1/k).
4. LO QUE NINGÚN CLIC ARREGLA: los CVs relevantes que producción nunca mostró en el top 10.
"""
from __future__ import annotations
import pathlib
import random
import sys
from importlib import import_module
from statistics import mean

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
lt = import_module("01_clics_y_learning_to_rank")
ac, bs, en, fx, q, li, ev = lt.ac, lt.bs, lt.en, lt.fx, lt.q, lt.li, lt.ev

SESIONES_POR_PAR = 40                  # por consulta y por posición k: 40 normales + 40 intercambiadas


def estimar_theta(rels, rnd: random.Random) -> list[float]:
    clics = {k: [0, 0] for k in range(2, 11)}               # k -> [clics en la posición 1, clics en la posición k]
    for k_c, (_, texto, _) in enumerate(q.CONSULTAS):
        prod = lt.produccion(texto)
        for k in range(2, 11):
            cambiado = prod.copy()
            cambiado[0], cambiado[k - 1] = prod[k - 1], prod[0]
            for lista in (prod, cambiado):
                for _ in range(SESIONES_POR_PAR):
                    sesion = lt.simular(lista, rels[k_c], rnd)
                    clics[k][0] += sesion[0][2]
                    clics[k][1] += sesion[k - 1][2]
    return [1.0] + [clics[k][1] / max(clics[k][0], 1) for k in range(2, 11)]


def costo_de_intervenir(rels) -> tuple[float, float]:
    """nDCG@10 medio de lo que ve el reclutador: producción contra las listas con el 1 intercambiado."""
    normal, cambiada = [], []
    for k_c, (_, texto, _) in enumerate(q.CONSULTAS):
        prod = lt.produccion(texto)
        normal.append(bs.ndcg(prod, rels[k_c]))
        for k in range(2, 11):
            c = prod.copy()
            c[0], c[k - 1] = prod[k - 1], prod[0]
            cambiada.append(bs.ndcg(c, rels[k_c]))
    return mean(normal), mean(cambiada)


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    cvs = ac.cvs()
    rels = q.relevancias(cvs)
    fichas = fx.fichas()
    rnd = random.Random(7)

    theta_est = estimar_theta(rels, rnd)
    rel1 = lt.THETA[0]
    print(f"θ relativa a la posición 1 ({len(q.CONSULTAS)} consultas × 9 intercambios × {2 * SESIONES_POR_PAR} sesiones):")
    print(f"  {'posición':10}" + "".join(f"{k:>6}" for k in range(1, 11)))
    print(f"  {'verdadera':10}" + "".join(f"{t / rel1:>6.2f}" for t in lt.THETA))
    print(f"  {'estimada':10}" + "".join(f"{t:>6.2f}" for t in theta_est))

    normal, cambiada = costo_de_intervenir(rels)
    print(f"\nLo que ve el reclutador (nDCG@10): producción {normal:.2f} · con el intercambio {cambiada:.2f}")
    print("  (si se intercambia en el 5% de las sesiones, el costo medio es "
          f"{0.05 * (normal - cambiada):.3f} de nDCG)")

    docs_tok = li.tokens([cv["texto"] for cv in cvs])
    parseos = ev.tz.en_paralelo(lambda t: en.parsear(t), [(t,) for _, t, _ in q.CONSULTAS])
    feats = {k: lt.features_de(t, parseos[k], cvs, docs_tok, fichas) for k, (_, t, _) in enumerate(q.CONSULTAS)}
    variantes = {"θ verdadera": lt.THETA, "θ estimada": theta_est,
                 "θ plana (sin corregir)": [1.0] * 10, "θ equivocada (1/k)": [1 / k for k in range(1, 11)]}
    PARTICIONES = 10
    print(f"\nLTR IPS según la θ que usa, nDCG@10 en prueba ({PARTICIONES} particiones):")
    for nombre, theta in variantes.items():
        v = [lt.correr(s, cvs, rels, fichas, feats, parseos, propension=theta)["LTR IPS"] for s in range(PARTICIONES)]
        print(f"  {nombre:24} {mean(v):.3f}")

    nunca = [(k, i) for k, (_, t, _) in enumerate(q.CONSULTAS)
             for i, r in rels[k].items() if r == 2 and i not in lt.produccion(t)]
    total = sum(r == 2 for rel in rels for r in rel.values())
    print(f"\nCVs muy relevantes que producción nunca muestra en el top 10: {len(nunca)} de {total} "
          f"({len(nunca) / total:.0%}). Ningún clic habla de ellos.")
