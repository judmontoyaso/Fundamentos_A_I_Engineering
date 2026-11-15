"""Poda de observaciones antiguas (observation masking) manteniendo intacto el estado estructurado."""
from __future__ import annotations

import json


def podar_historial_observaciones(mensajes: list[dict], ventana_reciente: int = 2) -> list[dict]:
    """Mantiene íntegras solo las últimas `ventana_reciente` observaciones de herramientas."""
    indices_tool = [i for i, m in enumerate(mensajes) if m.get("role") == "tool"]
    a_enmascarar = set(indices_tool[:-ventana_reciente]) if len(indices_tool) > ventana_reciente else set()

    salida = []
    for i, m in enumerate(mensajes):
        if i in a_enmascarar:
            salida.append({
                "role": "tool",
                "name": m.get("name", "herramienta"),
                "content": f"[Observación histórica de '{m.get('name')}' compactada: {len(m.get('content', ''))} caracteres archivados en estado]",
            })
        else:
            salida.append(m)
    return salida


if __name__ == "__main__":
    historial = [
        {"role": "system", "content": "Eres el agente de preselección técnica."},
        {"role": "tool", "name": "obtener_vacante", "content": json.dumps({"id": "VAC-101", "detalle": "x" * 600})},
        {"role": "tool", "name": "buscar_lote_1", "content": json.dumps({"candidatos": ["x" * 800]})},
        {"role": "tool", "name": "buscar_lote_2", "content": json.dumps({"candidatos": ["y" * 800]})},
        {"role": "tool", "name": "verificar_cand_01", "content": json.dumps({"id": "CAND-01", "elegible": True})},
    ]

    chars_antes = sum(len(m["content"]) for m in historial)
    podado = podar_historial_observaciones(historial, ventana_reciente=2)
    chars_despues = sum(len(m["content"]) for m in podado)

    print(f"Caracteres antes: {chars_antes} -> después de podar: {chars_despues}")
    print(json.dumps(podado, indent=2, ensure_ascii=False))
