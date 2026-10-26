"""
04 · Convertir los fallos más importantes en evals automáticos, y usarlos para medir un v2 (manual §6-§7).

  contacto en el perfil -> chequeo por código (regex): gratis y exacto.
  nivel sin criterio    -> primero una REGLA (ev.RUBRICA_NIVEL), después un chequeo por código que la aplica
                           con los años correctos de ev_datos y las palabras de liderazgo del CV.
  perfil inventa        -> exige leer y comparar con el CV: queda para el juez del Módulo 5.

Paso 1: validar los chequeos contra la revisión manual (¿encuentran lo mismo que la persona?).
Paso 2: usarlos para comparar el pipeline v1 con el v2 en una corrida nueva.
"""
from __future__ import annotations
import json
import pathlib
import re
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")
m2 = import_module("m2_notas")

MODELO = ev.MODELO_BARATO
CONTACTO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|\+?\d[\d\s-]{8,}\d|linkedin|contacto", re.IGNORECASE)
LIDERAZGO = re.compile(r"\bl[ií]der|lider[oó]|arquitect|lead\b|dirig", re.IGNORECASE)


def nivel_esperado(cv: dict) -> str:
    anios = cv["esperado"]["anios"]
    if anios >= 7 or (anios >= 5 and LIDERAZGO.search(cv["texto"])):
        return "senior"
    return "semi-senior" if anios >= 3 else "junior"


def chequear(fila: dict, cv: dict) -> dict[str, bool]:
    """True = pasa el chequeo."""
    return {"sin contacto en el perfil": not CONTACTO.search(fila["perfil"]),
            "nivel según la regla": ev.norm(fila["nivel"]).replace(" ", "-") == nivel_esperado(cv)}


def contar(filas: list[dict]) -> dict[str, list[int]]:
    cvs = {cv["id"]: cv for cv in datos.CVS}
    fallos: dict[str, list[int]] = {}
    for f in filas:
        for nombre, ok in chequear(f, cvs[f["id"]]).items():
            if not ok:
                fallos.setdefault(nombre, []).append(f["id"])
    return fallos


if __name__ == "__main__":
    print("== Paso 1 · ¿Los chequeos ven lo mismo que la persona? (salidas revisadas en el manual) ==")
    revisadas = [json.loads(l) for l in (ev.COMUN / "m2_salidas_revisadas.jsonl").read_text(encoding="utf-8").splitlines()]
    auto = contar(revisadas)
    manual = {"sin contacto en el perfil": "contacto en el perfil", "nivel según la regla": "nivel sin criterio"}
    for chequeo, categoria in manual.items():
        a = set(auto.get(chequeo, []))
        h = {i for (i, _), c in m2.NOTA_A_CATEGORIA.items() if c == categoria}
        print(f"  {chequeo:26} automático {sorted(a)}\n  {'':26} persona    {sorted(h)}"
              f"\n  {'':26} solo el chequeo: {sorted(a - h) or '-'} · solo la persona: {sorted(h - a) or '-'}")

    print(f"\n== Paso 2 · v1 contra v2 en una corrida nueva ({MODELO}) ==")
    for version in ("v1", "v2"):
        with ev.tz.nueva_traza(f"pipeline {version}", modelo=MODELO):
            filas = ev.tz.en_paralelo(lambda cv: {"id": cv["id"], **ev.pipeline(cv["texto"], MODELO, version)},
                                      [(cv,) for cv in datos.CVS])
        ev.guardar_jsonl(f"pipeline_{version}_{MODELO}.jsonl", filas)
        for chequeo, ids in sorted(contar(filas).items()):
            print(f"  {version} · {chequeo:26} falla en {len(ids):>2}/30  {ids}")
        if not contar(filas):
            print(f"  {version} · ningún chequeo falla")
    print("\nLos chequeos miden lo que miden: v2 puede pasar los dos y seguir inventando en el perfil.")
    print("Ese fallo necesita un juez (Módulo 5). Lee una muestra de perfiles v2 antes de darlo por bueno.")
