"""
as_vacantes.py — las 30 vacantes del proyecto final, generadas DESDE LOS HECHOS, y su relevancia contra los CVs.

Cada vacante sale de un CV ancla (así siempre hay al menos un candidato que la cumple):
  rol del ancla · 2-3 skills REQUERIDAS que el ancla tiene · 1-2 DESEABLES del rol · años mínimos ≤ los del ancla ·
  modalidad (remoto, o presencial/híbrido en una ciudad) · a veces inglés B2 o más · un cliente de la agencia.
Un LLM la redacta con un estilo (formal con párrafo de la empresa, informal, lista, larga con beneficios, en inglés)
y el código valida que el texto tenga los hechos; si no, se regenera (hasta 3 intentos).

Relevancia de un CV para una vacante (calculada con código):
  2 = mismo rol, todas las requeridas, años suficientes, ubicación compatible e inglés suficiente
  1 = mismo rol, pero falla alguno de los otros requisitos
  0 = otro rol
Las deseables NO cuentan para la relevancia: son un plus, no un requisito.
Uso: python as_vacantes.py   (genera as_vacantes.json; ya está en el repositorio, no hace falta correrlo)
"""
from __future__ import annotations
import json
import random
import sys
from functools import lru_cache
from importlib import import_module

from pydantic import BaseModel

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
ac = import_module("as_comun")
gen = import_module("as_generar")
ev = ac.ev

ARCHIVO = ac.COMUN / "as_vacantes.json"
CLIENTES = ["Finanzas Cóndor", "Retail Pacífico", "Salud Orquídea"]
ESTILOS = ["formal, con un párrafo largo sobre la empresa antes de los requisitos",
           "informal y cercano, como un post en redes",
           "lista de requisitos y lista de deseables, corta",
           "larga, con responsabilidades, beneficios y proceso de selección además de los requisitos",
           "en inglés, formal"]
ORDEN_INGLES = {None: 0, "básico": 1, "B1": 2, "B2": 3, "C1": 4, "nativo": 5}


def hechos_vacante(j: int, cvs: list[dict]) -> dict:
    rnd = random.Random(500 + j)
    ancla = rnd.choice([cv for cv in cvs if cv["hechos"]["anios"] >= 1])["hechos"]
    rol = ancla["rol"]
    requeridas = rnd.sample(ancla["skills"], min(len(ancla["skills"]), rnd.choice([2, 2, 3])))
    otras = [s for s in sum(gen.ROLES[rol], []) if s not in requeridas]
    deseables = rnd.sample(otras, min(len(otras), rnd.choice([1, 2])))
    anios_min = max(x for x in (0, 1, 2, 3, 5, 7) if x <= ancla["anios"])
    remoto = ancla["remoto"] and rnd.random() < 0.6
    return {"id": j + 1, "cliente": CLIENTES[j % 3], "rol": rol, "requeridas": requeridas, "deseables": deseables,
            "anios_min": anios_min, "rango_anios": anios_min >= 2 and rnd.random() < 0.3,
            "modalidad": "remoto" if remoto else rnd.choice(["presencial", "híbrido"]),
            "ciudad": None if remoto else ancla["ciudad"],
            "ingles_min": "B2" if ORDEN_INGLES[ancla["ingles"]] >= 3 and rnd.random() < 0.4 else None,
            "estilo": ESTILOS[j % len(ESTILOS)], "ancla": ancla["nombre"]}


def relevancia(v: dict, h: dict) -> int:
    if h["rol"] != v["rol"]:
        return 0
    cumple = (all(s in h["skills"] for s in v["requeridas"]) and h["anios"] >= v["anios_min"]
              and (v["modalidad"] == "remoto" or h["ciudad"] == v["ciudad"])
              and (v["ingles_min"] is None or ORDEN_INGLES[h["ingles"]] >= ORDEN_INGLES[v["ingles_min"]]))
    return 2 if cumple else 1


@lru_cache(maxsize=1)
def vacantes() -> list[dict]:
    return json.loads(ARCHIVO.read_text(encoding="utf-8"))


def relevancias(cvs: list[dict]) -> list[dict[int, int]]:
    return [{cv["id"]: r for cv in cvs if (r := relevancia(v["hechos"], cv["hechos"])) > 0} for v in vacantes()]


# ---------- generación (se corrió una vez) ----------
class Texto(BaseModel):
    texto: str


PROMPT = ("Redactas ofertas de empleo realistas para una agencia de selección en Colombia, a partir de unos hechos. "
          "Incluye TODOS los requisitos de los hechos, sin inventar requisitos obligatorios nuevos. Las skills deseables "
          "tienen que quedar claramente como deseables (deseable, es un plus, nice to have). Escribe los años de "
          "experiencia con número. No nombres al cliente: la agencia publica la oferta. Sigue el estilo pedido.")


def _valida(texto: str, v: dict) -> list[str]:
    t = ev.norm(texto)
    faltan = [s for s in v["requeridas"] + v["deseables"] if ev.norm(s) not in t]
    if v["anios_min"] and str(v["anios_min"]) not in t:
        faltan.append(f"{v['anios_min']} años")
    if v["ciudad"] and ev.norm(v["ciudad"]) not in t:
        faltan.append(v["ciudad"])
    if v["ingles_min"] and "b2" not in t:
        faltan.append("inglés B2")
    return faltan


def generar() -> None:
    cvs = ac.cvs()
    salida = []
    for j in range(30):
        v = hechos_vacante(j, cvs)
        pedido = {k: v[k] for k in ("rol", "requeridas", "deseables", "anios_min", "modalidad", "ciudad", "ingles_min")}
        if v["rango_anios"]:
            pedido["anios"] = f"rango de {v['anios_min']} a {v['anios_min'] + 3} años"
        for intento in range(3):
            texto = ev.tz.llm_trazado(Texto, PROMPT, f"Estilo: {v['estilo']}\nHechos: {json.dumps(pedido, ensure_ascii=False)}",
                                      nombre="generar vacante").texto
            faltan = _valida(texto, v)
            if not faltan:
                break
        if faltan:
            print(f"vacante {v['id']}: descartada, le faltan {faltan}")
            continue
        salida.append({"id": v["id"], "texto": texto, "hechos": v})
    ARCHIVO.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(salida)} vacantes en {ARCHIVO.name}")


if __name__ == "__main__":
    generar()
