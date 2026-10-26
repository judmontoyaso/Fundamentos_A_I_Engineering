"""
01 · Entender la consulta: reescribir, filtrar duro o filtrar suave, por tipo de consulta (manual §2-§5).

El parser (LLM) convierte cada consulta en filtros y una reformulación. Se comparan cuatro estrategias contra
la línea base del Módulo 1, por tipo, y la mejor contra la base consulta a consulta (bootstrap pareado).
El parser se cachea: la segunda corrida no vuelve a pagarlo (y por eso no mide su variación; ver ejercicios).
"""
from __future__ import annotations
import pathlib
import random
import sys
from importlib import import_module
from statistics import mean

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
q = import_module("as_consultas")
en = import_module("as_entender")
ev = ac.ev

ESTRATEGIAS = ["base", "reescrita", "duros", "suaves"]


def bootstrap(a, b, B=5000, rnd=random.Random(1)):
    d = [y - x for x, y in zip(a, b)]
    s = sorted(mean(rnd.choice(d) for _ in d) for _ in range(B))
    return mean(d), s[int(0.025 * B)], s[int(0.975 * B) - 1]


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    rels = q.relevancias(ac.cvs())
    with ev.tz.nueva_traza("entender consultas"):
        parseos = ev.tz.en_paralelo(lambda t: en.parsear(t), [(t,) for _, t, _ in q.CONSULTAS])
    res = {e: [] for e in ESTRATEGIAS}
    for ((tipo, texto, _), rel), p in zip(zip(q.CONSULTAS, rels), parseos):
        for e in ESTRATEGIAS:
            res[e].append({"tipo": tipo, "consulta": texto, "ndcg": bs.ndcg(en.buscar(texto, e, p), rel)})
    tipos = list(dict.fromkeys(t for t, _, _ in q.CONSULTAS))
    print(f"nDCG@10 por tipo ({len(q.CONSULTAS)} consultas)\n")
    print(f"{'tipo':14}" + "".join(f"{e:>11}" for e in ESTRATEGIAS))
    for t in tipos:
        print(f"{t:14}" + "".join(f"{mean(f['ndcg'] for f in res[e] if f['tipo'] == t):>11.2f}" for e in ESTRATEGIAS))
    print(f"{'TOTAL':14}" + "".join(f"{mean(f['ndcg'] for f in res[e]):>11.2f}" for e in ESTRATEGIAS))
    print()
    base = [f["ndcg"] for f in res["base"]]
    for e in ESTRATEGIAS[1:]:
        x = [f["ndcg"] for f in res[e]]
        m, lo, hi = bootstrap(base, x)
        print(f"  {e:9} contra base: gana {sum(b > a + 1e-9 for a, b in zip(base, x))}, pierde "
              f"{sum(b < a - 1e-9 for a, b in zip(base, x))} · diferencia {m:+.3f} IC95 [{lo:+.3f}, {hi:+.3f}]")
    print("\nCómo entendió el parser algunas consultas:")
    for (_, texto, _), p in zip(q.CONSULTAS, parseos):
        if texto in ("k8s", "desarrollador backend que no use Java", "senior data engineer", "recién egresado de desarrollo",
                     "alguien que automatice despliegues y administre contenedores", "desarrollador backend en Medellín"):
            print(f"  «{texto}» -> {p.model_dump(exclude_defaults=True)}")
    ac.guardar_jsonl("m2_estrategias.jsonl", [{**f, "estrategia": e} for e in ESTRATEGIAS for f in res[e]])
