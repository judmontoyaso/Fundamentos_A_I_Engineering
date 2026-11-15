"""Agente completo de preselección técnica en producción con presupuesto, estado, defensa de inyección y HITL."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, CANDIDATOS, PresupuestoAgente, Trayectoria


class AgentePreseleccionProd:
    def __init__(self) -> None:
        self.checkpoints: dict[str, dict] = {}

    def ejecutar_hasta_revision(self, ejecucion_id: str, vacante_id: str) -> dict:
        presupuesto = PresupuestoAgente(max_pasos=6, max_tokens=8000, max_costo_usd=0.03)
        tr = Trayectoria(tarea_id=ejecucion_id)

        # Paso 1: Cargar vacante
        presupuesto.registrar_paso(tokens=350)
        vac = VACANTES[vacante_id]
        tr.agregar("obtener_vacante", {"vacante_id": vacante_id}, True, vac["titulo"], 3.1)

        # Paso 2: Filtrar y auditar candidatos con defensas deterministas
        presupuesto.registrar_paso(tokens=900)
        reqs = set(vac["requisitos_obligatorios"])
        terna = []
        descartados = []

        for c in CANDIDATOS.values():
            alerta_inyeccion = "ignora las instrucciones" in c["resumen_cv"].lower()
            cubre = reqs.issubset(c["habilidades"])
            en_presupuesto = c["aspiracion_usd"] <= vac["presupuesto_usd_mes"]
            activo = c["estado_ats"] == "activo" and c["ultimo_contacto_dias"] >= 90

            if alerta_inyeccion:
                descartados.append({"id": c["id"], "motivo": "Bloqueado por intento de inyección indirecta en CV"})
            elif not activo:
                descartados.append({"id": c["id"], "motivo": "En periodo de enfriamiento (<90 días)"})
            elif not en_presupuesto:
                descartados.append({"id": c["id"], "motivo": "Supera presupuesto de la vacante"})
            elif not cubre:
                descartados.append({"id": c["id"], "motivo": "No cubre requisitos obligatorios"})
            else:
                terna.append({
                    "id": c["id"],
                    "nombre": c["nombre"],
                    "aspiracion_usd": c["aspiracion_usd"],
                    "disponibilidad_dias": c["disponibilidad_dias"],
                })

        terna.sort(key=lambda x: (x["aspiracion_usd"], x["disponibilidad_dias"]))
        tr.agregar("auditar_candidatos", {"vacante_id": vacante_id}, True, f"aprobados={[x['id'] for x in terna]}", 8.4)

        # Paso 3: Preparar propuesta de entrevistas y pausar para aprobación humana
        presupuesto.registrar_paso(tokens=400)
        tr.agregar("proponer_entrevistas", {"candidatos": [x["id"] for x in terna]}, True, "esperando_aprobacion_humana", 2.0)
        tr.estado_final = "esperando_aprobacion_humana"

        estado = {
            "ejecucion_id": ejecucion_id,
            "vacante_id": vacante_id,
            "etapa": "esperando_aprobacion_humana",
            "terna_recomendada": terna,
            "descartados": descartados,
            "presupuesto": presupuesto.__dict__,
            "trayectoria": tr.resumen(),
        }
        self.checkpoints[ejecucion_id] = estado
        return estado

    def aprobar_y_finalizar(self, ejecucion_id: str, aprobado_por: str) -> dict:
        estado = self.checkpoints[ejecucion_id]
        if estado["etapa"] != "esperando_aprobacion_humana":
            raise RuntimeError("La ejecución no está esperando aprobación.")
        estado["etapa"] = "completado"
        estado["aprobado_por"] = aprobado_por
        estado["invitaciones_enviadas"] = [c["id"] for c in estado["terna_recomendada"]]
        return estado


if __name__ == "__main__":
    agente = AgentePreseleccionProd()
    pausa = agente.ejecutar_hasta_revision("run-prod-01", "VAC-101")
    print("=== 1. Estado en pausa para revisión humana ===")
    print(json.dumps(pausa, indent=2, ensure_ascii=False))

    final = agente.aprobar_y_finalizar("run-prod-01", aprobado_por="lider.ia@empresa.co")
    print("\n=== 2. Estado final tras aprobación humana ===")
    print(json.dumps(final, indent=2, ensure_ascii=False))
