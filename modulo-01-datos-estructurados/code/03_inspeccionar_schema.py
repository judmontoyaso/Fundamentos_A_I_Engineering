"""
03 · El schema ES el prompt.

Imprime el JSON Schema REAL que Pydantic genera a partir de tu clase y que
Instructor envía dentro del request al modelo. Hazlo una vez y nunca más
tratarás el response_model como una caja negra.

No llama a ningún LLM: es gratis y offline.
"""
import json
from pydantic import BaseModel, Field
from typing import Literal


class Candidato(BaseModel):
    nombre_completo: str = Field(description="Nombre y apellidos tal como aparecen en el CV")
    anios_experiencia: int = Field(ge=0, le=60, description="Años totales de experiencia profesional")
    nivel: Literal["junior", "semi-senior", "senior"] = Field(
        description="Infiere el nivel a partir de la experiencia y responsabilidades"
    )
    correo: str | None = Field(default=None, description="Email; null si no aparece")


if __name__ == "__main__":
    schema = Candidato.model_json_schema()
    print(json.dumps(schema, indent=2, ensure_ascii=False))

    # Observa: tus descripciones, tipos y restricciones (ge/le, enum de Literal)
    # están TODOS aquí. Esto es texto que el modelo lee como instrucciones.
    # Prueba a renombrar 'anios_experiencia' -> 'ae' y vuelve a correr:
    # el schema pierde la pista que guiaba al modelo.
