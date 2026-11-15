"""Envoltorio universal de errores accionables para herramientas de agentes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, CANDIDATOS


def consultar_eligibilidad_ats(vacante_id: str, candidato_id: str) -> dict:
    vacante_id = vacante_id.strip().upper()
    candidato_id = candidato_id.strip().upper()

    if vacante_id not in VACANTES:
        return {
            "ok": False,
            "codigo": "VACANTE_NO_EXISTE",
            "mensaje": f"No existe la vacante '{vacante_id}'.",
            "accion_sugerida": f"Usa uno de los IDs válidos: {list(VACANTES.keys())}",
        }
    if candidato_id not in CANDIDATOS:
        return {
            "ok": False,
            "codigo": "CANDIDATO_NO_EXISTE",
            "mensaje": f"No existe el candidato '{candidato_id}'.",
            "accion_sugerida": f"Ejecuta primero buscar_candidatos o usa un ID válido: {list(CANDIDATOS.keys())}",
        }

    v = VACANTES[vacante_id]
    c = CANDIDATOS[candidato_id]
    motivos_bloqueo = []
    if c["estado_ats"] == "enfriamiento" or c["ultimo_contacto_dias"] < 90:
        motivos_bloqueo.append(
            f"Periodo de enfriamiento activo: último contacto hace {c['ultimo_contacto_dias']} días (mínimo 90 días)."
        )
    if c["aspiracion_usd"] > v["presupuesto_usd_mes"]:
        motivos_bloqueo.append(
            f"Aspiración salarial (${c['aspiracion_usd']}) supera presupuesto de la vacante (${v['presupuesto_usd_mes']})."
        )

    return {
        "ok": True,
        "elegible": len(motivos_bloqueo) == 0,
        "vacante": v["titulo"],
        "candidato": c["nombre"],
        "motivos_bloqueo": motivos_bloqueo,
    }


if __name__ == "__main__":
    print("Error guiado:", json.dumps(consultar_eligibilidad_ats("VAC-999", "CAND-01"), indent=2, ensure_ascii=False))
    print("Enfriamiento:", json.dumps(consultar_eligibilidad_ats("VAC-101", "CAND-02"), indent=2, ensure_ascii=False))
    print("Elegible:", json.dumps(consultar_eligibilidad_ats("VAC-101", "CAND-01"), indent=2, ensure_ascii=False))
