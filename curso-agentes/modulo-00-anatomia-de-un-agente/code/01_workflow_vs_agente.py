"""Compara un workflow fijo de 3 pasos frente a un bucle de agente exploratorio sobre el ATS."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, CANDIDATOS, Trayectoria


def workflow_fijo(vacante_id: str) -> dict:
    """Flujo determinista: 1) leer vacante, 2) filtrar candidatos elegibles, 3) ordenar por presupuesto."""
    t0 = time.perf_counter()
    vac = VACANTES[vacante_id]
    reqs = set(vac["requisitos_obligatorios"])
    elegibles = []
    for c in CANDIDATOS.values():
        if c["estado_ats"] != "activo":
            continue
        if c["aspiracion_usd"] > vac["presupuesto_usd_mes"]:
            continue
        if c["anos_experiencia"] < vac["anos_minimos"]:
            continue
        cobertura = len(reqs.intersection(c["habilidades"])) / len(reqs)
        if cobertura >= 0.75:
            elegibles.append({"id": c["id"], "nombre": c["nombre"], "cobertura": cobertura, "usd": c["aspiracion_usd"]})
    elegibles.sort(key=lambda x: (-x["cobertura"], x["usd"]))
    ms = round((time.perf_counter() - t0) * 1000, 3)
    return {"modo": "workflow_fijo", "pasos": 3, "latencia_ms": ms, "seleccionados": elegibles}


def agente_exploratorio(vacante_id: str) -> dict:
    """Agente que explora paso a paso y relaja restricciones si quedan pocos candidatos."""
    tr = Trayectoria(tarea_id=f"preseleccion_{vacante_id}")
    vac = VACANTES[vacante_id]
    tr.agregar("obtener_vacante", {"id": vacante_id}, True, json.dumps(vac, ensure_ascii=False), 4.2)

    # Paso 2: búsqueda estricta
    reqs = set(vac["requisitos_obligatorios"])
    estrictos = [
        c["id"] for c in CANDIDATOS.values()
        if c["estado_ats"] == "activo"
        and reqs.issubset(c["habilidades"])
        and c["aspiracion_usd"] <= vac["presupuesto_usd_mes"]
    ]
    tr.agregar("buscar_candidatos", {"estricto": True}, True, f"encontrados={estrictos}", 12.5)

    # Paso 3: inspeccionar cada candidato encontrado
    perfiles = []
    for cid in estrictos:
        c = CANDIDATOS[cid]
        tr.agregar("inspeccionar_ats", {"candidato_id": cid}, True, f"ultimo_contacto={c['ultimo_contacto_dias']}d", 6.1)
        perfiles.append({"id": cid, "nombre": c["nombre"], "aspiracion_usd": c["aspiracion_usd"]})

    tr.estado_final = "completado"
    return {"modo": "agente_exploratorio", **tr.resumen(), "seleccionados": perfiles}


if __name__ == "__main__":
    print("=== 1. Workflow determinista ===")
    print(json.dumps(workflow_fijo("VAC-101"), indent=2, ensure_ascii=False))
    print("\n=== 2. Agente exploratorio ===")
    print(json.dumps(agente_exploratorio("VAC-101"), indent=2, ensure_ascii=False))
