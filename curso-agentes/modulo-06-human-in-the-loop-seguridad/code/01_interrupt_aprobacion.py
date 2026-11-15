"""Human-in-the-Loop (HITL): interrupción antes de ejecutar herramientas con efectos irreversibles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import SALIDA, ejecutar_herramienta_ats, herramientas_ats, imprimir
from comun.ag_modelo import crear_modelo

RUTA_PAUSA = SALIDA / "m6_pausa_hitl.json"
HERRAMIENTAS_SENSIBLES = {"agendar_entrevista", "enviar_oferta"}


def correr_hasta_pausa_o_fin(estado: dict) -> dict:
    modelo = crear_modelo(agenda=True)
    esquemas = herramientas_ats(
        "obtener_vacante",
        "buscar_candidatos",
        "consultar_ficha_candidato",
        "verificar_elegibilidad",
        "agendar_entrevista",
        "entregar_terna",
    )

    while not estado["completado"]:
        r = modelo.responder(estado["mensajes"], esquemas)
        if not r.llamadas:
            break
        tc = r.llamadas[0]

        # Si la herramienta es sensible y aún no tiene aprobación firmada para esta llamada, pausamos el bucle
        if tc.nombre in HERRAMIENTAS_SENSIBLES:
            estado["pausa_pendiente"] = {
                "tool_call_id": tc.id,
                "herramienta": tc.nombre,
                "argumentos_propuestos": tc.argumentos,
            }
            RUTA_PAUSA.parent.mkdir(parents=True, exist_ok=True)
            RUTA_PAUSA.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")
            return estado

        estado["mensajes"].append(
            {
                "role": "assistant",
                "content": r.texto,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.nombre, "arguments": json.dumps(tc.argumentos, ensure_ascii=False)},
                    }
                ],
            }
        )
        res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
        estado["mensajes"].append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
        if tc.nombre == "entregar_terna":
            estado["terna"] = sorted(res.get("candidatos") or [])
            estado["completado"] = True

    return estado


def resolver_pausa_humana(decision: str, argumentos_editados: dict | None = None, revisor: str = "lider_rrhh") -> dict:
    """Reanuda la ejecución pausada aplicando la decisión humana ('aprobar', 'editar' o 'rechazar')."""
    estado = json.loads(RUTA_PAUSA.read_text(encoding="utf-8"))
    pausa = estado.pop("pausa_pendiente")
    args_finales = argumentos_editados if (decision == "editar" and argumentos_editados) else pausa["argumentos_propuestos"]

    estado["mensajes"].append(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": pausa["tool_call_id"],
                    "type": "function",
                    "function": {"name": pausa["herramienta"], "arguments": json.dumps(args_finales, ensure_ascii=False)},
                }
            ],
        }
    )

    if decision in ("aprobar", "editar"):
        res = ejecutar_herramienta_ats(pausa["herramienta"], args_finales)
        res["aprobado_por"] = revisor
        res["decision_hitl"] = decision
        estado["acciones_aprobadas"].append(res)
    else:
        res = {"ok": False, "rechazado_por_humano": True, "revisor": revisor, "motivo": "No agendar en esta ronda."}

    estado["mensajes"].append({"role": "tool", "tool_call_id": pausa["tool_call_id"], "content": json.dumps(res, ensure_ascii=False)})
    RUTA_PAUSA.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")
    return correr_hasta_pausa_o_fin(estado)


if __name__ == "__main__":
    estado_inicial = {
        "mensajes": [
            {"role": "system", "content": "Preselecciona candidatos elegibles, agenda entrevista y entrega la terna."},
            {"role": "user", "content": "Preselecciona la vacante VAC-101."},
        ],
        "pausa_pendiente": None,
        "acciones_aprobadas": [],
        "completado": False,
        "terna": [],
    }

    # 1) El agente avanza solo en las lecturas y se detiene justo antes del primer agendar_entrevista
    estado = correr_hasta_pausa_o_fin(estado_inicial)
    imprimir("1. Interrupción HITL activada antes de ejecutar herramienta sensible", estado["pausa_pendiente"])

    # 2) El humano aprueba pero edita la hora de la primera entrevista (CAND-01), y rechaza la segunda (CAND-03)
    args_mod = {**estado["pausa_pendiente"]["argumentos_propuestos"], "fecha": "2026-11-21T10:30"}
    estado = resolver_pausa_humana("editar", argumentos_editados=args_mod, revisor="ana.gomez@empresa.co")
    if estado.get("pausa_pendiente"):
        estado = resolver_pausa_humana("rechazar", revisor="ana.gomez@empresa.co")

    imprimir("2. Ejecución finalizada tras decisiones humanas", {
        "completado": estado["completado"],
        "acciones_ejecutadas": estado["acciones_aprobadas"],
        "terna_final": estado["terna"],
    })
