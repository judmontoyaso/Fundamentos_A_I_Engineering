"""Comparación cuantitativa de tokens facturados: agente monolítico vs. subagentes con contexto limpio."""
from __future__ import annotations

import json


def simular_costo_tokens(num_candidatos: int = 6, tokens_cv_crudo: int = 2500, tokens_resumen: int = 140) -> dict:
    # En un agente monolítico, al evaluar al candidato k ya están en el contexto los (k-1) CVs anteriores completos
    tokens_monolitico = sum(800 + k * tokens_cv_crudo for k in range(1, num_candidatos + 1))

    # Con subagentes aislados, cada subagente lee 1 solo CV (600 prompt + 2500 CV) y el orquestador solo lee los 6 resúmenes
    tokens_subagentes = num_candidatos * (600 + tokens_cv_crudo) + (800 + num_candidatos * tokens_resumen)

    ahorro_pct = round((1 - tokens_subagentes / tokens_monolitico) * 100, 1)
    return {
        "candidatos_evaluados": num_candidatos,
        "tokens_entrada_monolitico": tokens_monolitico,
        "tokens_entrada_subagentes": tokens_subagentes,
        "ahorro_porcentual": f"{ahorro_pct}%",
    }


if __name__ == "__main__":
    print(json.dumps(simular_costo_tokens(num_candidatos=8), indent=2, ensure_ascii=False))
