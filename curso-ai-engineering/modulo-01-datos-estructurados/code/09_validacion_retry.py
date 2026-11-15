"""
09 · Validación + retry: el corazón del módulo.

Pydantic valida tipos gratis; aquí agregamos reglas semánticas con
field/model validators, y dejamos que Instructor REINTENTE pasándole al
modelo el error exacto como feedback (auto-corrección).

    pip install instructor "pydantic>=2" openai
"""
import os
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, model_validator

MODELO = os.getenv("MODELO", "gpt-4.1-mini")
client = instructor.from_openai(OpenAI(), mode=instructor.Mode.JSON_SCHEMA)


class Decision(BaseModel):
    # Campo de razonamiento ANTES del resultado = chain-of-thought barato.
    # El modelo genera en orden, así que "piensa" antes de concluir.
    razonamiento: str = Field(description="Explica paso a paso antes de decidir")
    correo: str = Field(description="correo del candidato")
    anio_inicio: int
    anio_fin: int
    apto: bool

    @field_validator("correo")
    @classmethod
    def correo_valido(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("correo inválido: debe ser como nombre@dominio.com")
        return v.lower()

    @model_validator(mode="after")
    def rango_coherente(self):
        if self.anio_fin < self.anio_inicio:
            raise ValueError("anio_fin no puede ser anterior a anio_inicio")
        return self


if __name__ == "__main__":
    texto = (
        "Candidato: Marta Ríos. Contacto: MARTA RIOS (arroba) empresa punto com. "
        "Trabajó de 2019 a 2022. Tiene experiencia sólida liderando equipos."
    )
    d = client.chat.completions.create(
        model=MODELO,
        response_model=Decision,
        max_retries=3,          # si validación falla, reintenta con el error como feedback
        messages=[
            {"role": "system", "content": "Normaliza el correo al formato estándar."},
            {"role": "user", "content": texto},
        ],
    )
    print("correo normalizado:", d.correo)
    print("rango:", d.anio_inicio, "-", d.anio_fin)
    print("apto:", d.apto)
    print("razonamiento:", d.razonamiento[:120], "...")
