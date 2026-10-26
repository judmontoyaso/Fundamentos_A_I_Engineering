"""
Configuración de la suite: rutas a comun/, el .env de la app y la marca `llm`.

  pytest -m "not llm"   -> solo los tests sin llamadas al modelo (gratis, en cada commit)
  pytest                -> todos; los `llm` se saltan si no hay OPENAI_API_KEY
Por defecto activa la caché de llamadas (EVALS_CACHE=1): una llamada idéntica no se vuelve a pagar.
"""
from __future__ import annotations
import os
import pathlib
import sys

import pytest

CURSO = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(CURSO / "comun"))
os.environ.setdefault("EVALS_CACHE", "1")
try:
    from dotenv import load_dotenv
    load_dotenv(CURSO.parent / "app" / "backend" / ".env")
except ImportError:
    pass


def pytest_configure(config):
    config.addinivalue_line("markers", "llm: hace llamadas al modelo (cuestan; se saltan sin OPENAI_API_KEY)")


def pytest_collection_modifyitems(config, items):
    if os.getenv("OPENAI_API_KEY"):
        return
    saltar = pytest.mark.skip(reason="sin OPENAI_API_KEY")
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(saltar)
