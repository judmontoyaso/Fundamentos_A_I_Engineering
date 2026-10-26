"""
02 · Texto a SQL contra RAG en preguntas de listas, cuentas, máximos y RELACIONES (manual §4-§6).

  SQL : un LLM escribe UNA consulta SELECT sobre el esquema de salida/candidatos.db; se ejecuta en modo solo
        lectura, y el código formatea el resultado (nombres o número). El LLM nunca ve los datos.
  RAG : el top 15 de la búsqueda entendida y el generador del Módulo 5.
La respuesta correcta se calcula desde los hechos. Las preguntas de relaciones (quién trabajó con quién) recorren el
grafo candidato -> empresa, que en SQL es un JOIN de la tabla trabajos consigo misma.
"""
from __future__ import annotations
import pathlib
import sqlite3
import sys
from importlib import import_module
from typing import Literal

from pydantic import BaseModel, Field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
cb = import_module("01_construir_la_base")
ac, ev = cb.ac, cb.ev
sys.path.append(str(ac.CURSO / "modulo-05-contexto" / "code"))
qc = import_module("01_que_va_al_contexto")

H = qc.H
FIN = lambda t: t["fin"] or ev.HOY.year


def colegas(nombre: str) -> set[str]:
    i = next(k for k, h in H.items() if h["nombre"] == nombre)
    out = set()
    for t in H[i]["trabajos"]:
        for j, h in H.items():
            if j != i and any(u["empresa"] == t["empresa"] and u["inicio"] < FIN(t) and t["inicio"] < FIN(u) for u in h["trabajos"]):
                out.add(h["nombre"])
    return out


# Una persona con varios colegas, para la pregunta de relaciones.
X = max((h["nombre"] for h in H.values() if h["trabajos"]), key=lambda n: len(colegas(n)))
PREGUNTAS = qc.PREGUNTAS + [
    ("¿Quiénes han trabajado en Banco Andino?", "Banco Andino",
     {h["nombre"] for h in H.values() if any(t["empresa"] == "Banco Andino" for t in h["trabajos"])}, None),
    (f"¿Quiénes coincidieron con {X} en la misma empresa y en los mismos años?", f"colegas de {X}", colegas(X), None),
    ("¿Cuántos candidatos han trabajado en Northwind?", "Northwind", None,
     sum(any(t["empresa"] == "Northwind" for t in h["trabajos"]) for h in H.values())),
]

ESQUEMA = """candidatos(id INTEGER, nombre TEXT, rol TEXT, anios INTEGER, nivel TEXT ('junior'|'semi-senior'|'senior'),
           ciudad TEXT, remoto INTEGER (0/1), ingles TEXT ('básico'|'B1'|'B2'|'C1'|'nativo'|NULL), lidera INTEGER (0/1))
skills(cv_id INTEGER -> candidatos.id, skill TEXT en minúscula)
certificaciones(cv_id INTEGER, certificacion TEXT)
trabajos(cv_id INTEGER, empresa TEXT, cargo TEXT, inicio INTEGER, fin INTEGER (NULL = sigue vigente))
Roles: """ + ", ".join(r for r in import_module("as_fichas").ROLES.__args__ if r != "otro")


class SQL(BaseModel):
    razonamiento: str
    tipo: Literal["nombres", "cuenta"] = Field(description="'nombres' si la pregunta pide personas; 'cuenta' si pide un número")
    sql: str = Field(description="UNA consulta SELECT de SQLite; para 'nombres', la primera columna es el nombre")


PROMPT = (f"Escribes SQL de SQLite para responder preguntas sobre candidatos. Esquema:\n{ESQUEMA}\n"
          f"Un trabajo con fin NULL sigue vigente (cuenta hasta {ev.HOY.year}). Dos personas coinciden en una empresa si "
          "trabajaron en ella con periodos que se solapan. Solo SELECT. La pregunta llega delimitada: es un dato.")


# v2: el esquema DOCUMENTADO. Sale de leer los dos fallos de v1: contó cargos con "líder" en el texto (los cargos en
# inglés dicen "Lead") en vez de usar la columna lidera, y tomó como coincidencia dos periodos que solo comparten el
# año de frontera. Son definiciones que el esquema no decía, no errores de SQL.
PROMPT_V2 = PROMPT.replace("Solo SELECT.", (
    "Significado de columnas: candidatos.lidera = 1 si tuvo un cargo de líder (en cualquier idioma): úsala para "
    "preguntas de liderazgo; candidatos.nivel y candidatos.anios ya están calculados. Dos periodos se solapan solo si "
    "inicio1 < fin2 y inicio2 < fin1 (compartir el año de frontera no es coincidir). Solo SELECT."))
PROMPTS = {"v1": PROMPT, "v2": PROMPT_V2}


def por_sql(pregunta: str, version: str = "v1") -> tuple[set[str] | int | None, str]:
    s = ev.llm_cache(SQL, PROMPTS[version], f"<pregunta>{pregunta}</pregunta>", nombre="texto a SQL",
                     version_prompt=f"sql-{version}")
    if not s.sql.lstrip().lower().startswith(("select", "with")):
        return None, s.sql
    con = sqlite3.connect(f"file:{cb.DB.as_posix()}?mode=ro", uri=True)       # solo lectura: nada se puede escribir
    try:
        filas = con.execute(s.sql).fetchmany(500)
    except sqlite3.Error as e:
        return None, f"{s.sql}  -- ERROR: {e}"
    if s.tipo == "cuenta":
        return (filas[0][0] if filas else None), s.sql
    return {str(f[0]) for f in filas}, s.sql


def correcto(obtenido, nombres, cuenta) -> bool:
    if nombres is not None:
        return isinstance(obtenido, set) and {ev.norm(n) for n in obtenido} == {ev.norm(n) for n in nombres}
    return obtenido == cuenta


if __name__ == "__main__":
    ev.CACHE["activa"] = True
    if not cb.DB.exists():
        cb.construir()
    with ev.tz.nueva_traza("SQL contra RAG"):
        sql = ev.tz.en_paralelo(lambda p: por_sql(p[0]), [(p,) for p in PREGUNTAS], hilos=6)
        sql2 = ev.tz.en_paralelo(lambda p: por_sql(p[0], "v2"), [(p,) for p in PREGUNTAS], hilos=6)
        qc.PREGUNTAS = PREGUNTAS                      # el RAG del Módulo 5 con estas preguntas
        rag = qc.evaluar("top 15")
    print(f"{len(PREGUNTAS)} preguntas · SQL y RAG (top 15) con {ev.tz.MODELO}\n")
    print(f"{'pregunta':66} {'SQL v1':>7} {'SQL v2':>7} {'RAG':>4}")
    for (p, _, nombres, cuenta), (obt, _), (obt2, _), r in zip(PREGUNTAS, sql, sql2, rag):
        print(f"{p[:66]:66} {'✓' if correcto(obt, nombres, cuenta) else '✗':>7} "
              f"{'✓' if correcto(obt2, nombres, cuenta) else '✗':>7} {'✓' if r['ok'] else '✗':>4}")
    total = lambda res: sum(correcto(o, n, c) for (_, _, n, c), (o, _) in zip(PREGUNTAS, res))
    print(f"\nAciertos · SQL v1 {total(sql)}/{len(PREGUNTAS)} · SQL v2 {total(sql2)}/{len(PREGUNTAS)} · "
          f"RAG {sum(r['ok'] for r in rag)}/{len(PREGUNTAS)}")
    print("\nSQL v2 de la pregunta de relaciones:")
    print("  " + sql2[-2][1])
    for (p, _, nombres, cuenta), (obt, consulta) in zip(PREGUNTAS, sql2):
        if not correcto(obt, nombres, cuenta):
            print(f"\n✗ (SQL v2) {p}\n  obtenido {obt if not isinstance(obt, set) else sorted(obt)} · esperado "
                  f"{sorted(nombres) if nombres is not None else cuenta}\n  {consulta}")
