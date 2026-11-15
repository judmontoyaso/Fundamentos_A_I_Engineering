"""
01 · Patrón: encadenamiento con puertas (manual §4).

CV en texto -> extraer (LLM) -> PUERTA en código -> resumir perfil (LLM).
Si la puerta falla, la cadena se detiene: el error no llega al paso siguiente.
"""
from __future__ import annotations
from importlib import import_module
from pydantic import BaseModel, Field

c = import_module("00_comun")


class DatosCV(BaseModel):
    nombre: str
    correo: str | None = Field(default=None, description="null si no aparece")
    anios_experiencia: int = Field(ge=0, le=60, description="años de experiencia profesional total")
    evidencia_anios: str = Field(description="cita TEXTUAL del CV de la que salen los años")
    skills: list[str] = Field(description="tecnologías, en minúscula")


class Perfil(BaseModel):
    resumen: str = Field(description="perfil profesional en una o dos frases, máximo 40 palabras")


def puerta(datos: DatosCV, texto: str) -> list[str]:
    """Comprobaciones deterministas: código, no otra llamada al modelo."""
    problemas = []
    if not datos.correo:
        problemas.append("no hay correo de contacto")
    if datos.evidencia_anios.lower() not in texto.lower():
        problemas.append("la evidencia de los años no aparece literal en el CV")
    if not datos.skills:
        problemas.append("no se extrajo ninguna skill")
    return problemas


def cadena(texto: str) -> str:
    datos = c.llm(DatosCV, f"Extrae los datos del CV. {c.INSTRUCCION_CV} No inventes.", c.como_cv(texto))
    print(f"  paso 1 · extraer  -> {datos.nombre}, {datos.anios_experiencia} años, {datos.skills}")

    problemas = puerta(datos, texto)
    if problemas:
        print(f"  paso 2 · PUERTA   -> se detiene: {problemas}")
        return "REVISIÓN HUMANA"
    print("  paso 2 · puerta   -> ok")

    perfil = c.llm(Perfil, "Redacta un perfil profesional breve y factual, solo con estos datos.",
                   datos.model_dump_json())
    print(f"  paso 3 · resumir  -> {perfil.resumen}")
    return perfil.resumen


if __name__ == "__main__":
    c.reiniciar_contador()
    cvs = {
        "CV completo": "Laura Gómez · laura.gomez@mail.com · 9 años de experiencia en ingeniería de datos. "
                       "Kafka, Flink, Python y AWS. Lidera un equipo de 6.",
        "CV sin contacto": "Juan Ríos. Desarrollador con 2 años de experiencia en Node.js y Docker.",
    }
    for etiqueta, texto in cvs.items():
        print(f"\n== {etiqueta} ==")
        cadena(texto)
    print("\n" + c.resumen_costo("Costo: "))
    print("El CV sin contacto paró en la puerta: se ahorró el paso 3 y no pasó un dato incompleto.")
