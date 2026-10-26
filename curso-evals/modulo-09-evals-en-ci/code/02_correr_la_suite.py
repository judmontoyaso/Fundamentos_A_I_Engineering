"""
02 · Correr la suite como la correría el CI: primero lo gratis, después lo que cuesta (manual §2, §5).

Equivale a, desde la carpeta del módulo:
    pytest tests -m "not llm" -q      (en cada commit: sin llamadas, en segundos)
    pytest tests -q                   (en cada pull request: con la caché, los llm cuestan solo lo nuevo)
"""
from __future__ import annotations
import contextlib
import io
import pathlib

import pytest

TESTS = pathlib.Path(__file__).resolve().parents[1] / "tests"


def correr(*args: str) -> int:
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        codigo = pytest.main([str(TESTS), "-q", "-p", "no:cacheprovider", *args])
    lineas = [l for l in salida.getvalue().splitlines() if l.strip()]
    print("\n".join(lineas[-12:]))
    return int(codigo)


if __name__ == "__main__":
    print("== Tests sin LLM ==")
    c1 = correr("-m", "not llm")
    print("\n== Todos (con caché) ==")
    c2 = correr()
    print(f"\nCódigos de salida: {c1} y {c2} (0 = todo pasa; el CI bloquea el cambio con cualquier otro).")
