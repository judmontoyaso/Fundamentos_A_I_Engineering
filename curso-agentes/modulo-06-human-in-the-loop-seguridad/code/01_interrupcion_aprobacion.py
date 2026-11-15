"""Patrón de interrupción (checkpoint + pausa) para aprobación humana en herramientas críticas."""
from __future__ import annotations

import json

HERRAMIENTAS_SENSIBLES = {"agendar_entrevista", "enviar_oferta"}


def ejecutar_con_politica(estado: dict, herramienta: str, argumentos: dict, aprobacion_humana: dict | None = None) -> dict:
    if herramienta in HERRAMIENTAS_SENSIBLES:
        if not aprobacion_humana or not aprobacion_humana.get("aprobado"):
            estado["etapa"] = "esperando_aprobacion_humana"
            estado["accion_pendiente"] = {"herramienta": herramienta, "argumentos": argumentos}
            return {
                "estado": "PAUSADO_POR_APROBACION",
                "mensaje": f"La acción '{herramienta}' requiere aprobación humana antes de ejecutarse.",
                "propuesta": estado["accion_pendiente"],
            }

        # Si hay aprobación humana explícita, registramos auditoría y ejecutamos
        estado["etapa"] = "completado"
        estado["accion_pendiente"] = None
        return {
            "estado": "EJECUTADO_CON_APROBACION",
            "aprobado_por": aprobacion_humana["aprobado_por"],
            "resultado": f"Entrevista agendada para {argumentos['candidato_id']} en {argumentos['fecha']}",
        }

    return {"estado": "EJECUTADO_AUTOMATICO", "resultado": f"Lectura '{herramienta}' completada"}


if __name__ == "__main__":
    estado_run = {"ejecucion_id": "run-hitl-01", "etapa": "en_curso", "accion_pendiente": None}

    print("=== 1. El agente intenta agendar entrevista por su cuenta ===")
    pausa = ejecutar_con_politica(
        estado_run,
        "agendar_entrevista",
        {"candidato_id": "CAND-01", "vacante_id": "VAC-101", "fecha": "2026-11-20T15:00"},
    )
    print(json.dumps(pausa, indent=2, ensure_ascii=False))

    print("\n=== 2. La reclutadora revisa el checkpoint y aprueba la acción ===")
    reanudado = ejecutar_con_politica(
        estado_run,
        estado_run["accion_pendiente"]["herramienta"],
        estado_run["accion_pendiente"]["argumentos"],
        aprobacion_humana={"aprobado": True, "aprobado_por": "laura@empresa.co"},
    )
    print(json.dumps(reanudado, indent=2, ensure_ascii=False))
