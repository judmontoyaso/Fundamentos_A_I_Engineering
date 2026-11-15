"""Evaluador de trayectorias: mide exactitud del resultado final, eficiencia de pasos y respeto de invariantes."""
from __future__ import annotations

import json


def evaluar_corrida_agente(
    esperados: set[str],
    predichos: set[str],
    herramientas_usadas: list[str],
    errores_herramienta: int,
    pasos_optimos: int = 3,
) -> dict:
    aciertos = len(esperados.intersection(predichos))
    precision = aciertos / len(predichos) if predichos else 0.0
    recall = aciertos / len(esperados) if esperados else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    pasos_reales = max(1, len(herramientas_usadas))
    eficiencia = min(1.0, pasos_optimos / pasos_reales)
    penalizacion_errores = min(0.5, errores_herramienta * 0.15)
    score_compuesto = max(0.0, round(f1 * (0.7 + 0.3 * eficiencia) - penalizacion_errores, 3))

    return {
        "f1_resultado": round(f1, 3),
        "pasos_reales": pasos_reales,
        "eficiencia_pasos": round(eficiencia, 3),
        "errores_herramienta": errores_herramienta,
        "score_compuesto": score_compuesto,
    }


if __name__ == "__main__":
    verdad = {"CAND-01", "CAND-03"}
    print("Agente limpio (3 pasos, 0 errores):", json.dumps(
        evaluar_corrida_agente(verdad, {"CAND-01", "CAND-03"}, ["obtener_vacante", "buscar", "verificar"], errores_herramienta=0),
        indent=2,
    ))
    print("Agente errático (8 pasos, 2 errores):", json.dumps(
        evaluar_corrida_agente(verdad, {"CAND-01", "CAND-03"}, ["buscar"] * 8, errores_herramienta=2),
        indent=2,
    ))
