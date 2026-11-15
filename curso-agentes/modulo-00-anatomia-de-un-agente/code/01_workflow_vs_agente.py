"""Compara un workflow fijo de 3 pasos en código frente a un bucle de agente con tool calling sobre el ATS."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import (
    CANDIDATOS,
    PresupuestoAgente,
    VACANTES,
    ejecutar_herramienta_ats,
    herramientas_ats,
    imprimir,
    motivos_bloqueo,
    terna_correcta,
)
from comun.ag_modelo import Modelo, crear_modelo


def workflow_fijo(vacante_id: str) -> dict:
    """Flujo determinista en código: 1) leer vacante, 2) evaluar cada candidato con motivos_bloqueo, 3) entregar terna."""
    t0 = time.perf_counter()
    vac = VACANTES[vacante_id]
    elegibles = sorted(cid for cid, c in CANDIDATOS.items() if not motivos_bloqueo(vac, c))
    ms = round((time.perf_counter() - t0) * 1000, 3)
    return {
        "modo": "workflow_fijo",
        "vacante_id": vacante_id,
        "llamadas_llm": 0,
        "pasos": 1,
        "costo_usd": 0.0,
        "latencia_ms": ms,
        "terna": elegibles,
        "exacta": elegibles == terna_correcta(vacante_id),
    }


def bucle_agente(modelo: Modelo, vacante_id: str, max_pasos: int = 16) -> dict:
    """Bucle ReAct controlado: el modelo decide qué herramienta llamar en cada turno hasta entregar la terna."""
    presupuesto = PresupuestoAgente(max_pasos=max_pasos)
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {
            "role": "system",
            "content": (
                "Eres el agente de preselección técnica del ATS. "
                "Obtén la vacante, busca candidatos que cumplan las habilidades y el presupuesto, "
                "consulta su ficha, verifica su elegibilidad con verificar_elegibilidad y cierra con entregar_terna."
            ),
        },
        {"role": "user", "content": f"Preselecciona la terna de candidatos elegibles para la vacante {vacante_id}."},
    ]
    herramientas_usadas: list[str] = []
    terna_entregada: list[str] = []

    while True:
        presupuesto.abrir_paso()
        resp = modelo.responder(mensajes, esquemas)
        presupuesto.registrar(resp.tokens_entrada, resp.tokens_salida)

        if not resp.llamadas:
            break

        mensajes.append(
            {
                "role": "assistant",
                "content": resp.texto,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.nombre, "arguments": json.dumps(tc.argumentos, ensure_ascii=False)},
                    }
                    for tc in resp.llamadas
                ],
            }
        )

        cerro = False
        for tc in resp.llamadas:
            herramientas_usadas.append(tc.nombre)
            resultado = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
            mensajes.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                }
            )
            if tc.nombre == "entregar_terna":
                terna_entregada = sorted(resultado.get("candidatos") or [])
                cerro = True
        if cerro:
            break

    return {
        "modo": f"agente ({modelo.nombre})",
        "vacante_id": vacante_id,
        **presupuesto.resumen(),
        "herramientas": herramientas_usadas,
        "terna": terna_entregada,
        "exacta": terna_entregada == terna_correcta(vacante_id),
    }


if __name__ == "__main__":
    modelo = crear_modelo()
    imprimir("1. Workflow determinista en código (VAC-101)", workflow_fijo("VAC-101"))
    imprimir("2. Bucle de agente con herramientas (VAC-101)", bucle_agente(modelo, "VAC-101"))
    imprimir("3. Bucle de agente con herramientas (VAC-102)", bucle_agente(crear_modelo(), "VAC-102"))
