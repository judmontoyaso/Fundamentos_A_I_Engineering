"""
00 · Un trazador mínimo, sobre SQLite y sin servicios externos (manual §2-§4).

- span(nombre, **atributos): context manager que mide una operación y la cuelga de
  la que la contiene (contextvars). Registra estado ok/error.
- nueva_traza(nombre): abre una traza nueva (un pedido).
- llm_trazado(...): llamada con salida estructurada (Instructor, JSON_SCHEMA) que
  registra modelo, tokens (entrada, salida, razonamiento, caché) y latencia.
- enmascarar(): quita correos y teléfonos antes de guardar (los CVs son datos personales).
- arbol(trace_id): imprime la traza como árbol.

Las demás celdas del módulo lo importan: ejecútalo primero.
"""
from __future__ import annotations
import contextvars
import json
import os
import re
import sqlite3
import sys
import time
import uuid
import pathlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import lru_cache
from importlib import import_module

import instructor
from instructor.core import InstructorRetryException
from openai import OpenAI

RAIZ = pathlib.Path(__file__).resolve().parents[2]
for carpeta in (RAIZ / "modulo-05-workflows-agentes" / "code",):
    if str(carpeta) not in sys.path:
        sys.path.append(str(carpeta))

MODELO = os.getenv("MODELO", "gpt-4.1-mini")
DB = pathlib.Path(os.getenv("TRAZAS_DB") or RAIZ / "app" / "backend" / "data" / "trazas.db")

_traza: contextvars.ContextVar[str | None] = contextvars.ContextVar("traza", default=None)
_padre: contextvars.ContextVar[str | None] = contextvars.ContextVar("padre", default=None)


def _con() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS spans (
        span_id TEXT PRIMARY KEY, trace_id TEXT, parent_id TEXT, nombre TEXT,
        inicio REAL, fin REAL, estado TEXT, error TEXT, atributos TEXT)""")
    return con


# ---------- Datos personales fuera de las trazas ----------
_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_TELEFONO = re.compile(r"\+?\d[\d\s-]{6,}\d")


def enmascarar(texto: str, maximo: int = 300) -> str:
    t = _TELEFONO.sub("[teléfono]", _CORREO.sub("[correo]", str(texto)))
    return t if len(t) <= maximo else t[:maximo] + "…"


# ---------- Spans ----------
class Span:
    def __init__(self, nombre: str, atributos: dict):
        self.nombre, self.atributos = nombre, atributos


@contextmanager
def span(nombre: str, **atributos):
    trace_id = _traza.get() or uuid.uuid4().hex[:8]
    span_id, padre = uuid.uuid4().hex[:8], _padre.get()
    t_traza, t_padre = _traza.set(trace_id), _padre.set(span_id)
    s, inicio, estado, error = Span(nombre, atributos), time.time(), "ok", None
    try:
        yield s
    except Exception as e:
        primera = next((l.strip() for l in str(e).splitlines() if l.strip() and not l.strip().startswith("<")), "")
        estado, error = "error", f"{type(e).__name__}: {enmascarar(primera, 120)}"
        raise
    finally:
        _padre.reset(t_padre)
        _traza.reset(t_traza)
        with _con() as con:
            con.execute("INSERT INTO spans VALUES (?,?,?,?,?,?,?,?,?)",
                        (span_id, trace_id, padre, nombre, inicio, time.time(), estado, error,
                         json.dumps(s.atributos, ensure_ascii=False, default=str)))


@contextmanager
def nueva_traza(nombre: str, **atributos):
    """Un pedido = una traza nueva, aunque se abra dentro de otra."""
    t1, t2 = _traza.set(uuid.uuid4().hex[:8]), _padre.set(None)
    try:
        with span(nombre, **atributos) as s:
            s.trace_id = _traza.get()
            yield s
    finally:
        _padre.reset(t2)
        _traza.reset(t1)


def en_paralelo(fn, argumentos: list, hilos: int = 8) -> list:
    """Ejecuta fn(*args) en hilos conservando la traza actual (cada hilo copia el contexto)."""
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        futuros = [ex.submit(contextvars.copy_context().run, fn, *a) for a in argumentos]
        return [f.result() for f in futuros]


# ---------- Llamadas al LLM trazadas ----------
@lru_cache(maxsize=1)
def _cliente():
    return instructor.from_openai(OpenAI(), mode=instructor.Mode.JSON_SCHEMA)


def _uso(u) -> dict:
    return {"tokens_entrada": u.prompt_tokens,
            "tokens_salida": u.completion_tokens,
            "tokens_razonamiento": getattr(u.completion_tokens_details, "reasoning_tokens", 0) or 0,
            "tokens_cache": getattr(u.prompt_tokens_details, "cached_tokens", 0) or 0}


def llm_trazado(response_model, system: str, user: str, nombre: str = "llm",
                version_prompt: str | None = None, max_retries: int = 2):
    with span(nombre, tipo="llm", version_prompt=version_prompt, modelo_pedido=MODELO,
              entrada=enmascarar(user)) as s:
        try:
            obj, comp = _cliente().chat.completions.create_with_completion(
                model=MODELO, response_model=response_model, max_retries=max_retries,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        except InstructorRetryException as e:
            # Un fallo también se paga: registra los intentos y los tokens de TODOS ellos.
            s.atributos["intentos"] = e.n_attempts
            if e.total_usage is not None:
                s.atributos.update(_uso(e.total_usage))
            raise
        s.atributos.update(modelo=comp.model, salida=enmascarar(obj.model_dump_json()), **_uso(comp.usage))
        return obj


# ---------- Consultas ----------
def spans(trace_id: str | None = None) -> list[dict]:
    with _con() as con:
        con.row_factory = sqlite3.Row
        filas = con.execute("SELECT * FROM spans" + (" WHERE trace_id=?" if trace_id else "")
                            + " ORDER BY inicio", (trace_id,) if trace_id else ()).fetchall()
    return [{**dict(f), "atributos": json.loads(f["atributos"]), "seg": f["fin"] - f["inicio"]} for f in filas]


def arbol(trace_id: str) -> str:
    filas = spans(trace_id)
    hijos: dict = {}
    for f in filas:
        hijos.setdefault(f["parent_id"], []).append(f)
    lineas = []

    def pintar(padre, prefijo):
        nodos = hijos.get(padre, [])
        for i, f in enumerate(nodos):
            ultimo = i == len(nodos) - 1
            a = f["atributos"]
            extra = ""
            if a.get("tipo") == "llm" and "tokens_entrada" in a:
                extra = (f"  llm · {a['tokens_entrada']} entrada · {a['tokens_salida']} salida "
                         f"({a['tokens_razonamiento']} razonamiento)")
                if a.get("intentos"):
                    extra += f" · {a['intentos']} intentos"
            marca = "" if f["estado"] == "ok" else f"  ✗ {f['error']}"
            rama = "" if padre is None else ("└─ " if ultimo else "├─ ")
            lineas.append(f"{prefijo}{rama}{f['nombre']:<22} {f['seg']:5.1f} s{extra}{marca}")
            pintar(f["span_id"], prefijo + ("" if padre is None else ("   " if ultimo else "│  ")))

    pintar(None, "")
    return "\n".join(lineas)


def costo_usd(tokens_entrada: int, tokens_salida: int, tokens_cache: int = 0) -> float | None:
    """Solo si definiste los precios de tu cuenta en .env (USD por millón de tokens)."""
    try:
        pin = float(os.environ["PRECIO_ENTRADA_USD_1M"])
        pout = float(os.environ["PRECIO_SALIDA_USD_1M"])
    except (KeyError, ValueError):
        return None
    pcache = float(os.getenv("PRECIO_CACHE_USD_1M", pin))
    return ((tokens_entrada - tokens_cache) * pin + tokens_cache * pcache + tokens_salida * pout) / 1e6


def borrar_trazas():
    with _con() as con:
        con.execute("DELETE FROM spans")


if __name__ == "__main__":
    print(f"Modelo: {MODELO}")
    print(f"Base de trazas: {DB}  ({len(spans())} spans guardados)")
    print("Enmascarado:", enmascarar("Laura · laura.gomez@mail.com · +57 300 123 4567 · Kafka"))
    print("Precios configurados:", "sí" if costo_usd(1, 1) is not None else
          "no (define PRECIO_ENTRADA_USD_1M y PRECIO_SALIDA_USD_1M en .env para ver dinero)")
