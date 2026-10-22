"""
05 · Evaluar un RAG por sus dos mitades (Módulo 3 §10-11).

  - Retrieval: context_recall / context_precision sobre chunks etiquetados.
  - Generación: un chequeo de 'faithfulness' (¿cada frase de la respuesta se
    apoya en el contexto?) hecho con un LLM como juez.

El de retrieval corre sin dependencias. El de faithfulness necesita un LLM.

    pip install openai   (solo para la parte de faithfulness)
"""
from __future__ import annotations
import os
from statistics import mean


# ---------- Retrieval ----------
def context_recall(recuperados: list, relevantes: set) -> float:
    if not relevantes:
        return 0.0
    return len(set(recuperados) & relevantes) / len(relevantes)


def context_precision(recuperados: list, relevantes: set) -> float:
    if not recuperados:
        return 0.0
    return sum(1 for r in recuperados if r in relevantes) / len(recuperados)


def eval_retrieval(casos: list[dict]) -> dict:
    """casos = [{'recuperados': [chunk_ids], 'relevantes': {chunk_ids}}, ...]"""
    rec = [context_recall(c["recuperados"], c["relevantes"]) for c in casos]
    pre = [context_precision(c["recuperados"], c["relevantes"]) for c in casos]
    return {"context_recall": mean(rec), "context_precision": mean(pre)}


# ---------- Generación: faithfulness con LLM-juez ----------
FAITH_SYSTEM = (
    "Eres un evaluador estricto. Dada una RESPUESTA y un CONTEXTO, decide qué fracción de las "
    "afirmaciones de la respuesta está DIRECTAMENTE respaldada por el contexto. Devuelve solo un "
    "número entre 0.0 y 1.0 (1.0 = todo respaldado; 0.0 = nada). No expliques."
)


def faithfulness(respuesta: str, contexto: str, modelo: str | None = None) -> float:
    from openai import OpenAI
    modelo = modelo or os.getenv("MODELO", "gpt-4.1-mini")
    out = OpenAI().chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": FAITH_SYSTEM},
            {"role": "user", "content": f"RESPUESTA:\n{respuesta}\n\nCONTEXTO:\n{contexto}"},
        ],
    ).choices[0].message.content.strip()
    try:
        return max(0.0, min(1.0, float(out.split()[0])))
    except Exception:
        return float("nan")


if __name__ == "__main__":
    casos = [
        {"recuperados": [10, 3, 7, 1, 9], "relevantes": {10, 7}},
        {"recuperados": [4, 2, 8, 5, 6], "relevantes": {2}},
        {"recuperados": [1, 2, 3, 4, 5], "relevantes": {99}},  # el relevante NO se recuperó
    ]
    print("Retrieval:", eval_retrieval(casos))
    print("\nEl 3er caso tiene recall 0: el chunk con la respuesta nunca llegó al LLM.")
    print("Eso es un fallo de RECUPERACIÓN, no de generación (Módulo 3 §10).")
