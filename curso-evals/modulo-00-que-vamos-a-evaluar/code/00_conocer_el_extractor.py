"""
00 · Antes de medir, mirar: el set de datos y cinco salidas del extractor (manual §3-§4).

Cuenta los casos por tipo, ejecuta el extractor sobre cinco CVs difíciles y muestra lo que devuelve
al lado de lo esperado. No calcula ninguna métrica: el objetivo es leer.
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
datos = import_module("ev_datos")

MIRAR = [18, 19, 22, 24, 30]      # solapados, hasta hoy, inyección, dos correos, experiencia mixta

if __name__ == "__main__":
    tipos = Counter(cv["tipo"] for cv in datos.CVS)
    print(f"{len(datos.CVS)} CVs · {tipos['típico']} típicos · {len(datos.CVS) - tipos['típico']} difíciles:")
    print("  " + ", ".join(t for t in tipos if t != "típico"))

    casos = [cv for cv in datos.CVS if cv["id"] in MIRAR]
    with ev.tz.nueva_traza("conocer el extractor"):
        fichas = ev.tz.en_paralelo(lambda cv: ev.extraer(cv["texto"]), [(cv,) for cv in casos])
    print(f"\nModelo: {ev.tz.MODELO}")
    for cv, f in zip(casos, fichas):
        e = cv["esperado"]
        print(f"\n#{cv['id']} · {cv['tipo']}\n  CV       : {' '.join(cv['texto'].split())}")
        print(f"  esperado : {e['nombre']} · {e['correo']} · {e['anios']} años · {e['skills']}")
        print(f"  obtenido : {f.nombre} · {f.correo} · {f.anios_experiencia} años · {f.skills}")
    print("\nAntes de seguir: ¿en cuáles coincide? Si alguno no coincide, ¿el error es del extractor o de la")
    print("etiqueta? Escribe tu respuesta: es el primer paso del error analysis (Módulo 2).")
