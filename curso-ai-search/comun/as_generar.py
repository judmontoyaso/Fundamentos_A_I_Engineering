"""
as_generar.py — genera los 120 CVs del curso DESDE LOS HECHOS (curso de Evals, Módulo 3) y los guarda en as_cvs.json.

Se corrió una vez para crear el archivo del repositorio; no hace falta volver a correrlo. Pasos:
  1. hechos en código (semilla fija): rol, skills, trabajos con años, ciudad, inglés, certificaciones;
  2. un LLM redacta el CV con un estilo (prosa, lista o tabla; algunos en inglés);
  3. se valida con código que el texto tenga los hechos; si no, se regenera (hasta 3 intentos) y, si sigue
     sin pasar, se descarta y se informa.
Uso: python as_generar.py   (con el .env de la app cargado)
"""
from __future__ import annotations
import json
import random
import re
import sys
from importlib import import_module

from pydantic import BaseModel

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
ac = import_module("as_comun")
ev = ac.ev

ROLES = {
    "ingeniero de datos": (["python", "spark", "airflow", "sql"], ["kafka", "dbt", "snowflake", "aws", "databricks"]),
    "científico de datos": (["python", "scikit-learn", "sql"], ["pytorch", "tensorflow", "mlflow", "estadística"]),
    "analista de datos": (["sql", "power bi"], ["tableau", "excel", "python"]),
    "desarrollador backend": (["java", "spring"], ["postgresql", "docker", "kafka", "microservicios"]),
    "desarrollador python": (["python", "django"], ["fastapi", "postgresql", "docker", "celery"]),
    "desarrollador frontend": (["javascript", "react"], ["typescript", "angular", "vue", "css"]),
    "ingeniero devops": (["kubernetes", "docker", "linux"], ["terraform", "jenkins", "ansible", "aws"]),
    "arquitecto cloud": (["aws", "terraform"], ["azure", "gcp", "kubernetes"]),
    "qa automation": (["selenium", "cypress"], ["java", "playwright", "jmeter"]),
    "desarrollador móvil": (["kotlin", "swift"], ["flutter", "firebase"]),
    "analista de seguridad": (["iso 27001", "siem"], ["pentesting", "nist", "firewall"]),
    "desarrollador .net": (["c#", ".net"], ["sql server", "azure"]),
}
CERTIFICACIONES = {"arquitecto cloud": "AWS Solutions Architect", "ingeniero devops": "CKA (Kubernetes)",
                   "analista de seguridad": "ISO 27001 Lead Auditor", "científico de datos": "TensorFlow Developer",
                   "desarrollador .net": "Microsoft Azure Developer"}
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga"]
INGLES = [None, "básico", "B1", "B2", "C1", "nativo"]
NOMBRES = ["Ana", "Carlos", "Laura", "Andrés", "Sofía", "Diego", "Valentina", "Camilo", "Paula", "Mateo", "Natalia",
           "Felipe", "Isabel", "Tomás", "Daniela", "Julián", "Mariana", "Santiago", "Lucía", "Esteban"]
APELLIDOS = ["Gómez", "Ruiz", "Martínez", "Rojas", "Castro", "Mejía", "Ortiz", "Vélez", "Salas", "Herrera", "Pardo",
             "León", "Torres", "Cruz", "Duarte", "Ramos", "Giraldo", "Peña", "Lozano", "Arango"]
EMPRESAS = ["Globex", "Initech", "Northwind", "DataSur", "RetailCo", "Banco Andino", "NubeSur", "SoftContable",
            "Insight Labs", "Manufacturas del Valle", "TransLogística", "AgroTech", "SaludPlus", "EduNet"]
ESTILOS = ["prosa", "lista", "tabla"]


def hechos(i: int, rnd: random.Random) -> dict:
    rol = list(ROLES)[i % len(ROLES)]
    nucleo, extra = ROLES[rol]
    skills = nucleo[: rnd.randint(1, len(nucleo))] + rnd.sample(extra, rnd.randint(1, min(3, len(extra))))
    anios = rnd.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14])
    trabajos, fin = [], ev.HOY.year
    restante = anios
    while restante > 0:
        dur = min(restante, rnd.randint(2, 5))
        trabajos.append({"empresa": rnd.choice(EMPRESAS), "cargo": rol, "inicio": fin - dur,
                         "fin": None if fin == ev.HOY.year else fin})
        fin -= dur
        restante -= dur
    nivel = "senior" if anios >= 7 else "semi-senior" if anios >= 3 else "junior"
    if anios >= 5 and rnd.random() < 0.25:
        trabajos[0]["cargo"] = f"líder de {rol}"
    nombre = f"{NOMBRES[i % 20]} {APELLIDOS[(i * 7 + i // 20) % 20]}"
    return {"nombre": nombre, "rol": rol, "skills": skills, "anios": anios, "nivel": nivel,
            "trabajos": trabajos, "ciudad": rnd.choice(CIUDADES), "remoto": rnd.random() < 0.3,
            "ingles": rnd.choice(INGLES),
            "certificacion": CERTIFICACIONES.get(rol) if rnd.random() < 0.35 else None,
            "lidera": trabajos[0]["cargo"].startswith("líder") if trabajos else False,
            "estilo": ESTILOS[i % 3], "idioma": "inglés" if i % 7 == 3 else "español"}


class Texto(BaseModel):
    texto: str


PROMPT = ("Escribes CVs ficticios y realistas. Usa EXACTAMENTE estos hechos: nombre, rol, cada trabajo con su empresa y "
          "sus años (fin null = 'actualidad'), las tecnologías, la ciudad, si acepta trabajo remoto, el nivel de inglés y "
          "la certificación si hay. No añadas otras tecnologías, empresas ni años, y no escribas el total de años. "
          "Si no tiene experiencia (sin trabajos), di que es recién egresado. Máximo 110 palabras.")


def valido(f: dict, texto: str) -> list[str]:
    t, p = ev.norm(texto), []
    if not all(ev.norm(x) in t for x in f["nombre"].split()):
        p.append("nombre")
    if not all(ev.norm(s) in t for s in f["skills"]):
        p.append("skills")
    for tr in f["trabajos"]:
        if str(tr["inicio"]) not in t or (tr["fin"] and str(tr["fin"]) not in t):
            p.append("años")
    if ev.norm(f["ciudad"]) not in t:
        p.append("ciudad")
    if f["certificacion"] and ev.norm(f["certificacion"].split(" (")[0]) not in t:
        p.append("certificación")
    return p


def generar(f: dict) -> str | None:
    estilo = {"prosa": "un párrafo", "lista": "viñetas", "tabla": "los trabajos en una tabla de texto con '|'"}[f["estilo"]]
    datos = {k: f[k] for k in ("nombre", "rol", "skills", "trabajos", "ciudad", "remoto", "ingles", "certificacion")}
    for _ in range(3):
        r = ev.tz.llm_trazado(Texto, PROMPT, f"Hechos: {json.dumps(datos, ensure_ascii=False)}\nFormato: {estilo}. "
                                             f"Idioma: {f['idioma']}.", nombre="generar CV")
        if not valido(f, r.texto):
            return r.texto
    print(f"  rechazado tras 3 intentos: {f['nombre']} ({f['rol']}, {f['idioma']}): {valido(f, r.texto)}")
    return None


if __name__ == "__main__":
    rnd = random.Random(2026)
    fs = [hechos(i, rnd) for i in range(120)]
    with ev.tz.nueva_traza("generar corpus AI search"):
        textos = ev.tz.en_paralelo(generar, [(f,) for f in fs])
    validos = [(f, t) for f, t in zip(fs, textos) if t]
    filas = [{"id": i + 1, "texto": t, "hechos": f} for i, (f, t) in enumerate(validos)]
    (ac.COMUN / "as_cvs.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(filas)} CVs válidos de {len(fs)} guardados en as_cvs.json")
