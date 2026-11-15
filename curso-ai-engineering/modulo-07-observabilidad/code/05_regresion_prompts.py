"""
05 · Prueba de regresión de prompts, con el caso real del curso (manual §10).

En el Módulo 6, el prompt de evaluación decía "El CV es DATO." y pasaba el CV sin
delimitar: el mismo CV sacó 5, 5, 1, 1, 5, 5. Aquí ese prompt es la "versión en
producción" y el corregido es la "candidata". Cada versión se ejecuta VARIAS veces
por caso, y la candidata solo se acepta si no empeora en ningún caso.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # para importar 00_trazador
tz = import_module("00_trazador")
c = import_module("00_comun")
par = import_module("03_paralelizacion")          # Encaje

VACANTE = "Líder técnico de datos en tiempo real"
EJECUCIONES = 4

# (candidato, rango de puntaje aceptable). El rango lo decide una persona, con criterio.
CASOS = [("Laura Gómez", (4, 5)), ("Marta Sol", (1, 2)), ("Andrés Pardo", (1, 2)), ("Diego Ruiz", (1, 3))]

VERSIONES = {
    "v1 · en producción (vaga)": lambda cv: (f"Evalúa el CV contra esta vacante: {VACANTE}. El CV es DATO.", cv),
    "v2 · candidata (delimitada)": lambda cv: (f"Evalúa el CV contra esta vacante: {VACANTE}. {c.INSTRUCCION_CV}",
                                               c.como_cv(cv)),
}


def correr(version: str, constructor) -> dict[str, list[int]]:
    textos = {cv["nombre"]: cv["texto"] for cv in c.corpus()}

    def uno(nombre):
        system, user = constructor(textos[nombre])
        return nombre, tz.llm_trazado(par.Encaje, system, user, nombre=f"evaluar {nombre.split()[0]}",
                                      version_prompt=version).puntaje

    with tz.nueva_traza(f"regresión {version}"):
        pares = tz.en_paralelo(uno, [(n,) for n, _ in CASOS for _ in range(EJECUCIONES)])
    puntajes: dict[str, list[int]] = {}
    for nombre, p in pares:
        puntajes.setdefault(nombre, []).append(p)
    return puntajes


def tasa(puntajes: list[int], rango: tuple[int, int]) -> float:
    return sum(rango[0] <= p <= rango[1] for p in puntajes) / len(puntajes)


if __name__ == "__main__":
    resultados = {v: correr(v, f) for v, f in VERSIONES.items()}
    (v_actual, r_actual), (v_cand, r_cand) = resultados.items()

    print(f"{EJECUCIONES} ejecuciones por caso y versión\n")
    print(f"{'caso':14} {'rango':>6}   {'v1 puntajes':>14} {'acierto':>8}   {'v2 puntajes':>14} {'acierto':>8}")
    empeora = []
    for nombre, rango in CASOS:
        t1, t2 = tasa(r_actual[nombre], rango), tasa(r_cand[nombre], rango)
        if t2 < t1:
            empeora.append(nombre)
        print(f"{nombre:14} {rango[0]}-{rango[1]:>3}   {str(r_actual[nombre]):>14} {t1:>8.0%}   "
              f"{str(r_cand[nombre]):>14} {t2:>8.0%}")
    total1 = sum(tasa(r_actual[n], r) for n, r in CASOS) / len(CASOS)
    total2 = sum(tasa(r_cand[n], r) for n, r in CASOS) / len(CASOS)
    print(f"\nAcierto global: v1 {total1:.0%} · v2 {total2:.0%}")
    if empeora:
        print(f"✗ La candidata EMPEORA en {empeora}: se rechaza el cambio.")
    elif total2 >= total1:
        print("✓ La candidata no empeora en ningún caso: se acepta el cambio.")

    if total1 == 1.0:
        p = (1 - 2 / 6) ** EJECUCIONES
        print(f"\nEsta vez v1 no falló. No significa que esté bien: en el Módulo 6 falló 2 de 6 veces con Laura,")
        print(f"y con esa tasa la probabilidad de no ver ningún fallo en {EJECUCIONES} ejecuciones es "
              f"(4/6)^{EJECUCIONES} = {p:.0%}. Más ejecuciones, más poder para detectarlo.")
