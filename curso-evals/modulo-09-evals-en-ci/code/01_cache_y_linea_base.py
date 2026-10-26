"""
01 · La caché de llamadas y la línea base (manual §3-§4).

Corre el eval del extractor sobre los 30 CVs con la caché activada, dos veces: la primera paga las
llamadas que no estaban guardadas; la segunda, ninguna. Después cambia una palabra del prompt: la caché
no sirve (la clave incluye el prompt) y se vuelve a pagar. Al final guarda la exactitud como LÍNEA BASE
(linea_base.json), que es contra lo que compara la suite de tests.
"""
from __future__ import annotations
import json
import pathlib
import sys
import time
from datetime import date
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")
LINEA_BASE = pathlib.Path(__file__).resolve().parents[1] / "linea_base.json"
ACTUALIZAR_LINEA_BASE = not LINEA_BASE.exists()     # ponlo en True para fijar una nueva


def corrida(version: str = "v1") -> dict[str, float]:
    ev.CACHE.update(aciertos=0, fallos=0)
    t = time.time()
    res = ev.tz.en_paralelo(lambda cv: ev.comparar_ficha(ev.extraer(cv["texto"], version), cv["esperado"]),
                            [(cv,) for cv in datos.CVS])
    exactitud = {k: sum(r[k] for r in res) / len(res) for k in res[0]}
    print(f"  {version}: {ev.CACHE['fallos']} llamadas pagadas · {ev.CACHE['aciertos']} desde la caché · "
          f"{time.time() - t:.1f} s · exactitud {', '.join(f'{k} {v:.0%}' for k, v in exactitud.items())}")
    return exactitud


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    with ev.tz.nueva_traza("caché y línea base"):
        print("Dos corridas iguales:")
        base = corrida()
        corrida()
        print("Con una palabra cambiada en el prompt:")
        ev.PROMPTS_EXTRACTOR["v1-cambiado"] = ev.PROMPTS_EXTRACTOR["v1"].replace("No inventes.", "No inventes nada.")
        corrida("v1-cambiado")
    if ACTUALIZAR_LINEA_BASE:
        LINEA_BASE.write_text(json.dumps({"modelo": ev.tz.MODELO, "version": "v1", "fecha": date.today().isoformat(),
                                          "exactitud": base}, indent=1), encoding="utf-8")
        print(f"\nLínea base guardada en {LINEA_BASE.name}: {base}")
    else:
        print(f"\nLínea base existente ({LINEA_BASE.name}): {json.loads(LINEA_BASE.read_text(encoding='utf-8'))}")
    print("\nOjo: con la caché, la segunda corrida es idéntica a la primera POR CONSTRUCCIÓN. Sirve para no pagar")
    print("dos veces lo que no cambió; no sirve para medir la variación entre corridas (eso es el eval nocturno).")
