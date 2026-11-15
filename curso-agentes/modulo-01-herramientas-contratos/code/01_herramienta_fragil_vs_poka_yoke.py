"""Contrasta una herramienta genérica y ambigua frente a contratos Poka-Yoke con validación estricta."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import CATALOGO_HABILIDADES, ESQUEMAS_HERRAMIENTAS, VACANTES, ejecutar_herramienta_ats, imprimir


def herramienta_fragil(consulta_libre: str) -> dict:
    """Antipatrón: recibe texto libre o pseudo-SQL sin tipos, sin cotas y con errores crudos."""
    if "DROP" in consulta_libre.upper() or ";" in consulta_libre:
        return {"error": "SQLSyntaxError near ';' at line 1 (tabla interna expuesta: ats_prod_candidates_v2)"}
    return {"filas": "CAND-01, CAND-02, CAND-03, CAND-04, CAND-05, CAND-06, CAND-07, CAND-08 (volcado sin límite)"}


def probar_contratos_poka_yoke() -> dict:
    """Prueba el contrato Poka-Yoke ante entradas válidas, vacantes inexistentes y habilidades con errata."""
    casos = {
        "busqueda_valida": ejecutar_herramienta_ats(
            "buscar_candidatos",
            {"habilidades": ["Python", "RAG"], "max_aspiracion_usd": 6500},
        ),
        "vacante_inexistente": ejecutar_herramienta_ats(
            "obtener_vacante",
            {"vacante_id": "VAC-999"},
        ),
        "habilidad_con_errata": ejecutar_herramienta_ats(
            "buscar_candidatos",
            {"habilidades": ["Python", "Evaluacion de LLM"], "max_aspiracion_usd": 6500},
        ),
        "presupuesto_invalido": ejecutar_herramienta_ats(
            "buscar_candidatos",
            {"habilidades": ["Python"], "max_aspiracion_usd": -50},
        ),
    }
    return {
        "catalogo_habilidades_cerrado": CATALOGO_HABILIDADES,
        "vacantes_enum": sorted(VACANTES.keys()),
        "esquema_buscar_candidatos": ESQUEMAS_HERRAMIENTAS["buscar_candidatos"]["function"],
        "resultados_validacion": casos,
    }


if __name__ == "__main__":
    imprimir("1. Antipatrón: herramienta frágil de texto libre", herramienta_fragil("SELECT * FROM candidatos; DROP TABLE"))
    imprimir("2. Contratos Poka-Yoke con JSON Schema estricto", probar_contratos_poka_yoke())
