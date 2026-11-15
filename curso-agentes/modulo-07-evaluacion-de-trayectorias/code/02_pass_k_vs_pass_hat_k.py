"""Métrica de consistencia en producción (τ-bench): cálculo empírico de pass@k frente a pass^k sobre N corridas."""
from __future__ import annotations

from math import comb
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, ejecutar_herramienta_ats, herramientas_ats, imprimir, terna_correcta
from comun.ag_modelo import crear_modelo


def correr_intento(vacante_id: str, *, p_descuido: float, semilla: int) -> bool:
    """Ejecuta una corrida completa del agente y devuelve True solo si la terna es exacta y verificada."""
    modelo = crear_modelo(p_descuido=p_descuido, semilla=semilla)
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": "Preselecciona candidatos elegibles y entrega la terna."},
        {"role": "user", "content": f"Preselecciona la vacante {vacante_id}."},
    ]
    verificados: set[str] = set()
    terna: list[str] = []

    for _ in range(18):
        r = modelo.responder(mensajes, esquemas)
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
            if tc.nombre == "verificar_elegibilidad" and res.get("ok"):
                verificados.add(str(tc.argumentos.get("candidato_id")))
            mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
            if tc.nombre == "entregar_terna":
                terna = sorted(res.get("candidatos") or [])
                fin = True
        if fin:
            break

    # Éxito estricto: terna idéntica a la verdad de negocio Y todos los incluidos fueron verificados
    return terna == terna_correcta(vacante_id) and set(terna).issubset(verificados)


def estimar_pass_at_k(n: int, c: int, k: int) -> float:
    """Estimador insesgado de Chen et al. (Codex): probabilidad de acertar AL MENOS 1 vez en k intentos."""
    if n - c < k:
        return 1.0
    return 1.0 - (comb(n - c, k) / comb(n, k))


def estimar_pass_hat_k(n: int, c: int, k: int) -> float:
    """Estimador combinatorio de τ-bench (Yao et al.): probabilidad de que LOS k intentos salgan TODOS bien."""
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def evaluar_consistencia(p_descuido: float, n_corridas: int = 8) -> dict:
    ks = (1, 2, 3, 5)
    por_vacante: dict[str, dict] = {}
    for idx_v, vid in enumerate(sorted(VACANTES.keys())):
        exitos = sum(
            1 for i in range(n_corridas)
            if correr_intento(vid, p_descuido=p_descuido, semilla=100 * (idx_v + 1) + i)
        )
        por_vacante[vid] = {
            "exitos": f"{exitos}/{n_corridas}",
            "pass@k": {f"k={k}": round(estimar_pass_at_k(n_corridas, exitos, k), 3) for k in ks},
            "pass^k": {f"k={k}": round(estimar_pass_hat_k(n_corridas, exitos, k), 3) for k in ks},
        }

    # Promedio en todo el conjunto de tareas (metodología τ-bench)
    promedio_at = {
        f"k={k}": round(sum(por_vacante[v]["pass@k"][f"k={k}"] for v in por_vacante) / len(por_vacante), 3)
        for k in ks
    }
    promedio_hat = {
        f"k={k}": round(sum(por_vacante[v]["pass^k"][f"k={k}"] for v in por_vacante) / len(por_vacante), 3)
        for k in ks
    }
    return {
        "p_descuido": p_descuido,
        "corridas_por_tarea": n_corridas,
        "por_tarea": por_vacante,
        "promedio_pass_at_k": promedio_at,
        "promedio_pass_hat_k": promedio_hat,
    }


if __name__ == "__main__":
    imprimir("1. Agente sin guarda de estado (p_descuido=0.25): pass@k sube a 1.0 pero pass^k se desploma", evaluar_consistencia(0.25))
    imprimir("2. Agente determinista / con invariantes (p_descuido=0.0): pass^5 se mantiene en 1.0", evaluar_consistencia(0.0))
