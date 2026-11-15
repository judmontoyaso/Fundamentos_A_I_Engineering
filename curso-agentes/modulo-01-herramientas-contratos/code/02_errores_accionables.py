"""Autocorrección en el bucle del agente: errores opacos vs errores accionables con sugerencias del catálogo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import PresupuestoAgente, ejecutar_herramienta_ats, herramientas_ats, imprimir, terna_correcta
from comun.ag_modelo import crear_modelo


def correr_con_errata(*, sugerir_en_error: bool) -> dict:
    """Corre un modelo que comete una errata ('Evaluacion de LLM' sin tilde ni plural) en la primera búsqueda."""
    modelo = crear_modelo(errata=True)
    presupuesto = PresupuestoAgente(max_pasos=16)
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": "Preselecciona candidatos elegibles para la vacante y cierra con entregar_terna."},
        {"role": "user", "content": "Preselecciona la vacante VAC-101."},
    ]
    intentos_busqueda: list[dict] = []
    terna: list[str] = []

    while True:
        presupuesto.abrir_paso()
        r = modelo.responder(mensajes, esquemas)
        presupuesto.registrar(r.tokens_entrada, r.tokens_salida)
        if not r.llamadas:
            break
        mensajes.append(
            {
                "role": "assistant",
                "content": r.texto,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.nombre, "arguments": json.dumps(tc.argumentos, ensure_ascii=False)},
                    }
                    for tc in r.llamadas
                ],
            }
        )
        fin = False
        for tc in r.llamadas:
            res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos, sugerir_en_error=sugerir_en_error)
            if tc.nombre == "buscar_candidatos":
                intentos_busqueda.append(
                    {
                        "habilidades_enviadas": tc.argumentos.get("habilidades"),
                        "ok": res.get("ok"),
                        "sugerencias_devueltas": res.get("sugerencias"),
                        "encontrados": res.get("total", 0),
                    }
                )
            mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
            if tc.nombre == "entregar_terna":
                terna = sorted(res.get("candidatos") or [])
                fin = True
        if fin:
            break

    return {
        "modo_error": "accionable_con_sugerencias" if sugerir_en_error else "opaco_sin_pistas",
        "intentos_busqueda": intentos_busqueda,
        "pasos_totales": presupuesto.pasos,
        "terna_entregada": terna,
        "exito": terna == terna_correcta("VAC-101"),
    }


if __name__ == "__main__":
    imprimir("1. Error opaco (sin sugerencias): el agente no sabe cómo corregir la habilidad", correr_con_errata(sugerir_en_error=False))
    imprimir("2. Error accionable (con sugerencias del catálogo): el agente corrige y acierta", correr_con_errata(sugerir_en_error=True))
