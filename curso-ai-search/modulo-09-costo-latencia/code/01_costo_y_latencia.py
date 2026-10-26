"""
01 · Cuánto cuesta y cuánto tarda cada pieza, y qué compra cada una (manual §1-§4).

Cinco configuraciones del buscador, de la más barata a la más cara:
  base               : híbrida (Módulo 1), sin LLM
  parser nano        : consulta entendida con el modelo barato + filtros suaves (Módulo 2)
  parser principal   : lo mismo con el modelo principal
  nano + reranker    : parser nano + reranker LLM sobre el top 20 (Módulo 4, modelo barato, 20 llamadas en paralelo)
  principal + rerank : parser principal + el mismo reranker
1. CALIDAD: nDCG@10 en las 41 consultas (con la caché: no vuelve a pagar lo ya medido).
2. COSTO Y LATENCIA, EN VIVO: 8 consultas sin caché; de las trazas salen los segundos por consulta y los tokens de cada
   llamada. La medición se guarda en salida/m9_medicion.json y se reutiliza (MEDIR_DE_NUEVO=1 para repetirla).
   La primera medición tarda unos 3.5 minutos: si la app corta a los 300 s, córrela una vez desde la terminal (o sube
   KERNEL_TIMEOUT en app/backend/.env).
Precios: si defines en .env PRECIO_<MODELO>="entrada,salida" (USD por millón de tokens; por ejemplo
PRECIO_GPT_5_4_NANO), se calcula el costo por 1.000 consultas. Si no, se queda en tokens.
"""
from __future__ import annotations
import json
import os
import pathlib
import sys
import time
from importlib import import_module
from statistics import mean, quantiles

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
en = import_module("as_entender")
q = import_module("as_consultas")
ev = ac.ev
sys.path.append(str(ac.CURSO / "modulo-04-retrieval" / "code"))
rr = import_module("01_reranker_llm")

PRINCIPAL, BARATO = ev.tz.MODELO, ev.MODELO_BARATO
CONFIGS = {"base": (None, False), "parser nano": (BARATO, False), "parser principal": (PRINCIPAL, False),
           "nano + reranker": (BARATO, True), "principal + rerank": (PRINCIPAL, True)}
MUESTRA = [t for _, t, _ in q.CONSULTAS][::5][:8]
MEDICION = ac.SALIDA / "m9_medicion.json"


def buscar(texto: str, config: str) -> list[int]:
    modelo, rerank = CONFIGS[config]
    if modelo is None:
        return bs.ranking(texto, "hibrida", 119)
    orden = en.buscar(texto, "suaves", en.parsear(texto, modelo))
    return rr.rerank(texto, orden) if rerank else orden


def precio(modelo: str) -> tuple[float, float] | None:
    v = os.getenv("PRECIO_" + modelo.upper().replace("-", "_").replace(".", "_"))
    try:
        a, b = (float(x) for x in v.split(","))
        return a, b
    except (AttributeError, ValueError):
        return None


def medir_en_vivo() -> dict:
    ev.CACHE["activa"] = False
    out = {c: [] for c in CONFIGS}
    for texto in MUESTRA:
        for c in CONFIGS:
            with ev.tz.nueva_traza(f"m9 · {c}") as s:
                t0 = time.time()
                buscar(texto, c)
                seg = time.time() - t0
            llms = [x for x in ev.tz.spans(s.trace_id) if x["atributos"].get("tipo") == "llm"]
            tokens = {}
            for x in llms:
                a = x["atributos"]
                m = tokens.setdefault(a.get("modelo_pedido"), [0, 0, 0])
                m[0] += a.get("tokens_entrada", 0)
                m[1] += a.get("tokens_salida", 0)
                m[2] += a.get("tokens_razonamiento", 0)
            out[c].append({"seg": seg, "llamadas": len(llms), "tokens": tokens})
    return {"fecha": time.strftime("%Y-%m-%d"), "consultas": MUESTRA, "por_config": out}


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    rels = q.relevancias(ac.cvs())
    print("1. Calidad: nDCG@10 en las 41 consultas")
    calidad = {}
    for c in CONFIGS:
        ordenes = ev.tz.en_paralelo(lambda t: buscar(t, c), [(t,) for _, t, _ in q.CONSULTAS], hilos=4)
        calidad[c] = mean(bs.ndcg(o, r) for o, r in zip(ordenes, rels))
        print(f"   {c:20} {calidad[c]:.3f}")

    if MEDICION.exists() and os.getenv("MEDIR_DE_NUEVO") != "1":
        med = json.loads(MEDICION.read_text(encoding="utf-8"))
        print(f"\n2. Costo y latencia (medición guardada del {med['fecha']}; MEDIR_DE_NUEVO=1 para repetirla)")
    else:
        med = medir_en_vivo()
        ac.SALIDA.mkdir(exist_ok=True)
        MEDICION.write_text(json.dumps(med, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n2. Costo y latencia, en vivo")
    print(f"   {len(med['consultas'])} consultas, sin caché. Por consulta:")
    print(f"   {'':20} {'llamadas':>9} {'p50 s':>7} {'p95 s':>7} {'tokens entrada':>15} {'salida (razon.)':>16} {'USD/1000':>9}")
    for c, filas in med["por_config"].items():
        cuantiles = quantiles([f["seg"] for f in filas], n=20, method="inclusive")
        p50, p95 = cuantiles[9], cuantiles[18]
        ent = mean(sum(t[0] for t in f["tokens"].values()) for f in filas)
        sal = mean(sum(t[1] for t in f["tokens"].values()) for f in filas)
        raz = mean(sum(t[2] for t in f["tokens"].values()) for f in filas)
        usd = 0.0
        for f in filas:
            for m, (a, b, _) in f["tokens"].items():
                p = precio(m)
                usd = None if p is None or usd is None else usd + (a * p[0] + b * p[1]) / 1e6
        usd_txt = "—" if usd is None else f"{usd / len(filas) * 1000:.2f}"
        print(f"   {c:20} {mean(f['llamadas'] for f in filas):>9.0f} {p50:>7.2f} {p95:>7.2f} {ent:>15.0f} "
              f"{sal:>9.0f} ({raz:.0f}) {usd_txt:>9}")
    print("\n   Por modelo (tokens de entrada y salida por consulta, media):")
    for c, filas in med["por_config"].items():
        modelos = sorted({m for f in filas for m in f["tokens"]})
        if modelos:
            print(f"   {c:20} " + " · ".join(
                f"{m}: {mean(f['tokens'].get(m, [0, 0])[0] for f in filas):.0f} / "
                f"{mean(f['tokens'].get(m, [0, 0])[1] for f in filas):.0f}" for m in modelos))
