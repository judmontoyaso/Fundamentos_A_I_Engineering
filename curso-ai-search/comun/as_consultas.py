"""
as_consultas.py — las consultas de prueba del curso, con su relevancia CALCULADA desde los hechos de cada CV.

Relevancia graduada: 2 = cumple todo lo que pide la consulta · 1 = cumple lo principal (el rol o la tecnología)
pero no un requisito secundario · 0 = no sirve. Como se calcula con código sobre los hechos, no depende de
que nadie lea 119 CVs por consulta, y se puede recalcular si cambian las reglas.
Cada consulta tiene un tipo: es lo que permite ver QUÉ clase de búsqueda falla.
"""
from __future__ import annotations
from typing import Callable

DATOS = {"ingeniero de datos", "científico de datos", "analista de datos"}
BACKEND = {"desarrollador backend", "desarrollador python", "desarrollador .net"}


def _tiene(skill: str) -> Callable[[dict], int]:
    return lambda h: 2 if skill in h["skills"] else 0


def _rol_y(rol: str | set, extra: Callable[[dict], bool]) -> Callable[[dict], int]:
    roles = {rol} if isinstance(rol, str) else rol
    return lambda h: (2 if extra(h) else 1) if h["rol"] in roles else 0


AVANZADO = {"C1", "nativo"}

# (tipo, consulta, relevancia(hechos) -> 0/1/2)
CONSULTAS: list[tuple[str, str, Callable[[dict], int]]] = [
    # tecnología exacta
    ("tecnología", "Kubernetes", _tiene("kubernetes")),
    ("tecnología", "experiencia con Airflow", _tiene("airflow")),
    ("tecnología", "PyTorch", _tiene("pytorch")),
    ("tecnología", "Terraform", _tiene("terraform")),
    ("tecnología", "Selenium", _tiene("selenium")),
    ("tecnología", "Power BI", _tiene("power bi")),
    ("tecnología", "Flutter", _tiene("flutter")),
    ("tecnología", "dbt", _tiene("dbt")),
    # rol dicho tal cual
    ("rol", "científico de datos", _rol_y("científico de datos", lambda h: True)),
    ("rol", "desarrollador frontend", _rol_y("desarrollador frontend", lambda h: True)),
    ("rol", "analista de seguridad", _rol_y("analista de seguridad", lambda h: True)),
    ("rol", "desarrollador móvil", _rol_y("desarrollador móvil", lambda h: True)),
    # paráfrasis: el rol descrito sin nombrarlo
    ("paráfrasis", "alguien que automatice despliegues y administre contenedores",
     lambda h: 2 if h["rol"] == "ingeniero devops" else 1 if h["rol"] == "arquitecto cloud" else 0),
    ("paráfrasis", "persona que construya modelos predictivos con aprendizaje automático",
     _rol_y("científico de datos", lambda h: True)),
    ("paráfrasis", "quien haga pruebas automatizadas de software", _rol_y("qa automation", lambda h: True)),
    ("paráfrasis", "alguien que arme tableros e informes para el negocio", _rol_y("analista de datos", lambda h: True)),
    ("paráfrasis", "quien diseñe la infraestructura en la nube de la empresa",
     lambda h: 2 if h["rol"] == "arquitecto cloud" else 1 if h["rol"] == "ingeniero devops" else 0),
    ("paráfrasis", "persona que proteja los sistemas contra ataques", _rol_y("analista de seguridad", lambda h: True)),
    # rol + nivel
    ("rol + nivel", "ingeniero de datos senior", _rol_y("ingeniero de datos", lambda h: h["nivel"] == "senior")),
    ("rol + nivel", "desarrollador frontend junior", _rol_y("desarrollador frontend", lambda h: h["nivel"] == "junior")),
    ("rol + nivel", "científico de datos semi-senior", _rol_y("científico de datos", lambda h: h["nivel"] == "semi-senior")),
    # rol + ciudad
    ("rol + ciudad", "desarrollador backend en Medellín", _rol_y(BACKEND, lambda h: h["ciudad"] == "Medellín")),
    ("rol + ciudad", "analista de datos en Cali", _rol_y("analista de datos", lambda h: h["ciudad"] == "Cali")),
    ("rol + ciudad", "ingeniero devops que trabaje remoto", _rol_y("ingeniero devops", lambda h: h["remoto"])),
    # rol + idioma
    ("rol + idioma", "analista de datos con inglés avanzado", _rol_y("analista de datos", lambda h: h["ingles"] in AVANZADO)),
    ("rol + idioma", "desarrollador backend con inglés C1 o nativo", _rol_y(BACKEND, lambda h: h["ingles"] in AVANZADO)),
    # numérica
    ("numérica", "más de 8 años de experiencia en desarrollo backend", _rol_y(BACKEND, lambda h: h["anios"] > 8)),
    ("numérica", "científico de datos con al menos 5 años", _rol_y("científico de datos", lambda h: h["anios"] >= 5)),
    ("numérica", "recién egresado de desarrollo", lambda h: 2 if h["anios"] == 0 and "desarrollador" in h["rol"] else 0),
    # certificación
    ("certificación", "certificado AWS Solutions Architect",
     lambda h: 2 if h["certificacion"] == "AWS Solutions Architect" else 1 if h["rol"] == "arquitecto cloud" else 0),
    ("certificación", "ISO 27001 Lead Auditor",
     lambda h: 2 if h["certificacion"] == "ISO 27001 Lead Auditor" else 1 if "iso 27001" in h["skills"] else 0),
    # abreviaturas y erratas
    ("abreviatura", "k8s", _tiene("kubernetes")),
    ("abreviatura", "pyhton django", lambda h: 2 if "django" in h["skills"] else 0),
    ("abreviatura", "dev .NET C#", _rol_y("desarrollador .net", lambda h: True)),
    # en inglés
    ("en inglés", "senior data engineer", _rol_y("ingeniero de datos", lambda h: h["nivel"] == "senior")),
    ("en inglés", "mobile developer", _rol_y("desarrollador móvil", lambda h: True)),
    ("en inglés", "QA engineer with Cypress", lambda h: 2 if "cypress" in h["skills"] else 1 if h["rol"] == "qa automation" else 0),
    # liderazgo
    ("liderazgo", "líder técnico de un equipo de datos", _rol_y(DATOS, lambda h: h["lidera"])),
    ("liderazgo", "quien haya liderado equipos de desarrollo", lambda h: 2 if h["lidera"] and "desarrollador" in h["rol"] else 0),
    # exclusión
    ("exclusión", "desarrollador backend que no use Java", _rol_y(BACKEND, lambda h: "java" not in h["skills"])),
    ("exclusión", "ingeniero de datos sin Spark", _rol_y("ingeniero de datos", lambda h: "spark" not in h["skills"])),
]


def relevancias(cvs: list[dict]) -> list[dict[int, int]]:
    """Para cada consulta, {id_cv: relevancia} solo de los CVs con relevancia > 0."""
    return [{cv["id"]: r for cv in cvs if (r := f(cv["hechos"])) > 0} for _, _, f in CONSULTAS]
