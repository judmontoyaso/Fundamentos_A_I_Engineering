"""
03 · Por qué el porcentaje de acuerdo engaña: la paradoja del kappa (manual §4). Sin LLM: solo cuentas.

Dos parejas de anotadores con el MISMO 90 % de acuerdo. En la primera, la mitad de los perfiles no pasa;
en la segunda, casi todos pasan. El kappa las separa: con un fallo raro, acertar "pasa" es fácil hasta
para un anotador que no lee. El kappa descuenta ese acuerdo que saldría por azar.
"""
from __future__ import annotations
import pathlib
import random
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")


def pareja(n: int, pasa_a: int, pasa_b: int, ambos_pasa: int) -> tuple[list[bool], list[bool]]:
    """Construye dos listas de etiquetas con esos totales (tabla de contingencia 2x2)."""
    solo_a, solo_b = pasa_a - ambos_pasa, pasa_b - ambos_pasa
    ninguno = n - ambos_pasa - solo_a - solo_b
    a = [True] * ambos_pasa + [True] * solo_a + [False] * solo_b + [False] * ninguno
    b = [True] * ambos_pasa + [False] * solo_a + [True] * solo_b + [False] * ninguno
    return a, b


def describir(nombre: str, a: list[bool], b: list[bool]) -> None:
    acuerdo = sum(x == y for x, y in zip(a, b)) / len(a)
    print(f"  {nombre:44} acuerdo {acuerdo:.0%} · 'no pasa' A {a.count(False):>3} B {b.count(False):>3} · "
          f"kappa {ev.kappa(a, b):.2f}")


if __name__ == "__main__":
    print("100 perfiles, dos anotadores, 90 % de acuerdo en las dos parejas:")
    describir("fallos frecuentes (50 % no pasa)", *pareja(100, pasa_a=50, pasa_b=50, ambos_pasa=45))
    describir("fallos raros (~5 % no pasa)", *pareja(100, pasa_a=95, pasa_b=95, ambos_pasa=90))

    print("\nUn anotador que no lee y dice 'pasa' el 95 % de las veces, al azar, contra uno cuidadoso:")
    rnd = random.Random(1)
    cuidadoso = [rnd.random() > 0.05 for _ in range(1000)]
    perezoso = [rnd.random() > 0.05 for _ in range(1000)]
    describir("cuidadoso vs. perezoso (fallos raros)", cuidadoso, perezoso)
    print("\nCon fallos raros, el acuerdo alto es casi gratis. Reporta siempre el kappa, y mira cuántos 'no pasa'")
    print("marcó cada uno: dos anotadores pueden coincidir en lo fácil y no coincidir en NINGÚN fallo.")
