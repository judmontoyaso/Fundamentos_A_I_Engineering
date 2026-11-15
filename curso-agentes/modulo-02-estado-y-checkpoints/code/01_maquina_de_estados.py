"""Máquina de estados explícita que restringe las transiciones y herramientas por etapa."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, CANDIDATOS

Etapa = Literal["inicio", "vacante_cargada", "candidatos_buscados", "elegibilidad_verificada", "completado"]

TRANSICIONES_VALIDAS: dict[Etapa, list[Etapa]] = {
    "inicio": ["vacante_cargada"],
    "vacante_cargada": ["candidatos_buscados"],
    "candidatos_buscados": ["elegibilidad_verificada"],
    "elegibilidad_verificada": ["completado"],
    "completado": [],
}


@dataclass
class EstadoAgente:
    ejecucion_id: str
    vacante_id: str
    etapa: Etapa = "inicio"
    requisitos: list[str] = field(default_factory=list)
    candidatos_ids: list[str] = field(default_factory=list)
    elegibles_ids: list[str] = field(default_factory=list)

    def transicionar(self, nueva: Etapa) -> None:
        if nueva not in TRANSICIONES_VALIDAS[self.etapa]:
            raise ValueError(f"Transición ilegal: {self.etapa} -> {nueva}")
        self.etapa = nueva


def avanzar_paso(estado: EstadoAgente) -> EstadoAgente:
    if estado.etapa == "inicio":
        vac = VACANTES[estado.vacante_id]
        estado.requisitos = list(vac["requisitos_obligatorios"])
        estado.transicionar("vacante_cargada")
    elif estado.etapa == "vacante_cargada":
        reqs = set(estado.requisitos)
        estado.candidatos_ids = [
            c["id"] for c in CANDIDATOS.values()
            if len(reqs.intersection(c["habilidades"])) >= 3
        ]
        estado.transicionar("candidatos_buscados")
    elif estado.etapa == "candidatos_buscados":
        vac = VACANTES[estado.vacante_id]
        estado.elegibles_ids = [
            cid for cid in estado.candidatos_ids
            if CANDIDATOS[cid]["estado_ats"] == "activo"
            and CANDIDATOS[cid]["aspiracion_usd"] <= vac["presupuesto_usd_mes"]
        ]
        estado.transicionar("elegibilidad_verificada")
    elif estado.etapa == "elegibilidad_verificada":
        estado.transicionar("completado")
    return estado


if __name__ == "__main__":
    est = EstadoAgente(ejecucion_id="run-001", vacante_id="VAC-101")
    while est.etapa != "completado":
        avanzar_paso(est)
        print(f"[{est.etapa}] -> {json.dumps(asdict(est), ensure_ascii=False)}")
