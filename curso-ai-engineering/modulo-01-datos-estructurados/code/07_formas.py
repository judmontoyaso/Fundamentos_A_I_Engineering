"""
07 · Formas de extracción: listas, clasificación (Enum), multi-etiqueta,
     nested, Optional y Maybe. Todas son el mismo truco: cambiar response_model.

    pip install instructor "pydantic>=2" openai
"""
import os
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

MODELO = os.getenv("MODELO", "gpt-4.1-mini")
client = instructor.from_openai(OpenAI(), mode=instructor.Mode.JSON_SCHEMA)


class Persona(BaseModel):
    nombre: str
    edad: int


class Area(str, Enum):
    ingenieria = "ingenieria"
    datos = "datos"
    producto = "producto"


class Clasificacion(BaseModel):
    area: Area = Field(description="una sola área, la principal")


class ClasificacionMulti(BaseModel):
    areas: list[Area] = Field(description="todas las áreas que apliquen")


class Direccion(BaseModel):
    calle: str
    ciudad: str
    codigo_postal: str


class PersonaConDireccion(BaseModel):
    nombre: str
    edad: int
    direccion: Direccion


class PersonaOpcional(BaseModel):
    nombre: str
    telefono: Optional[str] = Field(default=None, description="null si no aparece")


def extraer(response_model, texto: str):
    return client.chat.completions.create(
        model=MODELO, response_model=response_model,
        messages=[{"role": "user", "content": texto}],
    )


if __name__ == "__main__":
    # Listas
    gente = extraer(list[Persona], "Ana tiene 28, Beto 35 y Caro 41.")
    print("lista:", [(p.nombre, p.edad) for p in gente])

    # Clasificación
    c = extraer(Clasificacion, "Perfil: 5 años construyendo APIs y microservicios en Go.")
    print("area:", c.area.value)

    # Multi-etiqueta
    cm = extraer(ClasificacionMulti, "Full-stack que además monta pipelines de datos en Spark.")
    print("areas:", [a.value for a in cm.areas])

    # Nested
    pd = extraer(PersonaConDireccion,
                 "Juan, 30 años, vive en Calle 10 #5-20, Bogotá, 110111.")
    print("nested:", pd.nombre, "->", pd.direccion.ciudad, pd.direccion.codigo_postal)

    # Optional
    po = extraer(PersonaOpcional, "Se llama Lucía. No dejó teléfono.")
    print("opcional telefono:", po.telefono)
