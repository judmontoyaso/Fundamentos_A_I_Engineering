"""Orquestador que delega la auditoría detallada de cada candidato a subagentes con contexto aislado."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, CANDIDATOS


async def subagente_auditor(vacante: dict, candidato: dict, semaforo: asyncio.Semaphore) -> dict:
    """Evalúa un candidato en una ventana de contexto limpia y devuelve solo un dictamen compacto."""
    async with semaforo:
        await asyncio.sleep(0.05)  # Simula latencia de red de la llamada al LLM del subagente
        reqs = set(vacante["requisitos_obligatorios"])
        cubre = sorted(reqs.intersection(candidato["habilidades"]))
        faltan = sorted(reqs - set(candidato["habilidades"]))
        en_presupuesto = candidato["aspiracion_usd"] <= vacante["presupuesto_usd_mes"]
        activo = candidato["estado_ats"] == "activo"

        puntaje = round((len(cubre) / len(reqs)) * 70 + (30 if (en_presupuesto and activo) else 0), 1)
        return {
            "candidato_id": candidato["id"],
            "nombre": candidato["nombre"],
            "puntaje": puntaje,
            "aprobado_tecnico": puntaje >= 80,
            "fortalezas": cubre,
            "brechas": faltan,
            "riesgo_ats": None if activo else "En enfriamiento (<90 días)",
        }


async def orquestador_preseleccion(vacante_id: str, max_concurrencia: int = 3) -> dict:
    t0 = time.perf_counter()
    vac = VACANTES[vacante_id]
    semaforo = asyncio.Semaphore(max_concurrencia)
    tareas = [
        subagente_auditor(vac, cand, semaforo)
        for cand in CANDIDATOS.values()
        if cand["id"] != "CAND-04"
    ]
    dictamenes = await asyncio.gather(*tareas)
    dictamenes.sort(key=lambda d: -d["puntaje"])
    ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "vacante": vac["titulo"],
        "subagentes_lanzados": len(dictamenes),
        "latencia_total_ms": ms,
        "ranking": dictamenes,
    }


if __name__ == "__main__":
    resultado = asyncio.run(orquestador_preseleccion("VAC-101"))
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
