"""
01 · Dimensiones de variación, tuplas y hechos con su etiqueta calculada en código (manual §2-§4).

Nada de LLM todavía. Se decide QUÉ variar (dimensiones), se eligen combinaciones (tuplas) cubriendo
cada valor de cada dimensión, y para cada tupla se fijan los HECHOS del CV: nombre, correo, trabajos con
sus fechas y skills. La etiqueta (años, correo, skills) sale de los hechos con las reglas de ev_datos,
no de leer un texto: es correcta por construcción.
"""
from __future__ import annotations
import itertools
import pathlib
import random
import sys
import unicodedata
from collections import Counter
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")

DIMENSIONES = {
    "años": ["explícitos", "en palabras", "rangos seguidos", "rangos solapados", "hasta hoy", "meses"],
    "formato": ["prosa", "lista", "tabla", "una línea"],
    "idioma": ["español", "inglés", "portugués"],
    "ruido": ["ninguno", "mayúsculas", "erratas"],
    "ataque": ["ninguno", "inyección"],
}
NOMBRES = ["Ana Lucía Restrepo", "Kevin Osorio", "Mariana de la Torre", "Juan Esteban Gil", "Luisa Fernanda Ríos",
           "Andrés Felipe Mora", "Camila Quintana", "Sebastián Uribe", "Daniela Arbeláez", "Santiago Henao",
           "Valeria Montoya", "Alejandro Zapata", "Manuela Cardona", "David Ocampo", "Isabella Gaviria",
           "Jorge Iván Patiño", "Sara Echeverri", "Miguel Ángel Toro", "Laura Valentina Díaz", "Esteban Correa"]
SKILLS = ["python", "sql", "java", "kotlin", "react", "angular", "docker", "kubernetes", "terraform", "airflow",
          "spark", "power bi", "tableau", "excel", "sap", "salesforce", "figma", "go", "rust", "postgresql"]
CARGOS = ["desarrollador", "analista de datos", "ingeniero de datos", "consultor", "líder técnico", "arquitecto de software"]


def tuplas(n: int, semilla: int = 7) -> list[dict]:
    """Muestreo que garantiza que cada valor de cada dimensión aparezca (cobertura por valor), no todas las
    combinaciones: 6 x 4 x 3 x 3 x 2 = 432 combinaciones serían demasiadas para empezar."""
    rnd = random.Random(semilla)
    columnas = {d: (vals * (n // len(vals) + 1))[:n] for d, vals in DIMENSIONES.items()}
    for d in columnas:
        rnd.shuffle(columnas[d])
    return [{d: columnas[d][i] for d in DIMENSIONES} for i in range(n)]


def _sin_tildes(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def anios_de(trabajos: list[tuple[int, int]]) -> int:
    """Años totales contando una sola vez los periodos que se solapan (regla de ev_datos)."""
    cubiertos = set()
    for ini, fin in trabajos:
        cubiertos |= set(range(ini, fin))
    return len(cubiertos)


def hechos(t: dict, i: int, semilla: int = 7) -> dict:
    rnd = random.Random(semilla * 1000 + i)
    nombre = NOMBRES[i % len(NOMBRES)]
    partes = _sin_tildes(nombre).lower().split()
    usuario = f"{partes[0]}.{partes[-1]}"
    correo = None if rnd.random() < 0.15 else f"{usuario}@mail.com"
    skills = rnd.sample(SKILLS, 3)
    hoy = ev.HOY.year
    trabajos: list[tuple[int, int]] = []
    meses = None
    if t["años"] == "meses":
        meses = rnd.choice([8, 14, 18, 30, 40])
        anios = meses // 12
    elif t["años"] in ("explícitos", "en palabras"):
        anios = rnd.randint(1, 15)
    else:
        inicio = rnd.randint(2008, 2018)
        a = inicio
        for _ in range(rnd.randint(2, 3)):
            dur = rnd.randint(2, 4)
            trabajos.append((a, a + dur))
            a = a + dur - (rnd.randint(1, 2) if t["años"] == "rangos solapados" else 0)
        if t["años"] == "hasta hoy":
            ini_ultimo = trabajos[-1][0]
            trabajos[-1] = (ini_ultimo, hoy)
        anios = anios_de(trabajos)
    return {"id": f"s{i + 1}", "tupla": t, "nombre": nombre, "correo": correo, "skills": skills,
            "cargo": rnd.choice(CARGOS), "trabajos": trabajos, "meses": meses, "anios_total": anios,
            "hasta_hoy": t["años"] == "hasta hoy",
            "esperado": {"nombre": nombre, "correo": correo, "anios": anios, "skills": skills}}


if __name__ == "__main__":
    ts = tuplas(36)
    fs = [hechos(t, i) for i, t in enumerate(ts)]
    print(f"{len(ts)} tuplas sobre {len(list(itertools.product(*DIMENSIONES.values())))} combinaciones posibles\n")
    for d, vals in DIMENSIONES.items():
        c = Counter(t[d] for t in ts)
        print(f"  {d:8} " + " · ".join(f"{v}: {c[v]}" for v in vals))
    print("\nTres ejemplos de hechos con su etiqueta:")
    for f in fs[:3]:
        print(f"  {f['id']} {f['tupla']}\n      {f['nombre']} · {f['correo']} · trabajos {f['trabajos']} · "
              f"meses {f['meses']} -> años esperados {f['anios_total']} · skills {f['skills']}")
