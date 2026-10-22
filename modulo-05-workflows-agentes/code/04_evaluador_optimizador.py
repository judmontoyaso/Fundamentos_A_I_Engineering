"""
04 · Patrón: evaluador y optimizador (manual §8).

Un LLM redacta una invitación a entrevista; un evaluador la revisa contra una
rúbrica y devuelve las fallas; se corrige hasta aprobar o agotar 3 vueltas.
Lo que se puede comprobar con código se comprueba con código.
"""
from __future__ import annotations
import re
from importlib import import_module
from pydantic import BaseModel, Field

c = import_module("00_comun")

TAREA = ("Escribe un mensaje breve invitando a Laura Gómez a una entrevista para la vacante "
         "'Líder técnico de datos en tiempo real'.")

# El generador NO ve la rúbrica en la primera vuelta: así pasa en la vida real, donde
# la rúbrica incluye convenciones de la empresa que quien redacta no conoce.
RUBRICA = [
    "menciona algo concreto del perfil de Laura (Kafka, Flink, liderazgo de un equipo)",
    "propone exactamente dos horarios concretos para elegir (día y hora)",
    "firma como 'Equipo de Talento, Acme'",
    "tono cercano y profesional, sin frases de relleno",
]
MAX_PALABRAS = 60
MAX_VUELTAS = 3


class Borrador(BaseModel):
    mensaje: str


class Evaluacion(BaseModel):
    fallas: list[str] = Field(description="criterios de la rúbrica que NO se cumplen; vacía si todo se cumple")
    aprobado: bool


def chequeos_en_codigo(texto: str) -> list[str]:
    fallas = []
    palabras = len(texto.split())
    if palabras > MAX_PALABRAS:
        fallas.append(f"tiene {palabras} palabras; el máximo es {MAX_PALABRAS}")
    if re.search(r"\$|salario|sueldo", texto, re.IGNORECASE):
        fallas.append("menciona salario: eso va en otra etapa")
    return fallas


if __name__ == "__main__":
    c.reiniciar_contador()
    perfil = next(cv["texto"] for cv in c.corpus() if cv["nombre"] == "Laura Gómez")
    borrador = c.llm(Borrador, "Redactas mensajes de reclutamiento.", f"{TAREA}\nPerfil: {perfil}")

    for vuelta in range(1, MAX_VUELTAS + 1):
        fallas = chequeos_en_codigo(borrador.mensaje)
        ev = c.llm(Evaluacion, "Evalúa el mensaje con esta rúbrica, criterio por criterio:\n- "
                   + "\n- ".join(RUBRICA), borrador.mensaje)
        fallas += ev.fallas
        print(f"\n== Vuelta {vuelta} ({len(borrador.mensaje.split())} palabras) ==\n{borrador.mensaje}")
        if not fallas:
            print("\n✓ Aprobado.")
            break
        print("\n✗ Fallas:\n  - " + "\n  - ".join(fallas))
        if vuelta == MAX_VUELTAS:
            print("\nSe agotaron las vueltas: a revisión humana. Un cuarto intento no suele arreglarlo.")
            break
        borrador = c.llm(Borrador, "Corrige el mensaje para resolver TODAS las fallas indicadas, sin añadir "
                         "nada más.", f"Mensaje:\n{borrador.mensaje}\n\nFallas:\n- " + "\n- ".join(fallas))

    print("\n" + c.resumen_costo("Costo: "))
