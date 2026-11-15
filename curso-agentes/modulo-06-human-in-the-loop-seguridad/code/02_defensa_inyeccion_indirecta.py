"""Defensa en profundidad contra inyección indirecta de prompts en textos de CVs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import CANDIDATOS, VACANTES

PATRONES_SOSPECHOSOS = [
    re.compile(r"ignora\s+las\s+instrucciones", re.IGNORECASE),
    re.compile(r"sistema\s+prioritario", re.IGNORECASE),
    re.compile(r"enviar_oferta\s*\(", re.IGNORECASE),
]


def sanitizar_y_aislar_cv(candidato: dict) -> dict:
    """Extrae únicamente atributos tipados y marca alertas si el texto libre intenta inyectar comandos."""
    texto = candidato.get("resumen_cv", "")
    alertas = [p.pattern for p in PATRONES_SOSPECHOSOS if p.search(texto)]
    return {
        "id": candidato["id"],
        "anos_experiencia": int(candidato["anos_experiencia"]),
        "aspiracion_usd": int(candidato["aspiracion_usd"]),
        "habilidades_verificadas": list(candidato["habilidades"]),
        "alerta_inyeccion_detectada": len(alertas) > 0,
        "patrones_bloqueados": alertas,
    }


def guardia_herramienta_oferta(vacante_id: str, candidato_id: str, monto_usd: int, preseleccionados_validos: set[str]) -> dict:
    """Policy Enforcement Point (PEP) en código determinista antes de ejecutar una oferta."""
    vac = VACANTES[vacante_id]
    if candidato_id not in preseleccionados_validos:
        return {"ok": False, "bloqueo": f"RECHAZADO: {candidato_id} no superó la validación técnica determinista."}
    if monto_usd > vac["presupuesto_usd_mes"]:
        return {"ok": False, "bloqueo": f"RECHAZADO: monto ${monto_usd} excede el tope de la vacante (${vac['presupuesto_usd_mes']})."}
    return {"ok": True, "mensaje": f"Propuesta válida dentro de políticas para {candidato_id}."}


if __name__ == "__main__":
    print("=== 1. Inspección aislada de CAND-04 (con payload de inyección en el CV) ===")
    ficha_segura = sanitizar_y_aislar_cv(CANDIDATOS["CAND-04"])
    print(json.dumps(ficha_segura, indent=2, ensure_ascii=False))

    print("\n=== 2. Incluso si el LLM intentara llamar a enviar_oferta('CAND-04', 9500), el PEP lo bloquea ===")
    intento = guardia_herramienta_oferta("VAC-101", "CAND-04", 9500, preseleccionados_validos={"CAND-01", "CAND-03"})
    print(json.dumps(intento, indent=2, ensure_ascii=False))
