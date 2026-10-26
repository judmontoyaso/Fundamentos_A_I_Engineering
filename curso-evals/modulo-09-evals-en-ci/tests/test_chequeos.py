"""
Tests del CÓDIGO de los evals, sin LLM. Un chequeo con un bug da resultados falsos con total
seguridad: estos tests son lo primero que corre en cada cambio, y no cuestan nada.
"""
from __future__ import annotations
import math
import sys
from importlib import import_module

import pytest

ev = import_module("ev_comun")
sys.path.append(str(ev.CURSO / "modulo-02-error-analysis" / "code"))
sys.path.append(str(ev.CURSO / "modulo-05-llm-juez" / "code"))


def ficha(**kw):
    base = {"nombre": "Laura Gómez", "correo": "laura.gomez@mail.com", "anios_experiencia": 9,
            "skills": ["kafka", "python 3.12"]}
    return ev.FichaCV(**{**base, **kw})


ESPERADO = {"nombre": "Laura Gómez", "correo": "laura.gomez@mail.com", "anios": 9, "skills": ["kafka", "python"]}


def test_skill_dentro_de_otra_cuenta():
    assert ev.comparar_ficha(ficha(), ESPERADO)["skills"]


def test_net_sin_punto_es_fallo():
    """Decisión del Módulo 1 §5: 'net' no vale por '.net'. Si alguien relaja el chequeo, este test avisa."""
    r = ev.comparar_ficha(ficha(skills=["c#", "net"]), {**ESPERADO, "skills": [".net"]})
    assert not r["skills"]


def test_nombre_sin_tildes_ni_mayusculas():
    assert ev.comparar_ficha(ficha(nombre="LAURA GOMEZ"), ESPERADO)["nombre"]


def test_correo_ausente():
    assert ev.comparar_ficha(ficha(correo=None), {**ESPERADO, "correo": None})["correo"]
    assert not ev.comparar_ficha(ficha(correo="inventado@mail.com"), {**ESPERADO, "correo": None})["correo"]


def test_kappa_perfecto_y_paradoja():
    assert ev.kappa([True, False] * 10, [True, False] * 10) == 1
    a = [True] * 90 + [True] * 5 + [False] * 5
    b = [True] * 90 + [False] * 5 + [True] * 5
    assert ev.kappa(a, b) < 0          # 90 % de acuerdo y ningún fallo en común (Módulo 4 §4)


@pytest.mark.parametrize("texto,hay", [
    ("Contacto: ricardo.salas@mail.com.", True),
    ("Contacto inicial a través de LinkedIn.", True),
    ("Analista de procesos (2016-2024).", False),
    ("Ingeniera de datos con 9 años de experiencia.", False),
])
def test_regex_de_contacto(texto, hay):
    fe = import_module("04_de_fallos_a_evals")
    assert bool(fe.CONTACTO.search(texto)) is hay


def test_rogan_gladen():
    tc = import_module("04_tasa_corregida")
    assert math.isclose(tc.corregir(0.30, 0.90, 0.80), 0.10 / 0.70)
    assert tc.corregir(0.30, 0.90, 0.55) == 0.0          # recortado: el juez no distingue nada
