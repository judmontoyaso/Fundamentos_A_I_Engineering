"""Poda de observaciones viejas en la ventana de contexto para controlar el crecimiento cuadrático de tokens."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import PresupuestoAgente, ejecutar_herramienta_ats, herramientas_ats, imprimir, terna_correcta
from comun.ag_modelo import crear_modelo


def enriquecer_con_ruido(resultado: dict, nombre: str) -> dict:
    """Simula respuestas verbosas de una API empresarial (metadatos de auditoría, logs HTTP y texto redundante)."""
    if nombre == "consultar_ficha_candidato" and resultado.get("ok"):
        copia = copy.deepcopy(resultado)
        copia["auditoria_ats"] = ["evento_lectura_ficha_v2_registro_completo_" + str(i) for i in range(45)]
        return copia
    return resultado


def podar_observaciones_antiguas(mensajes: list[dict], conservar_ultimas: int = 2) -> list[dict]:
    """Comprime las salidas de herramientas antiguas dejando intactas las últimas `conservar_ultimas`."""
    indices_tool = [i for i, m in enumerate(mensajes) if m.get("role") == "tool"]
    a_podar = set(indices_tool[:-conservar_ultimas]) if len(indices_tool) > conservar_ultimas else set()
    podados: list[dict] = []
    for i, m in enumerate(mensajes):
        if i not in a_podar:
            podados.append(m)
            continue
        try:
            datos = json.loads(m["content"])
        except Exception:
            podados.append(m)
            continue
        if "candidato" in datos:
            c = datos["candidato"]
            resumen = {"ok": True, "candidato": {"id": c["id"], "nombre": c["nombre"], "resumen_podado": True}}
        else:
            resumen = {k: v for k, v in datos.items() if k != "auditoria_ats"}
        podados.append({**m, "content": json.dumps(resumen, ensure_ascii=False)})
    return podados


def correr_experimento(*, podar: bool) -> dict:
    modelo = crear_modelo()
    presupuesto = PresupuestoAgente(max_pasos=18)
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": "Preselecciona candidatos elegibles para VAC-101 y cierra con entregar_terna."},
        {"role": "user", "content": "Preselecciona la vacante VAC-101."},
    ]
    terna: list[str] = []

    while True:
        presupuesto.abrir_paso()
        vista_mensajes = podar_observaciones_antiguas(mensajes, conservar_ultimas=2) if podar else mensajes
        r = modelo.responder(vista_mensajes, esquemas)
        presupuesto.registrar(r.tokens_entrada, r.tokens_salida)
        if not r.llamadas:
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
            crudo = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
            verboso = enriquecer_con_ruido(crudo, tc.nombre)
            mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(verboso, ensure_ascii=False)})
            if tc.nombre == "entregar_terna":
                terna = sorted(crudo.get("candidatos") or [])
                fin = True
        if fin:
            break

    return {
        "poda_activa": podar,
        **presupuesto.resumen(),
        "terna": terna,
        "exacta": terna == terna_correcta("VAC-101"),
    }


if __name__ == "__main__":
    sin_poda = correr_experimento(podar=False)
    con_poda = correr_experimento(podar=True)
    ahorro_pct = round((1 - con_poda["tokens_entrada"] / sin_poda["tokens_entrada"]) * 100, 1)
    imprimir("1. Sin poda de observaciones (contexto acumulativo)", sin_poda)
    imprimir("2. Con poda de observaciones antiguas", {**con_poda, "ahorro_tokens_entrada_pct": ahorro_pct})
