"""
Evaluación de referencia del proyecto final. NO la abras antes de terminar tu evaluación.

Etiquetas de las 10 ofertas con reglas escritas antes de ejecutar:
  - nivel: el que la oferta dice ("junior", "senior", "líder técnico" = senior, "practicante" = junior); si no lo
    dice, "no indicado" (no se infiere de los años).
  - anios_minimos: el mínimo que pide; en un rango ("3 a 5"), el menor.
  - salario_mensual_cop: el mensual en pesos; en un rango, el menor; None si no aparece.
  - skills: las requeridas y las deseables, tal como aparecen (cada esperada debe estar dentro de alguna extraída).
Corre con: python evaluacion_de_referencia.py   (desde esta carpeta, con el .env de la app cargado)
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter
from importlib import import_module

COMUN = pathlib.Path(__file__).resolve().parents[2] / "comun"
sys.path.append(str(COMUN))
try:
    from dotenv import load_dotenv
    load_dotenv(COMUN.parents[1] / "app" / "backend" / ".env")
except ImportError:
    pass
sis = import_module("m12_vacantes")
ev = sis.ev

E = [
    dict(nivel="senior", anios=5, req=["python", "spark", "airflow"], des=["kafka"], modalidad="híbrido", ciudad="bogota", salario=12_000_000),
    dict(nivel="semi-senior", anios=3, req=["java", "spring boot"], des=["docker", "kubernetes"], modalidad="remoto", ciudad=None, salario=None),
    dict(nivel="junior", anios=1, req=["power bi", "sql"], des=[], modalidad="presencial", ciudad="medellin", salario=3_500_000),
    dict(nivel="no indicado", anios=2, req=["python", "scikit-learn", "estadistica"], des=["pytorch"], modalidad="híbrido", ciudad="cali", salario=None),
    dict(nivel="senior", anios=8, req=["aws", "terraform"], des=["gcp"], modalidad="remoto", ciudad=None, salario=18_000_000),
    dict(nivel="junior", anios=0, req=["html", "css", "javascript"], des=[], modalidad="presencial", ciudad="barranquilla", salario=None),
    dict(nivel="semi-senior", anios=3, req=["selenium", "cypress"], des=[], modalidad="híbrido", ciudad="bogota", salario=6_500_000),
    dict(nivel="senior", anios=7, req=["c#", ".net"], des=["azure"], modalidad="remoto", ciudad=None, salario=15_000_000),
    dict(nivel="no indicado", anios=4, req=["iso 27001"], des=[], modalidad="presencial", ciudad="bogota", salario=None),
    dict(nivel="no indicado", anios=5, req=[], des=["sql", "tableau"], modalidad="híbrido", ciudad="medellin", salario=None),
]


def comparar(v, e) -> dict[str, bool]:
    contiene = lambda esperadas, obtenidas: all(any(ev.norm(x) in ev.norm(o) for o in obtenidas) for x in esperadas)
    return {"nivel": v.nivel == e["nivel"], "anios": v.anios_minimos == e["anios"],
            "skills requeridas": contiene(e["req"], v.skills_requeridas),
            "skills deseables": contiene(e["des"], v.skills_deseables),
            "modalidad": v.modalidad == e["modalidad"], "ciudad": (ev.norm(v.ciudad) if v.ciudad else None) == e["ciudad"],
            "salario": v.salario_mensual_cop == e["salario"]}


if __name__ == "__main__":
    ev.CACHE["activa"] = False
    fallos = Counter()
    for vez in range(2):
        res = ev.tz.en_paralelo(lambda t: sis.extraer_vacante(t), [(t,) for t in sis.OFERTAS])
        for i, (v, e) in enumerate(zip(res, E), 1):
            for campo, ok in comparar(v, e).items():
                if not ok:
                    fallos[(i, campo, str(getattr(v, {"anios": "anios_minimos", "salario": "salario_mensual_cop",
                                                       "skills requeridas": "skills_requeridas",
                                                       "skills deseables": "skills_deseables"}.get(campo, campo))))] += 1
    por_campo = Counter(c for (_, c, _), n in fallos.items() for _ in range(n))
    print("Fallos por campo (10 ofertas × 2 corridas = 20 extracciones):", dict(por_campo))
    for (i, campo, valor), n in sorted(fallos.items()):
        print(f"  oferta {i:>2} · {campo:18} {n}/2 · obtenido {valor[:70]!r} · esperado {E[i - 1][{'skills requeridas': 'req', 'skills deseables': 'des'}.get(campo, campo)]!r}")
