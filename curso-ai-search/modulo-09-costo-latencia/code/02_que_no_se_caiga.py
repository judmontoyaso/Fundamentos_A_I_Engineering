"""
02 · Que no se caiga: tiempos límite, reintentos, respaldo y cortacircuitos, medidos (manual §5-§7).

1. LO QUE DICEN TUS TRAZAS: cuántas llamadas al LLM fallaron de verdad en este proyecto, y por qué.
2. UNA CAÍDA SIMULADA (sin llamadas al LLM): 1.000 pedidos, uno por segundo. El parser de consultas (modelo principal)
   tarda lo que tardó en tus trazas, falla el 2% de las veces y, entre los pedidos 400 y 600, el proveedor está caído:
   cada intento se cuelga hasta el tiempo límite. Cinco estrategias:
     ingenua            : los valores por defecto del SDK (600 s de límite, 2 reintentos) y sin respaldo
     límite + reintento : 5 s de límite, 2 reintentos con espera exponencial, sin respaldo
     límite + respaldo  : 5 s de límite, 1 intento; si falla, búsqueda híbrida sin entender la consulta
     presupuesto 3 s    : igual, pero el parser tiene 3 s en total (corta también las respuestas lentas)
     + cortacircuitos   : tras 5 fallos seguidos deja de llamar al parser 30 s, y luego prueba con un pedido
   Se mide: disponibilidad, nDCG@10 (con el del parser cuando responde y el de la híbrida cuando no), latencia y
   llamadas al LLM.
"""
from __future__ import annotations
import pathlib
import random
import sys
from collections import Counter
from importlib import import_module
from statistics import mean, quantiles

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
en = import_module("as_entender")
q = import_module("as_consultas")
ev = ac.ev

PEDIDOS, CAIDA, FALLA_FONDO = 1000, range(400, 600), 0.02


def estrategia(nombre: str) -> dict:
    base = {"limite": 5.0, "intentos": 1, "respaldo": True, "presupuesto": None, "cortacircuitos": False}
    return base | {
        "ingenua": {"limite": 600.0, "intentos": 3, "respaldo": False},
        "límite + reintento": {"intentos": 3, "respaldo": False},
        "límite + respaldo": {},
        "presupuesto 3 s": {"presupuesto": 3.0},
        "+ cortacircuitos": {"presupuesto": 3.0, "cortacircuitos": True},
    }[nombre]


def simular(nombre: str, latencias: list[float], ndcg_parser: list[float], ndcg_base: list[float],
            semilla: int = 0) -> dict:
    e, rnd = estrategia(nombre), random.Random(semilla)
    fallos_seguidos, abierto_hasta = 0, -1.0
    res = {"respondidos": 0, "ndcg": [], "seg": [], "llamadas": 0}
    for t in range(PEDIDOS):
        k = rnd.randrange(len(ndcg_parser))
        seg, entendida = 0.0, False
        if e["cortacircuitos"] and t < abierto_hasta:
            pass                                                   # circuito abierto: ni se intenta
        else:
            for intento in range(e["intentos"]):
                res["llamadas"] += 1
                cae = t in CAIDA or rnd.random() < FALLA_FONDO
                dura = e["limite"] if cae else rnd.choice(latencias)
                if not cae and dura > e["limite"]:
                    cae, dura = True, e["limite"]
                if e["presupuesto"] is not None and seg + dura > e["presupuesto"]:
                    seg, cae = e["presupuesto"], True              # se acabó el presupuesto: se corta y se sigue
                    break
                seg += dura
                if not cae:
                    entendida = True
                    break
                if intento < e["intentos"] - 1:
                    seg += 0.5 * 2 ** intento                      # espera exponencial antes de reintentar
            if e["cortacircuitos"]:
                fallos_seguidos = 0 if entendida else fallos_seguidos + 1
                if fallos_seguidos >= 5:
                    abierto_hasta, fallos_seguidos = t + 30, 4     # tras 30 s, un pedido de prueba
        if entendida or e["respaldo"]:
            res["respondidos"] += 1
            res["ndcg"].append(ndcg_parser[k] if entendida else ndcg_base[k])
        else:
            res["ndcg"].append(0.0)                                # un error no muestra nada
        res["seg"].append(seg + 0.05)                              # + la búsqueda local
    return res


if __name__ == "__main__":
    print("1. Lo que dicen tus trazas")
    llm = [s for s in ev.tz.spans() if s["atributos"].get("tipo") == "llm"]
    errores = Counter((s["error"] or "").split(":")[0] + ": " + (s["error"] or "").split(":", 1)[-1].strip()[:55]
                      for s in llm if s["estado"] == "error")
    print(f"   {len(llm)} llamadas al LLM, {sum(errores.values())} con error ({sum(errores.values()) / max(len(llm), 1):.2%})")
    for err, n in errores.most_common(5):
        print(f"   {n:>5} × {err}")
    latencias = {}
    for m in (ev.tz.MODELO, ev.MODELO_BARATO):
        latencias[m] = [s["seg"] for s in llm if s["nombre"] == "entender consulta" and s["estado"] == "ok"
                        and s["atributos"].get("modelo_pedido") == m]
        c = quantiles(latencias[m], n=20, method="inclusive")
        print(f"   Parser con {m}: {len(latencias[m])} llamadas · p50 {c[9]:.1f} s · p95 {c[18]:.1f} s · "
              f"máx {max(latencias[m]):.1f} s")

    ev.CACHE["activa"] = True
    rels = q.relevancias(ac.cvs())
    ndcg_parser = {m: [bs.ndcg(en.buscar(t, "suaves", en.parsear(t, m)), r) for (_, t, _), r in zip(q.CONSULTAS, rels)]
                   for m in latencias}
    ndcg_base = [bs.ndcg(bs.ranking(t, "hibrida", 119), r) for (_, t, _), r in zip(q.CONSULTAS, rels)]

    print(f"\n2. Una caída simulada: {PEDIDOS} pedidos, el proveedor caído en los pedidos {CAIDA.start}-{CAIDA.stop}, "
          f"{FALLA_FONDO:.0%} de fallos sueltos")
    print(f"   {'':34} {'disponible':>10} {'nDCG@10':>8} {'p50 s':>7} {'p95 s':>7} {'peor s':>8} {'llamadas':>9}")
    filas = [(n, ev.tz.MODELO) for n in ("ingenua", "límite + reintento", "límite + respaldo", "presupuesto 3 s",
                                         "+ cortacircuitos")]
    filas += [(n, ev.MODELO_BARATO) for n in ("límite + respaldo", "+ cortacircuitos")]
    for nombre, m in filas:
        r = simular(nombre, latencias[m], ndcg_parser[m], ndcg_base)
        c = quantiles(r["seg"], n=20, method="inclusive")
        print(f"   {nombre + ' · ' + m:34} {r['respondidos'] / PEDIDOS:>10.1%} {mean(r['ndcg']):>8.3f} {c[9]:>7.1f} "
              f"{c[18]:>7.1f} {max(r['seg']):>8.0f} {r['llamadas']:>9}")
    print("\n   Referencias, sin fallos: " + " · ".join(f"siempre con parser {m} {mean(v):.3f}"
                                                       for m, v in ndcg_parser.items())
          + f" · siempre sin parser {mean(ndcg_base):.3f}")
