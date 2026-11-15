"""Memoria episódica indexada por vacante para recordar preferencias verificadas entre sesiones."""
from __future__ import annotations

import json


class MemoriaEpisodicaATS:
    def __init__(self) -> None:
        self._memorias: dict[str, list[dict]] = {}

    def registrar_aprendizaje(self, vacante_id: str, regla: str, autor: str) -> None:
        self._memorias.setdefault(vacante_id, []).append({"regla": regla, "autor": autor})

    def recuperar_contexto(self, vacante_id: str) -> str:
        notas = self._memorias.get(vacante_id, [])
        if not notas:
            return "Sin preferencias previas registradas para esta vacante."
        lineas = [f"- {n['regla']} (validado por {n['autor']})" for n in notas]
        return "Preferencias históricas de esta vacante:\n" + "\n".join(lineas)


if __name__ == "__main__":
    mem = MemoriaEpisodicaATS()
    mem.registrar_aprendizaje(
        "VAC-101",
        "Priorizar candidatos con experiencia práctica en evaluación de LLMs aunque tengan 4 años en vez de 5.",
        "Líder Técnico de IA",
    )
    mem.registrar_aprendizaje(
        "VAC-101",
        "Descartar perfiles que no puedan asistir 2 días por semana a la oficina de Bogotá.",
        "Talent Acquisition",
    )
    print(mem.recuperar_contexto("VAC-101"))
