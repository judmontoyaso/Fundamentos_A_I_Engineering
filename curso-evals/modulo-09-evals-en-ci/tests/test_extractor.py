"""
Evals del extractor como tests. Dos clases de test, con reglas distintas:

  CRÍTICOS : casos que no pueden fallar NUNCA (la inyección, el correo que el candidato dice no usar). Un
             fallo bloquea el cambio, sin estadística.
  UMBRAL   : la exactitud por campo sobre los 30 casos no puede bajar de la línea base menos una
             tolerancia. La tolerancia existe porque un caso de 30 son 3 puntos, y el ruido no es una regresión.
"""
from __future__ import annotations
import json
import pathlib
from importlib import import_module

import pytest

ev = import_module("ev_comun")
datos = import_module("ev_datos")
CVS = {cv["id"]: cv for cv in datos.CVS}
LINEA_BASE = pathlib.Path(__file__).resolve().parents[1] / "linea_base.json"
TOLERANCIA = 0.07            # ~2 casos de 30


@pytest.mark.llm
@pytest.mark.parametrize("cv_id,campo", [(22, "anios"), (24, "correo"), (16, "correo"), (25, "anios")])
def test_casos_criticos(cv_id, campo):
    cv = CVS[cv_id]
    assert ev.comparar_ficha(ev.extraer(cv["texto"]), cv["esperado"])[campo], f"#{cv_id} {cv['tipo']}: {campo}"


@pytest.mark.llm
def test_exactitud_no_baja_de_la_linea_base():
    base = json.loads(LINEA_BASE.read_text(encoding="utf-8"))
    res = ev.tz.en_paralelo(lambda cv: ev.comparar_ficha(ev.extraer(cv["texto"]), cv["esperado"]),
                            [(cv,) for cv in datos.CVS])
    for campo, valor_base in base["exactitud"].items():
        actual = sum(r[campo] for r in res) / len(res)
        assert actual >= valor_base - TOLERANCIA, f"{campo}: {actual:.0%} < línea base {valor_base:.0%} - {TOLERANCIA:.0%}"
