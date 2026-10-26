"""
04 · ¿Qué encuentran los sintéticos que el set escrito a mano no encontraba? (manual §7)

Corre el extractor (Módulo 1) sobre los CVs sintéticos válidos con varias configuraciones y cuenta
los casos con algún fallo POR VALOR DE CADA DIMENSIÓN. Una dimensión donde un valor falla mucho más
que los demás es un tipo de entrada que el sistema no maneja, y que quizá el set a mano no tenía.
"""
from __future__ import annotations
import pathlib
import sys
from collections import defaultdict
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
dh = import_module("01_dimensiones_y_hechos")
ev = dh.ev

CONFIGS = [("v1", ev.MODELO_BARATO), ("v2", ev.MODELO_BARATO), ("v1", None)]   # None = el modelo del .env


def correr(filas: list[dict], version: str, modelo: str | None) -> list[dict]:
    def uno(f):
        ficha = ev.extraer(f["texto"], version, modelo)
        return {**f, "obtenido": ficha.model_dump(), "ok": ev.comparar_ficha(ficha, f["esperado"])}
    with ev.tz.nueva_traza(f"extractor sobre sintéticos {version}", modelo=modelo or ev.tz.MODELO):
        return ev.tz.en_paralelo(uno, [(f,) for f in filas])


if __name__ == "__main__":
    validas = ev.leer_jsonl("sinteticos_validos.jsonl")
    print(f"{len(validas)} CVs sintéticos válidos\n")
    resultados = {}
    for version, modelo in CONFIGS:
        nombre = f"{modelo or ev.tz.MODELO} {version}"
        res = correr(validas, version, modelo)
        resultados[nombre] = res
        malos = [r for r in res if not all(r["ok"].values())]
        campos = defaultdict(int)
        for r in malos:
            for k, ok in r["ok"].items():
                campos[k] += not ok
        print(f"== {nombre}: {len(validas) - len(malos)}/{len(validas)} perfectos · fallos por campo {dict(campos)}")
        for d, vals in dh.DIMENSIONES.items():
            linea = []
            for v in vals:
                grupo = [r for r in res if r["tupla"][d] == v]
                if grupo:
                    linea.append(f"{v} {sum(not all(r['ok'].values()) for r in grupo)}/{len(grupo)}")
            print(f"   {d:8} " + " · ".join(linea))
        for r in malos:
            mal = [k for k, ok in r["ok"].items() if not ok]
            clave = {"anios": "anios_experiencia"}
            det = ", ".join(f"{k}: esperado {r['esperado'][k]!r} obtenido {r['obtenido'][clave.get(k, k)]!r}" for k in mal)
            print(f"     {r['id']:4} {r['tupla']['años']:16} {r['tupla']['idioma']:9} {r['tupla']['ruido']:10} "
                  f"{r['tupla']['ataque']:9} {det}")
        print()
