"""Evaluación de un agente en dos niveles: calidad del resultado final (F1) y salud de la trayectoria."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import PresupuestoAgente, ejecutar_herramienta_ats, herramientas_ats, imprimir, terna_correcta
from comun.ag_modelo import Modelo, crear_modelo


def ejecutar_y_trazar(modelo: Modelo, vacante_id: str) -> dict:
    presupuesto = PresupuestoAgente(max_pasos=18)
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": "Preselecciona candidatos elegibles y entrega la terna."},
        {"role": "user", "content": f"Preselecciona la vacante {vacante_id}."},
    ]
    pasos_traza: list[dict] = []
    terna: list[str] = []

    while True:
        presupuesto.abrir_paso()
        r = modelo.responder(mensajes, esquemas)
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
            res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
            pasos_traza.append({"herramienta": tc.nombre, "args": tc.argumentos, "ok": bool(res.get("ok", True))})
            mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
            if tc.nombre == "entregar_terna":
                terna = sorted(res.get("candidatos") or [])
                fin = True
        if fin:
            break

    return {"vacante_id": vacante_id, "terna": terna, "pasos": pasos_traza, "presupuesto": presupuesto.resumen()}


def evaluar_corrida(corrida: dict, pasos_optimos: int) -> dict:
    esperada = set(terna_correcta(corrida["vacante_id"]))
    obtenida = set(corrida["terna"])
    aciertos = len(esperada & obtenida)
    precision = aciertos / len(obtenida) if obtenida else 0.0
    recall = aciertos / len(esperada) if esperada else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    pasos = corrida["pasos"]
    fallos_herramienta = sum(1 for p in pasos if not p["ok"])
    verificados = {p["args"].get("candidato_id") for p in pasos if p["herramienta"] == "verificar_elegibilidad" and p["ok"]}
    sin_verificar = sorted(obtenida - verificados)

    return {
        "vacante_id": corrida["vacante_id"],
        "exact_match": obtenida == esperada,
        "f1_terna": round(f1, 3),
        "pasos_reales": len(pasos),
        "pasos_optimos": pasos_optimos,
        # Menos pasos que el óptimo no es "más eficiente": significa que se saltó trabajo obligatorio.
        # Por eso la eficiencia se acota a 1 y el atajo se reporta aparte.
        "eficiencia_trayectoria": round(min(1.0, pasos_optimos / max(len(pasos), 1)), 3),
        "pasos_saltados": max(0, pasos_optimos - len(pasos)),
        "errores_herramienta": fallos_herramienta,
        "recuperado_de_errores": fallos_herramienta > 0 and (obtenida == esperada),
        "violaciones_politica_sin_verificar": sin_verificar,
    }


if __name__ == "__main__":
    # Para VAC-101 la búsqueda devuelve 4 candidatos -> óptimo = 1 (vacante) + 1 (búsqueda) + 4*2 (ficha+verif) + 1 (entrega) = 11 llamadas
    optimo_v101 = 11
    c_limpia = ejecutar_y_trazar(crear_modelo(), "VAC-101")
    c_errata = ejecutar_y_trazar(crear_modelo(errata=True), "VAC-101")
    c_descuido = ejecutar_y_trazar(crear_modelo(p_descuido=0.6, semilla=7), "VAC-101")

    imprimir("1. Trayectoria óptima sin defectos", evaluar_corrida(c_limpia, optimo_v101))
    imprimir("2. Trayectoria con errata y autocorrección (1 paso extra)", evaluar_corrida(c_errata, optimo_v101))
    imprimir("3. Trayectoria con descuido (viola política y falla F1)", evaluar_corrida(c_descuido, optimo_v101))
