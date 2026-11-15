"""
13 · Economía a escala: contar tokens, cachear y paralelizar.

Tres funciones independientes:
  - estimar_costo(): cuánto costaría procesar N documentos.
  - extraer_cacheado(): no vuelvas a pagar por el mismo (doc, schema, modelo).
  - extraer_muchos(): concurrencia con límite para respetar el rate limit.

    pip install instructor "pydantic>=2" openai tiktoken
"""
import os
import json
import hashlib
import asyncio
from pathlib import Path
from pydantic import BaseModel
import instructor
from openai import OpenAI, AsyncOpenAI

MODELO = os.getenv("MODELO", "gpt-4.1-mini")
CACHE_DIR = Path(".cache_extraccion")
CACHE_DIR.mkdir(exist_ok=True)


# ---------- 1. Estimar costo ----------
def estimar_costo(n_docs: int, tok_in_prom: int, tok_out_prom: int,
                  precio_in_1k: float, precio_out_1k: float) -> float:
    """Costo aproximado en USD de procesar n_docs. Mide tok_in_prom con
    tiktoken sobre una muestra real; no lo adivines."""
    por_doc = (tok_in_prom / 1000) * precio_in_1k + (tok_out_prom / 1000) * precio_out_1k
    return n_docs * por_doc


def contar_tokens(texto: str, encoding: str = "o200k_base") -> int:
    import tiktoken
    return len(tiktoken.get_encoding(encoding).encode(texto))


# ---------- 2. Cache por hash(doc + schema + modelo) ----------
def _clave(texto: str, schema_json: str, modelo: str) -> str:
    return hashlib.sha256((texto + schema_json + modelo).encode()).hexdigest()


def extraer_cacheado(client, response_model: type[BaseModel], texto: str):
    schema_json = json.dumps(response_model.model_json_schema(), sort_keys=True)
    clave = _clave(texto, schema_json, MODELO)
    f = CACHE_DIR / f"{clave}.json"
    if f.exists():
        return response_model.model_validate_json(f.read_text(encoding="utf-8"))
    obj = client.chat.completions.create(
        model=MODELO, response_model=response_model,
        messages=[{"role": "user", "content": texto}],
    )
    f.write_text(obj.model_dump_json(), encoding="utf-8")
    return obj
    # Cambiar un campo del schema cambia schema_json -> invalida solo lo necesario.


# ---------- 3. Paralelizar con límite ----------
async def extraer_muchos(response_model: type[BaseModel], docs: list[str],
                         concurrencia: int = 8):
    aclient = instructor.from_openai(AsyncOpenAI(), mode=instructor.Mode.JSON_SCHEMA)
    sem = asyncio.Semaphore(concurrencia)   # evita el baneo por rate limit (429)

    async def uno(doc: str):
        async with sem:
            return await aclient.chat.completions.create(
                model=MODELO, response_model=response_model,
                messages=[{"role": "user", "content": doc}],
            )

    return await asyncio.gather(*(uno(d) for d in docs))


if __name__ == "__main__":
    # Ejemplo de estimación (ajusta precios a los de tu proveedor):
    usd = estimar_costo(n_docs=1000, tok_in_prom=1800, tok_out_prom=250,
                        precio_in_1k=0.00015, precio_out_1k=0.0006)
    print(f"Procesar 1000 CVs ~= {usd:.2f} USD (con los supuestos dados)")
