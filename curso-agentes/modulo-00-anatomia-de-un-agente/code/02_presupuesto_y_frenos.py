"""Freno presupuestario fuera del modelo: corte determinista por pasos, tokens y dólares."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import (
    PresupuestoAgente,
    PresupuestoAgotado,
    ejecutar_herramienta_ats,
    herramientas_ats,
    imprimir,
    terna_correcta,
)
from comun.ag_modelo import Modelo, crear_modelo


def correr_con_presupuesto(modelo: Modelo, vacante_id: str, presupuesto: PresupuestoAgente) -> dict:
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": "Preselecciona candidatos elegibles y entrega la terna con entregar_terna."},
        {"role": "user", "content": f"Preselecciona la vacante {vacante_id}."},
    ]
    terna: list[str] = []
    motivo_corte: str | None = None

    try:
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
                res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
                mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
                if tc.nombre == "entregar_terna":
                    terna = sorted(res.get("candidatos") or [])
                    fin = True
            if fin:
                break
    except PresupuestoAgotado as exc:
        motivo_corte = str(exc)

    return {
        "estado": "cortado_por_presupuesto" if motivo_corte else "completado",
        "motivo_corte": motivo_corte,
        **presupuesto.resumen(),
        "terna_entregada": terna,
        "exacta": terna == terna_correcta(vacante_id),
    }


if __name__ == "__main__":
    # 1) Ejecución sana dentro del presupuesto (12 pasos, 30k tokens, $0.05)
    sana = correr_con_presupuesto(
        crear_modelo(),
        "VAC-101",
        PresupuestoAgente(max_pasos=16, max_tokens=30_000, max_costo_usd=0.05),
    )
    imprimir("1. Ejecución normal dentro del presupuesto", sana)

    # 2) Agente atascado (terco=True repite la misma búsqueda vacía sin parar): el freno corta en el paso 5
    bucle = correr_con_presupuesto(
        crear_modelo(terco=True),
        "VAC-101",
        PresupuestoAgente(max_pasos=5, max_tokens=30_000, max_costo_usd=0.05),
    )
    imprimir("2. Agente en bucle infinito cortado por max_pasos=5", bucle)

    # 3) Tope estricto de tokens (max_tokens=1500): corta antes de acumular contexto excesivo
    tope_tokens = correr_con_presupuesto(
        crear_modelo(),
        "VAC-101",
        PresupuestoAgente(max_pasos=16, max_tokens=1_500, max_costo_usd=0.05),
    )
    imprimir("3. Corte por presupuesto de tokens (max_tokens=1500)", tope_tokens)
