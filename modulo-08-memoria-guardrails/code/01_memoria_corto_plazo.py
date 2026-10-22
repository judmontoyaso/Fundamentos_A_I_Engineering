"""
01 · Memoria de corto plazo: el historial y su presupuesto (manual §3).

Una conversación donde el dato clave está en el PRIMER turno. Tres estrategias:
historial completo, ventana deslizante y resumen + ventana. Se miden los tokens
enviados y se comprueba CON CÓDIGO si la respuesta recuerda los datos del inicio.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module
from pydantic import BaseModel, Field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "modulo-05-workflows-agentes" / "code"))
c = import_module("00_comun")

CONVERSACION = [
    {"role": "user", "content": "Voy a abrir una vacante de ingeniería de datos. Es 100 % remota desde Colombia y "
                                "exijo inglés C1, porque el equipo está en Canadá."},
    {"role": "assistant", "content": "Entendido. ¿Qué tecnologías son imprescindibles para el puesto?"},
    {"role": "user", "content": "Kafka o algún sistema de streaming, Python y algo de nube. Idealmente AWS."},
    {"role": "assistant", "content": "Perfecto. En la base hay perfiles con Kafka y Flink, otros con AWS y "
                                     "Terraform, y varios con Python orientado a ciencia de datos."},
    {"role": "user", "content": "¿Y cuántos tienen experiencia liderando equipos?"},
    {"role": "assistant", "content": "Al menos una candidata lideró un equipo de seis ingenieros como Tech Lead; "
                                     "en los demás CVs no aparece liderazgo explícito."},
    {"role": "user", "content": "Bien. Sobre el proceso: primero una prueba técnica de dos horas, después una "
                                "entrevista con el líder del equipo y al final una con recursos humanos."},
    {"role": "assistant", "content": "Anotado: prueba técnica, entrevista técnica y entrevista de recursos humanos."},
    {"role": "user", "content": "La prueba técnica sería sobre diseño de un pipeline de eventos con Kafka, con "
                                "manejo de errores y reprocesamiento."},
    {"role": "assistant", "content": "Es una buena prueba para medir experiencia real en streaming."},
]
PREGUNTA = "Recuérdame: ¿qué nivel de idioma te dije que exijo y cuál es la modalidad de trabajo de la vacante?"
VENTANA = 4


class Respuesta(BaseModel):
    nivel_idioma: str | None = Field(description="el nivel de idioma exigido, o null si no lo sabes")
    modalidad: str | None = Field(description="la modalidad de trabajo, o null si no la sabes")


class Resumen(BaseModel):
    resumen: str = Field(description="resumen de la conversación en máximo 60 palabras, con TODOS los requisitos")


def tokens(mensajes: list[dict]) -> int:
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    return sum(len(enc.encode(m["content"])) + 4 for m in mensajes)


def historial(estrategia: str) -> list[dict]:
    if estrategia == "completo":
        return CONVERSACION
    if estrategia == "ventana":
        return CONVERSACION[-VENTANA:]
    antiguo, reciente = CONVERSACION[:-VENTANA], CONVERSACION[-VENTANA:]
    r = c.llm(Resumen, "Resume esta conversación entre un reclutador y un asistente.",
              "\n".join(f"{m['role']}: {m['content']}" for m in antiguo))
    return [{"role": "user", "content": f"(Resumen de lo hablado antes: {r.resumen})"}, *reciente]


if __name__ == "__main__":
    c.reiniciar_contador()
    print(f"{'estrategia':10} {'tokens enviados':>16} {'idioma':>8} {'modalidad':>10}   respuesta")
    for estrategia in ("completo", "ventana", "resumen"):
        mensajes = historial(estrategia) + [{"role": "user", "content": PREGUNTA}]
        r = c.llm(Respuesta, "Eres el asistente de un reclutador. Responde solo con lo que se dijo en la "
                             "conversación; si no lo sabes, usa null.", mensajes)
        idioma_ok = bool(r.nivel_idioma) and "c1" in r.nivel_idioma.lower()
        modalidad_ok = bool(r.modalidad) and "remot" in r.modalidad.lower()
        print(f"{estrategia:10} {tokens(mensajes):>16} {'✓' if idioma_ok else '✗':>8} {'✓' if modalidad_ok else '✗':>10}"
              f"   {r.nivel_idioma!r} / {r.modalidad!r}")

    print("\n== Lo que cuesta cada estrategia en una conversación larga ==")
    por_turno = tokens(CONVERSACION) / len(CONVERSACION)
    for n in (10, 30, 60):
        completo = sum(por_turno * k for k in range(1, n + 1))            # cada turno reenvía todo lo anterior
        ventana = sum(por_turno * min(k, VENTANA) for k in range(1, n + 1))
        print(f"  {n:>3} turnos · tokens de entrada acumulados: completo ~{completo:,.0f} · ventana ~{ventana:,.0f}")
    print("  El historial completo crece con el cuadrado de los turnos; la ventana, en línea recta.")
    print("  El resumen cuesta una llamada extra cada cierto tiempo, a cambio de no olvidar lo esencial.")
    print("\n" + c.resumen_costo("Costo: "))
