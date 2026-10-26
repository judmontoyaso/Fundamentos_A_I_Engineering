"""
03 · ¿El cambio empeora el sistema, o es ruido? Una regla de decisión para el CI (manual §6).

Se compara una versión nueva con la actual SOBRE LOS MISMOS CASOS. Los casos donde las dos aciertan o
las dos fallan no informan; los que importan son los DISCORDANTES: b = arreglados (fallaba y ahora no),
c = rotos (acertaba y ahora no). La prueba exacta de McNemar dice si c es mayor que b más de lo que
explicaría el azar. Regla del CI:
  1. un caso crítico roto  -> bloquear, siempre;
  2. rotos significativamente más que arreglados (p < 0.05) -> bloquear;
  3. si no, pasar, y avisar si hay rotos (para leerlos).
Ejemplo: el extractor v1 contra v2 con el modelo barato (el caso del Módulo 1).
"""
from __future__ import annotations
import math
import pathlib
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")

CRITICOS = {22, 24}                    # la inyección y el correo que el candidato dice no usar
MODELO = ev.MODELO_BARATO
REPETICIONES = 3                       # sin caché: cada caso cuenta como bien si sale bien en todas


def mcnemar_exacta(b: int, c: int) -> float:
    """P de observar c o más rotos entre b + c discordantes si romper y arreglar fueran igual de probables."""
    n = b + c
    return sum(math.comb(n, k) for k in range(c, n + 1)) / 2 ** n if n else 1.0


def perfectos(version: str) -> dict[int, bool]:
    res: dict[int, bool] = {}
    for _ in range(REPETICIONES):
        filas = ev.tz.en_paralelo(lambda cv: (cv["id"], all(ev.comparar_ficha(ev.extraer(cv["texto"], version, MODELO),
                                                                               cv["esperado"]).values())),
                                  [(cv,) for cv in datos.CVS])
        for i, ok in filas:
            res[i] = res.get(i, True) and ok
    return res


def decidir(actual: dict[int, bool], nueva: dict[int, bool]) -> str:
    rotos = [i for i in actual if actual[i] and not nueva[i]]
    arreglados = [i for i in actual if not actual[i] and nueva[i]]
    p = mcnemar_exacta(len(arreglados), len(rotos))
    print(f"  arreglados {arreglados} · rotos {rotos} · McNemar p = {p:.3f}")
    if CRITICOS & set(rotos):
        return f"BLOQUEAR: rompe casos críticos {sorted(CRITICOS & set(rotos))}"
    if p < 0.05:
        return "BLOQUEAR: rompe significativamente más casos de los que arregla"
    return "PASAR" + (f", pero lee los rotos {rotos}" if rotos else "")


if __name__ == "__main__":
    ev.CACHE["activa"] = False               # aquí interesa la variación real
    with ev.tz.nueva_traza("decidir contra la línea base", modelo=MODELO):
        v1, v2 = perfectos("v1"), perfectos("v2")
    print(f"Modelo {MODELO} · {len(v1)} casos · un caso cuenta como bien si sale bien en las {REPETICIONES} corridas")
    print(f"  perfectos: v1 {sum(v1.values())} · v2 {sum(v2.values())}")
    print(f"\nDecisión para pasar de v1 a v2: {decidir(v1, v2)}")
    print("\nEjemplos de la regla con números inventados para ver la frontera:")
    for b, c in [(1, 3), (0, 4), (0, 5), (2, 8)]:
        print(f"  {b} arreglados, {c} rotos -> p = {mcnemar_exacta(b, c):.3f}")
