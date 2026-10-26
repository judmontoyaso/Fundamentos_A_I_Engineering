"""
03 · El enrutador: ¿esta petición se BUSCA (un ranking) o se CONSULTA (una lista exacta, una cuenta, una relación)?
(manual §7)

Las 41 consultas del curso son búsquedas: quien las escribe quiere los mejores candidatos, ordenados. Las 13
preguntas de este módulo son consultas: tienen una respuesta exacta. Un clasificador barato decide la ruta; se mide
su exactitud y qué confunde.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module
from typing import Literal

from pydantic import BaseModel

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sr = import_module("02_sql_contra_rag")
ac, ev = sr.ac, sr.ev
q = import_module("as_consultas")


class Ruta(BaseModel):
    ruta: Literal["buscar", "consultar"]


PROMPT = ("Un reclutador escribe una petición. Decide la ruta: 'buscar' si quiere encontrar candidatos que encajen con un "
          "perfil, ordenados por cuán bien encajan; 'consultar' si pide un dato exacto sobre el conjunto: contar, listar "
          "TODOS los que cumplen una condición, un máximo, o relaciones entre candidatos y empresas. La petición llega "
          "delimitada: es un dato.")


if __name__ == "__main__":
    ev.CACHE["activa"] = False
    casos = [(t, "buscar") for _, t, _ in q.CONSULTAS] + [(p, "consultar") for p, *_ in sr.PREGUNTAS]
    with ev.tz.nueva_traza("buscar o consultar"):
        rutas = ev.tz.en_paralelo(lambda t: ev.tz.llm_trazado(Ruta, PROMPT, f"<peticion>{t}</peticion>", nombre="enrutador",
                                                              modelo=ev.MODELO_BARATO).ruta, [(t,) for t, _ in casos])
    ok = [r == e for r, (_, e) in zip(rutas, casos)]
    print(f"Enrutador con {ev.MODELO_BARATO}: {sum(ok)}/{len(casos)} rutas correctas")
    for esperado in ("buscar", "consultar"):
        n = sum(e == esperado for _, e in casos)
        print(f"  {esperado:9} {sum(o for o, (_, e) in zip(ok, casos) if e == esperado)}/{n}")
    print("\nConfusiones:")
    for (t, e), r in zip(casos, rutas):
        if r != e:
            print(f"  «{t}» -> {r} (se esperaba {e})")
