"""
01 · Una base relacional desde el índice: candidatos, skills, certificaciones y trabajos con su EMPRESA (manual §2-§3).

Las fichas del Módulo 2 no guardaban ni el nombre ni la empresa de cada trabajo: para buscar no hacían falta. Para
preguntas de RELACIONES ("¿quién trabajó con quién?") sí. Se extraen del texto (el mismo extractor, con caché) y
se cargan, junto con las fichas, en salida/candidatos.db:
  candidatos(id, nombre, rol, anios, nivel, ciudad, remoto, ingles, lidera)
  skills(cv_id, skill) · certificaciones(cv_id, certificacion)
  trabajos(cv_id, empresa, cargo, inicio, fin)      -- fin NULL = sigue vigente
Las tablas trabajos + candidatos forman un GRAFO: candidato -[trabajó en, años]-> empresa.
"""
from __future__ import annotations
import pathlib
import sqlite3
import sys
from importlib import import_module

from pydantic import BaseModel, Field

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
fx = import_module("as_fichas")
ev = ac.ev
DB = ac.SALIDA / "candidatos.db"


class TrabajoEmpresa(BaseModel):
    empresa: str
    cargo: str
    inicio: int | None = None
    fin: int | None = Field(default=None, description="null si sigue vigente")


class Relaciones(BaseModel):
    nombre: str
    trabajos: list[TrabajoEmpresa]


PROMPT = (f"Extrae el nombre del candidato y cada trabajo con su empresa, cargo y años tal como aparecen. "
          f"{ev.c.INSTRUCCION_CV} No inventes.")


def construir() -> sqlite3.Connection:
    ev.CACHE["activa"] = True
    cvs = ac.cvs()
    with ev.tz.nueva_traza("relaciones para la base"):
        rel = ev.tz.en_paralelo(lambda cv: ev.llm_cache(Relaciones, PROMPT, ev.c.como_cv(cv["texto"]), nombre="relaciones"),
                                [(cv,) for cv in cvs], hilos=12)
    fichas = fx.fichas()
    DB.parent.mkdir(exist_ok=True)
    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE candidatos (id INTEGER PRIMARY KEY, nombre TEXT, rol TEXT, anios INTEGER, nivel TEXT, ciudad TEXT,
                                 remoto INTEGER, ingles TEXT, lidera INTEGER);
        CREATE TABLE skills (cv_id INTEGER, skill TEXT);
        CREATE TABLE certificaciones (cv_id INTEGER, certificacion TEXT);
        CREATE TABLE trabajos (cv_id INTEGER, empresa TEXT, cargo TEXT, inicio INTEGER, fin INTEGER);""")
    for cv, r in zip(cvs, rel):
        f = fichas[cv["id"]]
        con.execute("INSERT INTO candidatos VALUES (?,?,?,?,?,?,?,?,?)",
                    (cv["id"], r.nombre, f["rol"], f["anios"], f["nivel"], f["ciudad"], int(f["remoto"]), f["ingles"],
                     int(f["lidera"])))
        con.executemany("INSERT INTO skills VALUES (?,?)", [(cv["id"], s.lower()) for s in f["skills"]])
        con.executemany("INSERT INTO certificaciones VALUES (?,?)", [(cv["id"], c) for c in f["certificaciones"]])
        con.executemany("INSERT INTO trabajos VALUES (?,?,?,?,?)",
                        [(cv["id"], t.empresa, t.cargo, t.inicio, t.fin) for t in r.trabajos])
    con.commit()
    return con


if __name__ == "__main__":
    con = construir()
    for tabla in ("candidatos", "skills", "certificaciones", "trabajos"):
        print(f"{tabla:16} {con.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]:>4} filas")
    print("\nEl grafo candidato -> empresa, visto como tabla (empresas con más candidatos):")
    for fila in con.execute("SELECT empresa, COUNT(DISTINCT cv_id) n FROM trabajos GROUP BY empresa ORDER BY n DESC LIMIT 5"):
        print("  ", fila)
    hechos = {cv["id"]: cv["hechos"] for cv in ac.cvs()}
    ok = sum(sorted((t["empresa"], t["inicio"]) for t in hechos[i]["trabajos"]) ==
             sorted(con.execute("SELECT empresa, inicio FROM trabajos WHERE cv_id=?", (i,)).fetchall()) for i in hechos)
    print(f"\nTrabajos (empresa e inicio) extraídos igual que en los hechos: {ok}/{len(hechos)} CVs")
