"""Checkpoints en disco/memoria y ejecución idempotente de herramientas con efectos secundarios."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import clave_idempotencia


class AlmacenCheckpoints:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self.efectos_externos_reales: list[str] = []

    def guardar(self, ejecucion_id: str, estado: dict) -> None:
        self._store[ejecucion_id] = json.loads(json.dumps(estado))

    def cargar(self, ejecucion_id: str) -> dict | None:
        return json.loads(json.dumps(self._store[ejecucion_id])) if ejecucion_id in self._store else None

    def ejecutar_efecto_idempotente(self, estado: dict, herramienta: str, args: dict) -> dict:
        key = clave_idempotencia(herramienta, {"run": estado["ejecucion_id"], **args})
        if key in estado["efectos_ejecutados"]:
            return {"reutilizado_de_checkpoint": True, "recibo": estado["efectos_ejecutados"][key]}

        # Simula el efecto real en el sistema externo (ej. escribir nota en el ATS)
        recibo = f"NOTA-ATS-{len(self.efectos_externos_reales) + 1}:{args['candidato_id']}"
        self.efectos_externos_reales.append(recibo)
        estado["efectos_ejecutados"][key] = recibo
        self.guardar(estado["ejecucion_id"], estado)
        return {"reutilizado_de_checkpoint": False, "recibo": recibo}


if __name__ == "__main__":
    cp = AlmacenCheckpoints()
    estado = {"ejecucion_id": "run-42", "candidatos": ["CAND-01", "CAND-03"], "efectos_ejecutados": {}}
    cp.guardar("run-42", estado)

    print("--- Intento 1: registra CAND-01 y luego sufre una caída antes de CAND-03 ---")
    print(cp.ejecutar_efecto_idempotente(estado, "registrar_nota_ats", {"candidato_id": "CAND-01"}))

    print("\n--- Intento 2 (reanudando desde checkpoint): vuelve a pasar por CAND-01 y sigue con CAND-03 ---")
    recuperado = cp.cargar("run-42")
    for cid in recuperado["candidatos"]:
        res = cp.ejecutar_efecto_idempotente(recuperado, "registrar_nota_ats", {"candidato_id": cid})
        print(f"Candidato {cid}: {res}")

    print("\nEfectos reales disparados en el servidor externo (sin duplicados):", cp.efectos_externos_reales)
