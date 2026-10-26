"""
02 · De notas sueltas a una taxonomía de fallos, contada y priorizada (manual §4-§6).

Usa la revisión guardada en comun/ (las mismas 30 salidas que leyó quien escribió el curso), para
que el resultado sea reproducible. Con tus propias notas, cambia NOTAS y NOTA_A_CATEGORIA.
Muestra: casos con algún fallo, casos por categoría y por paso del pipeline, la curva de
saturación (cuántas categorías nuevas aparecen al leer más casos) y la prioridad.
"""
from __future__ import annotations
import pathlib
import sys
from collections import defaultdict
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
m2 = import_module("m2_notas")

if __name__ == "__main__":
    notas, cat, asig = m2.NOTAS, m2.CATEGORIAS, m2.NOTA_A_CATEGORIA
    n = len(notas)
    sin_asignar = [(i, j) for i, ns in notas.items() for j in range(len(ns)) if (i, j) not in asig]
    assert not sin_asignar, f"notas sin categoría: {sin_asignar}"

    con_fallo = [i for i, ns in notas.items() if ns]
    print(f"{n} casos leídos · {len(con_fallo)} con algún problema ({len(con_fallo) / n:.0%}) · "
          f"{sum(map(len, notas.values()))} notas")

    casos = defaultdict(set)
    for (i, _), c in asig.items():
        casos[c].add(i)
    print(f"\n{'categoría':32} {'paso':11} {'grav.':>5} {'casos':>6} {'% de 30':>8}  prioridad")
    filas = sorted(cat.items(), key=lambda kv: -(len(casos[kv[0]]) * kv[1][1]))
    for nombre, (paso, grav, _) in filas:
        k = len(casos[nombre])
        print(f"{nombre:32} {paso:11} {grav:>5} {k:>6} {k / n:>8.0%}  {k * grav:>5}  casos {sorted(casos[nombre])}")

    por_paso = defaultdict(set)
    for nombre, (paso, _, _) in cat.items():
        por_paso[paso] |= casos[nombre]
    print("\nCasos afectados por paso del pipeline:", {p: len(c) for p, c in por_paso.items()})

    vistas, curva = set(), []
    for i in sorted(notas):
        vistas |= {c for (k, _), c in asig.items() if k == i}
        curva.append(len(vistas))
    print("\nSaturación: categorías distintas vistas tras leer 5, 10, 15... casos:",
          [curva[k - 1] for k in range(5, n + 1, 5)])
    ultima_nueva = max(i for i in range(1, n + 1) if curva[i - 1] > (curva[i - 2] if i > 1 else 0))
    print(f"La última categoría nueva apareció en el caso #{ultima_nueva}.")
    print("\nPrioridad = casos × gravedad. Es una guía para empezar, no una fórmula: un fallo raro pero grave")
    print("(una certificación inventada) puede ir primero aunque el número diga otra cosa.")
