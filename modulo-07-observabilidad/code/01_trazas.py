"""
01 · Trazar un pedido de punta a punta (manual §2-§3).

buscar -> evaluar a cada candidato (LLM) -> redactar invitación (LLM), cada paso
un span con sus tokens. Al final, un pedido que FALLA para ver cómo se ve un error
en la traza (y cuánto cuestan los reintentos antes de rendirse).
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module
from pydantic import BaseModel, field_validator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # para importar 00_trazador
tz = import_module("00_trazador")
c = import_module("00_comun")                    # buscador y helpers del Módulo 5
par = import_module("03_paralelizacion")         # Encaje
ev = import_module("04_evaluador_optimizador")   # Borrador

VACANTE = "Líder técnico de datos en tiempo real"


def atender(pedido: str) -> str:
    with tz.nueva_traza("pedido", pedido=pedido) as raiz:
        with tz.span("buscar", modo="hibrida", k=3) as s:
            hits = c.buscar(pedido, modo="hibrida", k=3, nivel="senior")
            s.atributos["resultados"] = [h.payload["nombre"] for h in hits]
        mejores = []
        for h in hits:
            e = tz.llm_trazado(par.Encaje, f"Evalúa el CV contra esta vacante: {VACANTE}. {c.INSTRUCCION_CV}",
                               c.como_cv(h.payload["texto"]), nombre=f"evaluar {h.payload['nombre'].split()[0]}",
                               version_prompt="encaje-v2")
            mejores.append((e.puntaje, h.payload["nombre"]))
        puntaje, nombre = max(mejores)
        borrador = tz.llm_trazado(ev.Borrador, "Redactas invitaciones a entrevista, máximo 50 palabras.",
                                  f"Invita a {nombre} a una entrevista para: {VACANTE}.",
                                  nombre="redactar", version_prompt="invitacion-v1")
        raiz.atributos.update(elegido=nombre, puntaje=puntaje)
        return raiz.trace_id, borrador.mensaje


class Imposible(BaseModel):
    """Un schema que nunca valida: para ver un error y sus reintentos en la traza."""
    valor: int

    @field_validator("valor")
    @classmethod
    def nunca(cls, v):
        raise ValueError("este validador rechaza cualquier valor")


def duracion(trace_id: str, nombre: str) -> float:
    return next(s["seg"] for s in tz.spans(trace_id) if s["nombre"] == nombre)


if __name__ == "__main__":
    traza, mensaje = atender("Líder técnico de datos en tiempo real")
    print(f"== Traza {traza} ==\n{tz.arbol(traza)}\n\nInvitación: {mensaje}")

    traza2, _ = atender("Arquitecto de datos en la nube que haya liderado equipos")
    print(f"\n== Segundo pedido (traza {traza2}) ==\n{tz.arbol(traza2)}")
    print(f"\n'buscar' tardó {duracion(traza, 'buscar'):.1f} s en el primer pedido y {duracion(traza2, 'buscar'):.1f} s "
          "en el segundo.\nSi el primero es mucho más lento, es arranque en frío (cargar el modelo de embeddings y "
          "construir el índice):\nlo paga el primer usuario y dispara tu p95 (manual §5).")

    print("\n== Un pedido que falla ==")
    try:
        with tz.nueva_traza("pedido con error") as raiz:
            fallida = raiz.trace_id
            tz.llm_trazado(Imposible, "Devuelve un número.", "Dame el número 7.", nombre="extraer",
                           max_retries=2)
    except Exception as e:
        print(f"Excepción capturada: {type(e).__name__}")
    print(tz.arbol(fallida))
    print("\nEl span del LLM midió el tiempo de TODOS los intentos: un reintento de validación cuesta")
    print("otra llamada completa. Si ves muchos, el problema está en el prompt o en el schema.")
