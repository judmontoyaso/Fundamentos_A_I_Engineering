"""
02 · Métricas operativas y costo a partir de las trazas guardadas (manual §4-§5).

Sin llamadas al modelo: lee los spans de 01 (ejecútalo antes) y calcula latencia
p50/p95 por tipo de operación, tasa de error, tokens por pedido, la proporción de
salida que es razonamiento, y el costo si configuraste los precios en .env.
"""
from __future__ import annotations
import math
import statistics
from collections import defaultdict
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # para importar 00_trazador
tz = import_module("00_trazador")


def percentil(valores: list[float], p: float) -> float:
    """Rango más cercano: el valor en la posición ceil(p/100 · n). Sin interpolar: un valor que existió."""
    v = sorted(valores)
    return v[max(0, math.ceil(p / 100 * len(v)) - 1)]


def tipo_de(nombre: str) -> str:
    return nombre.split()[0]          # "evaluar Laura" -> "evaluar"


if __name__ == "__main__":
    spans = tz.spans()
    if not spans:
        raise SystemExit("No hay trazas: ejecuta primero 01_trazas.py")
    pedidos = [s for s in spans if s["parent_id"] is None]
    llm = [s for s in spans if s["atributos"].get("tipo") == "llm" and "tokens_entrada" in s["atributos"]]
    print(f"{len(pedidos)} pedidos · {len(spans)} spans · {len(llm)} llamadas al LLM con tokens registrados\n")

    print("== Latencia por tipo de operación ==")
    por_tipo = defaultdict(list)
    errores = defaultdict(int)
    for s in spans:
        por_tipo[tipo_de(s["nombre"])].append(s["seg"])
        errores[tipo_de(s["nombre"])] += s["estado"] == "error"
    print(f"  {'operación':10} {'n':>3} {'p50':>7} {'p95':>7} {'promedio':>9} {'errores':>8}")
    for t, segs in sorted(por_tipo.items(), key=lambda x: -statistics.mean(x[1])):
        print(f"  {t:10} {len(segs):>3} {percentil(segs, 50):6.1f}s {percentil(segs, 95):6.1f}s "
              f"{statistics.mean(segs):8.1f}s {errores[t]:>8}")
    print("  Con pocas muestras el p95 es casi el máximo; aun así, compara p50 con promedio: si difieren mucho,")
    print("  hay una cola (arranque en frío, reintentos) que el promedio esconde.")

    print("\n== Tokens ==")
    ent = sum(s["atributos"]["tokens_entrada"] for s in llm)
    sal = sum(s["atributos"]["tokens_salida"] for s in llm)
    raz = sum(s["atributos"]["tokens_razonamiento"] for s in llm)
    cache = sum(s["atributos"]["tokens_cache"] for s in llm)
    print(f"  entrada {ent} (en caché: {cache}) · salida {sal}, de los cuales razonamiento {raz} "
          f"({raz / sal:.0%} de la salida)" if sal else "  sin tokens de salida registrados")
    for t in sorted({tipo_de(s["nombre"]) for s in llm}):
        grupo = [s["atributos"] for s in llm if tipo_de(s["nombre"]) == t]
        gs, gr = sum(a["tokens_salida"] for a in grupo), sum(a["tokens_razonamiento"] for a in grupo)
        print(f"    {t:10} salida media {gs / len(grupo):5.0f} tokens · razonamiento {gr / gs:4.0%}" if gs else "")

    print("\n== Por pedido ==")
    for p in pedidos[-5:]:
        hijos = [s for s in spans if s["trace_id"] == p["trace_id"] and s["atributos"].get("tipo") == "llm"]
        e = sum(h["atributos"].get("tokens_entrada", 0) for h in hijos)
        o = sum(h["atributos"].get("tokens_salida", 0) for h in hijos)
        usd = tz.costo_usd(e, o, sum(h["atributos"].get("tokens_cache", 0) for h in hijos))
        dinero = f" · {usd * 1000:.3f} USD por cada 1000 pedidos así" if usd is not None else ""
        print(f"  {p['trace_id']} {p['nombre'][:18]:18} {p['seg']:5.1f}s · {len(hijos)} llamadas · "
              f"{e} entrada / {o} salida{dinero}  [{p['estado']}]")
    if tz.costo_usd(1, 1) is None:
        print("\n  Para ver dinero, pon en app/backend/.env los precios de tu cuenta (USD por millón de tokens):")
        print("  PRECIO_ENTRADA_USD_1M=...  PRECIO_SALIDA_USD_1M=...  PRECIO_CACHE_USD_1M=...  y reinicia la API.")
