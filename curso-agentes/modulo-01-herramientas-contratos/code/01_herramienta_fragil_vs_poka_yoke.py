"""Contrasta una herramienta cruda de bajo nivel con una herramienta poka-yoke diseñada para un LLM."""
from __future__ import annotations

from difflib import get_close_matches
from typing import Literal
from pydantic import BaseModel, Field
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import CANDIDATOS

CATALOGO_HABILIDADES = sorted({h for c in CANDIDATOS.values() for h in c["habilidades"]})


class BuscarCandidatosInput(BaseModel):
    habilidades_requeridas: list[str] = Field(
        description="Lista de habilidades técnicas canónicas, p. ej. ['Python', 'SQL', 'RAG']."
    )
    modalidad: Literal["remoto", "bogota_hibrido", "cualquiera"] = Field(
        default="cualquiera",
        description="Filtro de ubicación/modalidad de trabajo.",
    )
    max_aspiracion_usd: int = Field(
        default=10_000,
        ge=1000,
        le=25_000,
        description="Tope salarial mensual en USD.",
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Máximo de candidatos a devolver.")


def buscar_candidatos_poka_yoke(params: BuscarCandidatosInput) -> dict:
    desconocidas = [h for h in params.habilidades_requeridas if h not in CATALOGO_HABILIDADES]
    if desconocidas:
        sugerencias = {
            h: get_close_matches(h, CATALOGO_HABILIDADES, n=2, cutoff=0.5)
            for h in desconocidas
        }
        return {
            "ok": False,
            "error": f"Habilidades no reconocidas en el catálogo: {desconocidas}",
            "sugerencias_catalogo": sugerencias,
            "catalogo_disponible": CATALOGO_HABILIDADES,
        }

    reqs = set(params.habilidades_requeridas)
    resultados = []
    for c in CANDIDATOS.values():
        if c["estado_ats"] != "activo":
            continue
        if c["aspiracion_usd"] > params.max_aspiracion_usd:
            continue
        if params.modalidad == "bogota_hibrido" and c["ciudad"] != "Bogotá":
            continue
        faltantes = sorted(reqs - set(c["habilidades"]))
        cobertura = round((len(reqs) - len(faltantes)) / max(1, len(reqs)), 2)
        if cobertura > 0:
            resultados.append({
                "id": c["id"],
                "nombre": c["nombre"],
                "cobertura_requisitos": cobertura,
                "habilidades_faltantes": faltantes,
                "aspiracion_usd": c["aspiracion_usd"],
                "anos_experiencia": c["anos_experiencia"],
            })

    resultados.sort(key=lambda x: (-x["cobertura_requisitos"], x["aspiracion_usd"]))
    recorte = resultados[: params.top_k]
    return {
        "ok": True,
        "total_coincidencias": len(resultados),
        "mostrando": len(recorte),
        "candidatos": recorte,
    }


if __name__ == "__main__":
    print("=== 1. Llamada con errata en habilidad ('Postgress') ===")
    mal = BuscarCandidatosInput(habilidades_requeridas=["Python", "Postgress"], max_aspiracion_usd=6500)
    print(json.dumps(buscar_candidatos_poka_yoke(mal), indent=2, ensure_ascii=False))

    print("\n=== 2. Llamada corregida por el agente en el siguiente turno ===")
    bien = BuscarCandidatosInput(habilidades_requeridas=["Python", "Postgres"], max_aspiracion_usd=6500)
    print(json.dumps(buscar_candidatos_poka_yoke(bien), indent=2, ensure_ascii=False))
