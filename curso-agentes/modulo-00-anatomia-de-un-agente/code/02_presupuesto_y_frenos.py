"""Guardia de presupuesto y detector de bucles repetitivos para un agente en producción."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import PresupuestoAgente, clave_idempotencia


class ControladorAgente:
    def __init__(self, presupuesto: PresupuestoAgente) -> None:
        self.presupuesto = presupuesto
        self.llamadas_previas: set[str] = set()

    def ejecutar_herramienta(self, nombre: str, argumentos: dict, fn) -> dict:
        self.presupuesto.registrar_paso(tokens=600, costo_por_1k=0.002)
        huella = clave_idempotencia(nombre, argumentos)
        if huella in self.llamadas_previas:
            return {
                "ok": False,
                "error_tipo": "LLAMADA_DUPLICADA",
                "sugerencia": f"Ya llamaste a '{nombre}' con {argumentos}. Cambia los filtros o avanza con los datos actuales.",
            }
        self.llamadas_previas.add(huella)
        return {"ok": True, "datos": fn(**argumentos)}


if __name__ == "__main__":
    ctrl = ControladorAgente(PresupuestoAgente(max_pasos=4, max_tokens=5000, max_costo_usd=0.02))
    buscar = lambda ciudad: [f"Candidato en {ciudad}"]

    print("Llamada 1:", ctrl.ejecutar_herramienta("buscar", {"ciudad": "Bogotá"}, buscar))
    print("Llamada 2 (repetida):", ctrl.ejecutar_herramienta("buscar", {"ciudad": "Bogotá"}, buscar))
    print("Presupuesto actual:", json.dumps(ctrl.presupuesto.__dict__, indent=2))
