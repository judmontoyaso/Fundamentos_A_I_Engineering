"""Cálculo empírico de pass@k vs. pass^k (consistencia en producción) sobre múltiples corridas."""
from __future__ import annotations

import json
import math


def metricas_confiabilidad(exitos: int, total_corridas: int, k: int = 5) -> dict:
    p = exitos / total_corridas
    # pass@k: probabilidad de al menos 1 éxito en k intentos
    pass_at_k = 1.0 - ((1.0 - p) ** k)
    # pass^k: probabilidad de que los k intentos seguidos tengan éxito
    pass_hat_k = p ** k
    return {
        "tasa_base_p": round(p, 3),
        f"pass@{k}": round(pass_at_k, 4),
        f"pass^{k}": round(pass_hat_k, 4),
        "interpretacion": (
            f"Con p={p:.0%}, en {k} tareas reales seguidas solo tienes {pass_hat_k:.1%} de probabilidad de no fallar ninguna."
        ),
    }


if __name__ == "__main__":
    for exitos in (7, 9, 10):
        print(json.dumps(metricas_confiabilidad(exitos, total_corridas=10, k=5), indent=2, ensure_ascii=False))
