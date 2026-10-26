"""
04 · ¿Cuántos perfiles inventan DE VERDAD? Corregir la tasa observada con los errores del juez (manual §7).

El juez marca "inventa" en una fracción p de los perfiles. Como el juez se equivoca, p no es la tasa
real. Si se conocen su TPR y su TNR (03), la estimación de Rogan-Gladen corrige:
        tasa real ≈ (p + TNR - 1) / (TPR + TNR - 1)
El intervalo sale de un bootstrap que remuestrea a la vez los perfiles juzgados y los juicios de
calibración: así refleja la incertidumbre de los dos.
Se aplica a los perfiles v1 y v2 del pipeline del Módulo 2 (salida/pipeline_v1|v2_<modelo>.jsonl).
"""
from __future__ import annotations
import json
import pathlib
import random
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
jd = import_module("02_juez_en_desarrollo")
ev = jd.ev
datos = import_module("ev_datos")

MODELO = ev.MODELO_BARATO
B = 2000


def corregir(p: float, tpr: float, tnr: float) -> float:
    d = tpr + tnr - 1
    return min(1.0, max(0.0, (p + tnr - 1) / d)) if d > 0 else float("nan")


def perfiles(version: str) -> list[dict]:
    try:
        return ev.leer_jsonl(f"pipeline_{version}_{MODELO}.jsonl")
    except FileNotFoundError:                     # no corriste el 04 del Módulo 2: se genera aquí
        with ev.tz.nueva_traza(f"pipeline {version}"):
            filas = ev.tz.en_paralelo(lambda cv: {"id": cv["id"], **ev.pipeline(cv["texto"], MODELO, version)},
                                      [(cv,) for cv in datos.CVS])
        ev.guardar_jsonl(f"pipeline_{version}_{MODELO}.jsonl", filas)
        return filas


if __name__ == "__main__":
    cal = json.loads((ev.SALIDA / "juez_calibracion.json").read_text(encoding="utf-8"))
    tpr, tnr = cal["vp"] / (cal["vp"] + cal["fn"]), cal["vn"] / (cal["vn"] + cal["fp"])
    pos = [1] * cal["vp"] + [0] * cal["fn"]          # juicios del juez sobre ítems que inventan (1 = acierta)
    neg = [1] * cal["vn"] + [0] * cal["fp"]          # juicios sobre ítems que no inventan (1 = acierta)
    print(f"Juez {cal['version']} calibrado en prueba: TPR {tpr:.0%} · TNR {tnr:.0%}\n")
    textos = {cv["id"]: " ".join(cv["texto"].split()) for cv in datos.CVS}
    rnd = random.Random(3)
    with ev.tz.nueva_traza("tasa corregida"):
        for version in ("v1", "v2"):
            filas = perfiles(version)
            items = [{"cv": textos[f["id"]], "perfil": f["perfil"]} for f in filas]
            marcas = [r.inventa for r in ev.tz.en_paralelo(lambda it: jd.juzgar(it, cal["version"]), [(it,) for it in items])]
            p = sum(marcas) / len(marcas)
            boot = []
            for _ in range(B):
                pb = sum(rnd.choice(marcas) for _ in marcas) / len(marcas)
                tb = sum(rnd.choice(pos) for _ in pos) / len(pos)
                nb = sum(rnd.choice(neg) for _ in neg) / len(neg)
                boot.append(corregir(pb, tb, nb))
            boot.sort()
            lo, hi = boot[int(0.025 * B)], boot[int(0.975 * B) - 1]
            print(f"  perfiles {version}: el juez marca {sum(marcas)}/{len(marcas)} ({p:.0%}) · tasa corregida "
                  f"{corregir(p, tpr, tnr):.0%}  IC95 [{lo:.0%}, {hi:.0%}]")
            print(f"     marcados: {[f['id'] for f, m in zip(filas, marcas) if m]}")
    print("\nSi el juez casi nunca se equivoca (TPR y TNR cerca de 100 %), la corrección casi no cambia nada.")
    print("Cuanto más se equivoca, más se mueve la estimación y más ancho es el intervalo.")
