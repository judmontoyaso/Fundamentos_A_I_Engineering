"""
01 · Producción: medir sin la respuesta correcta, y ver qué parte de los errores se ve así (manual §2-§5).

Tres "días" de tráfico al extractor (modelo barato, prompt v2). Días 1 y 2: CVs como los del set del
Módulo 1. Día 3: la mezcla cambia (CVs sintéticos del Módulo 3: portugués, tablas, rangos) = drift.
En producción no hay etiquetas: solo chequeos SIN REFERENCIA, que miran la salida contra la propia entrada:
  correo inventado (no aparece en el CV) · nombre ausente · años imposibles para las fechas del CV · skills vacías
Como aquí SÍ hay etiquetas, se compara la tasa de alertas con la tasa de error real: qué cubren los chequeos.
Requiere salida/sinteticos_validos.jsonl (laboratorios 02 y 03 del Módulo 3).
"""
from __future__ import annotations
import math
import pathlib
import random
import re
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")

MODELO, VERSION = ev.MODELO_BARATO, "v2"
POR_DIA = 25
VIGENTE = re.compile(r"hoy|actual|presente|present|current|atual|hoje|la fecha", re.IGNORECASE)


def trafico(semilla: int = 5) -> dict[int, list[dict]]:
    rnd = random.Random(semilla)
    reales = [{"id": f"r{cv['id']}", "texto": cv["texto"], "esperado": cv["esperado"]} for cv in datos.CVS]
    sinteticos = [{"id": f["id"], "texto": f["texto"], "esperado": f["esperado"]}
                  for f in ev.leer_jsonl("sinteticos_validos.jsonl")]
    return {1: rnd.sample(reales, POR_DIA), 2: rnd.sample(reales, POR_DIA),
            3: rnd.sample(sinteticos, 20) + rnd.sample(reales, POR_DIA - 20)}


def alertas(texto: str, f) -> list[str]:
    """Chequeos que solo necesitan la entrada y la salida."""
    t, a = ev.norm(texto), []
    if f.correo and ev.norm(f.correo) not in t:
        a.append("correo inventado")
    if not all(ev.norm(p) in t for p in f.nombre.split()):
        a.append("nombre ausente")
    anios = [int(x) for x in re.findall(r"\b(?:19|20)\d{2}\b", texto)]
    if anios:
        tope = max(max(anios), ev.HOY.year if VIGENTE.search(texto) else 0) - min(anios)
        if f.anios_experiencia > tope:
            a.append("años imposibles")
    elif f.anios_experiencia > 45:
        a.append("años imposibles")
    if not f.skills:
        a.append("skills vacías")
    return a


def binomial_cola(k: int, n: int, p: float) -> float:
    """P(X >= k) con X ~ Binomial(n, p): qué tan raro es ver k alertas si la tasa siguiera siendo p."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def procesar(cv: dict) -> dict:
    f = ev.extraer(cv["texto"], VERSION, MODELO)
    ok = ev.comparar_ficha(f, cv["esperado"])
    return {"id": cv["id"], "texto": cv["texto"], "esperado": cv["esperado"], "ficha": f,
            "error_real": not all(ok.values()), "alertas": alertas(cv["texto"], f)}


if __name__ == "__main__":
    ev.CACHE["activa"] = False
    dias = trafico()
    resultados = {}
    with ev.tz.nueva_traza("producción simulada", modelo=MODELO):
        for d, cvs in dias.items():
            resultados[d] = ev.tz.en_paralelo(procesar, [(cv,) for cv in cvs])
    base_alertas = sum(bool(r["alertas"]) for d in (1, 2) for r in resultados[d]) / (2 * POR_DIA)
    print(f"Extractor {MODELO} {VERSION} · {POR_DIA} CVs por día\n")
    print(f"{'día':>3} {'alertas':>9} {'errores reales':>15} {'errores con alerta':>19}  alerta estadística")
    for d, rs in resultados.items():
        k = sum(bool(r["alertas"]) for r in rs)
        reales = [r for r in rs if r["error_real"]]
        vistos = [r for r in reales if r["alertas"]]
        p = binomial_cola(k, len(rs), max(base_alertas, 1 / (2 * POR_DIA))) if d == 3 else None
        print(f"{d:>3} {k:>6}/{len(rs)} {len(reales):>12}/{len(rs)} {len(vistos):>15}/{len(reales) or 1}  "
              + (f"P(≥{k} | tasa de los días 1-2 = {base_alertas:.0%}) = {p:.4f}" if p is not None else ""))
    todos = [r for rs in resultados.values() for r in rs]
    errores = [r for r in todos if r["error_real"]]
    print(f"\nDe {len(errores)} errores reales, los chequeos sin referencia vieron {sum(bool(r['alertas']) for r in errores)}. "
          f"Falsas alarmas (alerta sin error): {sum(bool(r['alertas']) and not r['error_real'] for r in todos)}.")
    print("Errores que NO se vieron (lo que producción no te cuenta):")
    for r in errores:
        if not r["alertas"]:
            fallo = [k for k, v in ev.comparar_ficha(r["ficha"], r["esperado"]).items() if not v]
            print(f"  {r['id']:4} {fallo} · obtenido {r['ficha'].anios_experiencia} años, esperado {r['esperado']['anios']} · "
                  f"{' '.join(r['texto'].split())[:90]}")
    ev.guardar_jsonl("produccion_dia3.jsonl", [{**{k: v for k, v in r.items() if k != "ficha"},
                                               "ficha": r["ficha"].model_dump()} for r in resultados[3]])
