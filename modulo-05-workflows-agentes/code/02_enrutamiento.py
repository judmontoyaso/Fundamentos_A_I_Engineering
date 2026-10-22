"""
02 · Patrón: enrutamiento (manual §5).

Un LLM clasifica cada consulta (exacta / paráfrasis / mixta) y el código elige el
modo de búsqueda del Módulo 4. Lo comparamos, con el set etiquetado del Módulo 4,
contra (a) usar siempre la híbrida y (b) una regla gratuita sin LLM.
"""
from __future__ import annotations
import asyncio
from importlib import import_module
from statistics import mean
from typing import Literal
from pydantic import BaseModel, Field

c = import_module("00_comun")
ev = import_module("05_comparar_busquedas")     # SET etiquetado del Módulo 4
met = import_module("11_eval_retrieval")        # métricas del Módulo 2

MODO_POR_TIPO = {"exacta": "bm25", "parafrasis": "semantica", "mixta": "hibrida"}


class Ruta(BaseModel):
    razonamiento: str = Field(description="una frase: por qué es de ese tipo")
    tipo: Literal["exacta", "parafrasis", "mixta"] = Field(description=(
        "exacta: siglas, códigos o nombres de tecnología que deben coincidir literalmente; "
        "parafrasis: describe una habilidad con otras palabras; mixta: combina ambas cosas"))


SYSTEM = "Clasifica la consulta de un buscador de hojas de vida para elegir cómo buscar."


async def clasificar_todas(consultas: list[str]) -> list[Ruta]:
    return await asyncio.gather(*(c.llm_async(Ruta, SYSTEM, q) for q in consultas))


def regla(consulta: str) -> str:
    """Heurística sin LLM: 1-2 palabras suele ser una sigla o un nombre exacto."""
    return "bm25" if len(consulta.split()) <= 2 else "hibrida"


def evaluar(modos: list[str]) -> tuple[float, float]:
    rec, rr = [], []
    for (consulta, relevantes, _), modo in zip(ev.SET, modos):
        ids = [h.id for h in c.buscar(consulta, modo=modo, k=ev.K)]
        rec.append(met.recall_at_k(ids, relevantes, ev.K))
        rr.append(met.reciprocal_rank(ids, relevantes))
    return mean(rec), mean(rr)


if __name__ == "__main__":
    c.reiniciar_contador()
    consultas = [q for q, _, _ in ev.SET]
    rutas = asyncio.run(clasificar_todas(consultas))

    aciertos = 0
    print(f"{'consulta':52} {'etiqueta':10} {'LLM':10} {'regla'}")
    for (q, _, etiqueta), r in zip(ev.SET, rutas):
        aciertos += r.tipo == etiqueta
        print(f"{q[:52]:52} {etiqueta:10} {r.tipo + (' ✓' if r.tipo == etiqueta else ' ✗'):10} {regla(q)}")
    print(f"\nEl enrutador LLM coincide con la etiqueta en {aciertos}/{len(rutas)} consultas.")

    filas = {
        "siempre híbrida": evaluar(["hibrida"] * len(consultas)),
        "enrutador LLM": evaluar([MODO_POR_TIPO[r.tipo] for r in rutas]),
        "regla sin LLM": evaluar([regla(q) for q in consultas]),
    }
    print(f"\n{'estrategia':18} {'recall@' + str(ev.K):>9} {'MRR':>6}")
    for nombre, (r, m) in filas.items():
        print(f"{nombre:18} {r:9.2f} {m:6.2f}")
    print("\n" + c.resumen_costo("Costo del enrutador LLM: "))
    base, llm_r, reg = filas["siempre híbrida"][1], filas["enrutador LLM"][1], filas["regla sin LLM"][1]
    if llm_r <= base:
        print("El enrutador LLM no supera a 'siempre híbrida': añade una llamada por consulta sin ganar nada.")
    elif reg >= llm_r:
        print("Enrutar mejora a la híbrida fija, pero la regla gratuita rinde igual que el LLM:")
        print("en este caso el LLM sobra (manual §5). Con consultas más variadas la regla podría quedarse corta.")
    else:
        print("El enrutador LLM supera a la híbrida fija y a la regla: aquí la llamada extra se justifica.")
