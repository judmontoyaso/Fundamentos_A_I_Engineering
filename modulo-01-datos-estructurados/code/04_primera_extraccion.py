"""
04 · Tu primera extracción con Instructor.

Convierte una frase en un objeto tipado. El LLM deja de devolver "texto" y
pasa a devolver una instancia de tu clase.

Requisitos:
    pip install instructor "pydantic>=2" openai
    export OPENAI_API_KEY=...   (o define MODELO para otro proveedor)
"""
import os
import instructor
from openai import OpenAI
from pydantic import BaseModel

MODELO = os.getenv("MODELO", "gpt-4.1-mini")  # cámbialo sin tocar el resto


class Persona(BaseModel):
    nombre: str
    edad: int


def main() -> None:
    # JSON_SCHEMA = structured outputs nativos; funciona con modelos normales y de razonamiento.
    client = instructor.from_openai(OpenAI(), mode=instructor.Mode.JSON_SCHEMA)

    persona = client.chat.completions.create(
        model=MODELO,
        response_model=Persona,          # el contrato
        messages=[{"role": "user", "content": "Ana Pérez tiene 28 años y vive en Medellín."}],
    )

    print(f"nombre = {persona.nombre!r}")
    print(f"edad   = {persona.edad!r}  (tipo: {type(persona.edad).__name__})")
    print(f"objeto = {type(persona).__name__}")  # Persona, no dict


if __name__ == "__main__":
    main()
