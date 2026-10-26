"""
01 · El primer eval: 30 CVs, lo esperado de cada uno y un chequeo por campo (manual §3-§5).

No hay juez ni métrica sofisticada: cada campo tiene una respuesta correcta que el código compara.
El resultado se guarda versionado en salida/ para poder compararlo con la siguiente versión (02).
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")
CAMPOS = ["nombre", "correo", "anios", "skills"]


def correr(version: str = "v1", modelo: str | None = None) -> list[dict]:
    def uno(cv):
        ficha = ev.extraer(cv["texto"], version, modelo)
        return {"id": cv["id"], "tipo": cv["tipo"], "version": version, "modelo": modelo or ev.tz.MODELO,
                "esperado": cv["esperado"],
                "obtenido": ficha.model_dump(), "ok": ev.comparar_ficha(ficha, cv["esperado"])}
    with ev.tz.nueva_traza(f"eval extractor {version}", casos=len(datos.CVS), modelo=modelo or ev.tz.MODELO):
        return ev.tz.en_paralelo(uno, [(cv,) for cv in datos.CVS])


def informe(filas: list[dict]) -> None:
    n = len(filas)
    print(f"{'campo':8} {'exactitud':>10}")
    for k in CAMPOS:
        print(f"{k:8} {sum(f['ok'][k] for f in filas) / n:>10.0%}")
    perfectos = sum(all(f["ok"].values()) for f in filas)
    print(f"Casos con todos los campos bien: {perfectos}/{n}")
    por_tipo = Counter(f["tipo"] for f in filas if not all(f["ok"].values()))
    print(f"Casos con algún fallo, por tipo: {dict(por_tipo) or 'ninguno'}")
    print("\nCada fallo, con lo esperado y lo obtenido (léelos: el número solo no dice qué arreglar):")
    for f in filas:
        for k in CAMPOS:
            if not f["ok"][k]:
                clave = "anios_experiencia" if k == "anios" else k
                print(f"  #{f['id']:<3} {f['tipo']:18} {k:7} esperado {f['esperado'][k]!r:28} "
                      f"obtenido {f['obtenido'][clave]!r}")


if __name__ == "__main__":
    filas = correr("v1")
    informe(filas)
    print(f"\nGuardado en {ev.guardar_jsonl('extractor_v1.jsonl', filas)}")
