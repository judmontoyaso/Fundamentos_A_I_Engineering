"""
01 · Correr el pipeline sobre los 30 CVs y dejar las salidas listas para LEER (manual §2-§3).

Pipeline: extraer (FichaCV) -> clasificar nivel -> redactar perfil, con el modelo barato.
No hay etiquetas para el nivel ni para el perfil: no se puede calcular una exactitud. Se lee.
Guarda salida/pipeline_<modelo>.jsonl y muestra cada caso en una ficha compacta.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")

MODELO = ev.MODELO_BARATO


def correr() -> list[dict]:
    def uno(cv):
        return {"id": cv["id"], "texto": cv["texto"], **ev.pipeline(cv["texto"], MODELO)}
    with ev.tz.nueva_traza("pipeline para error analysis", modelo=MODELO):
        return ev.tz.en_paralelo(uno, [(cv,) for cv in datos.CVS])


def ficha_de_lectura(f: dict) -> str:
    x = f["ficha"]
    return (f"#{f['id']} {' '.join(f['texto'].split())}\n"
            f"   ficha : {x['nombre']} · {x['correo']} · {x['anios_experiencia']} años · {x['skills']}\n"
            f"   nivel : {f['nivel']} ({f['razon_nivel']})\n"
            f"   perfil: {f['perfil']}")


if __name__ == "__main__":
    filas = correr()
    ruta = ev.guardar_jsonl(f"pipeline_{MODELO}.jsonl", filas)
    print(f"Modelo {MODELO} · {len(filas)} CVs · guardado en {ruta}\n")
    for f in filas:
        print(ficha_de_lectura(f) + "\n")
    print("Ahora: por cada caso, escribe UNA nota con lo primero que esté mal (o 'ok'). Sin categorías todavía.")
