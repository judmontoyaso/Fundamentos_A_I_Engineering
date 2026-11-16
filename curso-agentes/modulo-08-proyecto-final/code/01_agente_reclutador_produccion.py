"""Proyecto integrador: agente reclutador con presupuesto, máquina de estados, defensa de inyección, idempotencia y firma de aprobación."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import (
    CANDIDATOS,
    PresupuestoAgente,
    PresupuestoAgotado,
    VACANTES,
    clave_idempotencia,
    ejecutar_herramienta_ats,
    herramientas_ats,
    imprimir,
    terna_correcta,
)
from comun.ag_modelo import Modelo, crear_modelo


def sanitizar_ficha_cv(candidato: dict) -> dict:
    """Capa de aislamiento de datos no confiables: elimina instrucciones embebidas y conserva solo hechos tipados."""
    resumen = re.sub(r"\[[^\]]*\]", "", str(candidato.get("resumen_cv") or "")).strip()
    return {
        "id": candidato["id"],
        "nombre": candidato["nombre"],
        "ciudad": candidato["ciudad"],
        "remoto": bool(candidato["remoto"]),
        "anos_experiencia": int(candidato["anos_experiencia"]),
        "ingles": candidato["ingles"],
        "aspiracion_usd": int(candidato["aspiracion_usd"]),
        "disponibilidad_dias": int(candidato["disponibilidad_dias"]),
        "habilidades": list(candidato["habilidades"]),
        "ultimo_contacto_dias": int(candidato["ultimo_contacto_dias"]),
        "resumen_sanitizado": resumen[:160],
    }


@dataclass
class AgenteReclutadorProduccion:
    vacante_id: str
    presupuesto: PresupuestoAgente = field(default_factory=lambda: PresupuestoAgente(max_pasos=16, max_tokens=40_000, max_costo_usd=0.04))
    aprobador_humano: str | None = "comite.seleccion@empresa.co"

    def ejecutar(self, modelo: Modelo | None = None) -> dict:
        m = modelo or crear_modelo()
        # Mínimo privilegio: enviar_oferta NUNCA se expone al agente de preselección
        esquemas = herramientas_ats(
            "obtener_vacante",
            "buscar_candidatos",
            "consultar_ficha_candidato",
            "verificar_elegibilidad",
            "agendar_entrevista",
            "entregar_terna",
        )
        mensajes: list[dict] = [
            {
                "role": "system",
                "content": (
                    "Eres el Agente Reclutador de Producción. Carga la vacante, busca candidatos, "
                    "consulta sus fichas, verifica la elegibilidad de cada uno y entrega la terna."
                ),
            },
            {"role": "user", "content": f"Preselecciona la vacante {self.vacante_id}."},
        ]

        vacante_cargada = False
        candidatos_hallados: list[str] = []
        verificados: dict[str, bool] = {}
        cache_idem: dict[str, dict] = {}
        entrevistas_firmadas: list[dict] = []
        incidentes_seguridad: list[str] = []
        errores_recuperados = 0
        terna_final: list[str] = []
        estado_final = "en_curso"

        try:
            while True:
                self.presupuesto.abrir_paso()
                r = m.responder(mensajes, esquemas)
                self.presupuesto.registrar(r.tokens_entrada, r.tokens_salida)
                if not r.llamadas:
                    estado_final = "sin_llamadas"
                    break

                mensajes.append(
                    {
                        "role": "assistant",
                        "content": r.texto,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.nombre, "arguments": json.dumps(tc.argumentos, ensure_ascii=False)},
                            }
                            for tc in r.llamadas
                        ],
                    }
                )

                fin = False
                for tc in r.llamadas:
                    clave = clave_idempotencia(tc.nombre, tc.argumentos)
                    # Detector de bucle repetitivo: si repite exactamente la misma llamada 2 veces, abortamos
                    if clave in cache_idem and tc.nombre == "buscar_candidatos":
                        raise PresupuestoAgotado(f"bucle_repetitivo_detectado:{tc.nombre}")

                    if tc.nombre == "enviar_oferta":
                        incidentes_seguridad.append(f"Intento bloqueado de llamar herramienta prohibida: {tc.nombre}")
                        res = {"ok": False, "error": "Herramienta no autorizada en el perfil de preselección."}
                    elif tc.nombre == "consultar_ficha_candidato":
                        cid = str(tc.argumentos.get("candidato_id", ""))
                        if cid in CANDIDATOS:
                            if "[SISTEMA" in CANDIDATOS[cid]["resumen_cv"]:
                                incidentes_seguridad.append(f"Inyección detectada y neutralizada en ficha de {cid}")
                            res = {"ok": True, "candidato": sanitizar_ficha_cv(CANDIDATOS[cid])}
                        else:
                            res = {"ok": False, "error": "Candidato inexistente."}
                    elif tc.nombre == "agendar_entrevista":
                        cid = str(tc.argumentos.get("candidato_id", ""))
                        if not verificados.get(cid, False):
                            incidentes_seguridad.append(f"Intento de agendar a {cid} sin elegibilidad verificada.")
                            res = {"ok": False, "error": "Solo se puede agendar a candidatos verificados como elegibles."}
                        elif not self.aprobador_humano:
                            res = {"ok": False, "error": "Falta firma de aprobación humana (HITL)."}
                        else:
                            res = cache_idem.get(clave) or ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
                            res["firmado_por"] = self.aprobador_humano
                            if clave not in cache_idem:
                                entrevistas_firmadas.append(res)
                    elif tc.nombre == "entregar_terna":
                        if not vacante_cargada:
                            res = {"ok": False, "error": "Primero debes cargar la vacante."}
                        else:
                            # Invariante dura: si el modelo olvidó verificar algún candidato hallado, el controlador lo verifica
                            for cid in candidatos_hallados:
                                if cid not in verificados:
                                    v_res = ejecutar_herramienta_ats(
                                        "verificar_elegibilidad", {"vacante_id": self.vacante_id, "candidato_id": cid}
                                    )
                                    verificados[cid] = bool(v_res.get("elegible"))
                            terna_final = sorted(c for c, ok in verificados.items() if ok)
                            res = ejecutar_herramienta_ats(
                                "entregar_terna",
                                {
                                    "vacante_id": self.vacante_id,
                                    "candidatos": terna_final,
                                    "justificacion": tc.argumentos.get("justificacion", ""),
                                },
                            )
                            estado_final = "completado"
                            fin = True
                    else:
                        res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
                        if tc.nombre == "obtener_vacante" and res.get("ok"):
                            vacante_cargada = True
                        elif tc.nombre == "buscar_candidatos":
                            if res.get("ok"):
                                candidatos_hallados = [c["id"] for c in res.get("candidatos", [])]
                            else:
                                errores_recuperados += 1
                        elif tc.nombre == "verificar_elegibilidad" and res.get("ok"):
                            verificados[str(tc.argumentos.get("candidato_id"))] = bool(res.get("elegible"))

                    cache_idem[clave] = res
                    mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})

                if fin:
                    break
        except PresupuestoAgotado as exc:
            estado_final = f"cortado:{exc}"

        # Cálculo de pasos óptimos: 1 (vacante) + 1 (búsqueda) + 2*N (ficha+verificación) + agendas + 1 (terna)
        pasos_optimos = 3 + 2 * len(candidatos_hallados) + len(entrevistas_firmadas)
        eficiencia = round(min(1.0, pasos_optimos / max(self.presupuesto.pasos, 1)), 3) if estado_final == "completado" else 0.0

        return {
            "vacante_id": self.vacante_id,
            "titulo_vacante": VACANTES[self.vacante_id]["titulo"],
            "estado_final": estado_final,
            "terna": terna_final,
            "exacta": terna_final == terna_correcta(self.vacante_id),
            "entrevistas_firmadas": entrevistas_firmadas,
            "incidentes_seguridad": incidentes_seguridad,
            "errores_herramienta_recuperados": errores_recuperados,
            "eficiencia_trayectoria": eficiencia,
            "presupuesto": self.presupuesto.resumen(),
        }


if __name__ == "__main__":
    agente_101 = AgenteReclutadorProduccion("VAC-101")
    imprimir("1. Producción VAC-101 (con entrevista firmada e inyección neutralizada)", agente_101.ejecutar(crear_modelo(agenda=True)))

    agente_102 = AgenteReclutadorProduccion("VAC-102")
    imprimir("2. Producción VAC-102 (vacante remota de plataforma)", agente_102.ejecutar(crear_modelo(agenda=True)))
