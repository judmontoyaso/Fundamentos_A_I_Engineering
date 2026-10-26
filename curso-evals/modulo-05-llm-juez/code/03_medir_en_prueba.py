"""
03 · Medir el juez elegido en el set de PRUEBA, que no se usó para mejorarlo (manual §6).

Se corre tres veces (para ver cuánto varía) y se reportan TPR y TNR con un intervalo de confianza de
Wilson. Si los números en prueba son mucho peores que en desarrollo, el prompt se ajustó a los casos de
desarrollo. Guarda salida/juez_calibracion.json para que 04 corrija la tasa de fallos con estos números.
"""
from __future__ import annotations
import json
import math
import pathlib
import sys
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
jd = import_module("02_juez_en_desarrollo")
sj, ev = jd.sj, jd.ev

VERSION = "v3"
CORRIDAS = 3


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - m), min(1.0, c + m)


if __name__ == "__main__":
    _, test = sj.separar(sj.construir())
    print(f"Set de prueba: {len(test)} ítems · juez {VERSION} · {CORRIDAS} corridas\n")
    vp = fn = vn = fp = 0
    with ev.tz.nueva_traza("juez en prueba"):
        for vez in range(1, CORRIDAS + 1):
            res = ev.tz.en_paralelo(lambda it: jd.juzgar(it, VERSION), [(it,) for it in test])
            for it, r in zip(test, res):
                if it["inventa"]:
                    vp += r.inventa
                    fn += not r.inventa
                else:
                    vn += not r.inventa
                    fp += r.inventa
            print(f"  corrida {vez}: errores en {[it['item'] for it, r in zip(test, res) if r.inventa != it['inventa']]}")
    tpr, tnr = vp / (vp + fn), vn / (vn + fp)
    print(f"\nSumando las {CORRIDAS} corridas ({vp + fn} juicios de ítems que inventan, {vn + fp} de ítems que no):")
    print(f"  TPR {tpr:.0%}  IC95 [{wilson(vp, vp + fn)[0]:.0%}, {wilson(vp, vp + fn)[1]:.0%}]")
    print(f"  TNR {tnr:.0%}  IC95 [{wilson(vn, vn + fp)[0]:.0%}, {wilson(vn, vn + fp)[1]:.0%}]")
    print("  (Las corridas repiten los mismos ítems: el intervalo es optimista; el tamaño que manda son los ítems.)")
    ruta = ev.SALIDA / "juez_calibracion.json"
    ruta.write_text(json.dumps({"version": VERSION, "vp": vp, "fn": fn, "vn": vn, "fp": fp}), encoding="utf-8")
    print(f"\nGuardado en {ruta}")
