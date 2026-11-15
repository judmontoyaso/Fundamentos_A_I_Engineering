"""Memoria episódica entre sesiones: el agente incorpora correcciones operativas sin reentrenar."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import SALIDA, ejecutar_herramienta_ats, herramientas_ats, imprimir
from comun.ag_modelo import crear_modelo

RUTA_MEMORIA = SALIDA / "m3_memoria_episodica.json"


class MemoriaEpisodica:
    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def listar(self, vacante_id: str) -> list[dict]:
        if not self.ruta.exists():
            return []
        todas = json.loads(self.ruta.read_text(encoding="utf-8"))
        return [r for r in todas if r.get("vacante_id") == vacante_id]

    def registrar_aprendizaje(self, vacante_id: str, regla: str, origen: str) -> None:
        todas = json.loads(self.ruta.read_text(encoding="utf-8")) if self.ruta.exists() else []
        todas.append({"vacante_id": vacante_id, "regla": regla, "origen": origen})
        self.ruta.write_text(json.dumps(todas, indent=2, ensure_ascii=False), encoding="utf-8")


def preseleccionar_con_memoria(vacante_id: str, memoria: MemoriaEpisodica) -> dict:
    recuerdos = memoria.listar(vacante_id)
    bloque_memoria = "\n".join(r["regla"] for r in recuerdos)
    sistema = "Eres el agente de preselección del ATS."
    if bloque_memoria:
        sistema += f"\nReglas aprendidas en sesiones previas para {vacante_id}:\n{bloque_memoria}"

    modelo = crear_modelo()
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": sistema},
        {"role": "user", "content": f"Preselecciona la vacante {vacante_id}."},
    ]
    terna: list[str] = []
    habilidades_buscadas: list[str] = []

    for _ in range(16):
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
            if tc.nombre == "buscar_candidatos":
                habilidades_buscadas = list(tc.argumentos.get("habilidades") or [])
            res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
            mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
            if tc.nombre == "entregar_terna":
                terna = sorted(res.get("candidatos") or [])
                fin = True
        if fin:
            break

    return {
        "vacante_id": vacante_id,
        "recuerdos_inyectados": len(recuerdos),
        "habilidades_buscadas": habilidades_buscadas,
        "terna": terna,
    }


if __name__ == "__main__":
    if RUTA_MEMORIA.exists():
        RUTA_MEMORIA.unlink()
    mem = MemoriaEpisodica(RUTA_MEMORIA)

    # Sesión 1: sin memoria previa, la vacante VAC-101 selecciona a CAND-01 y CAND-03
    s1 = preseleccionar_con_memoria("VAC-101", mem)
    imprimir("1. Sesión 1 (sin memoria previa)", s1)

    # El líder técnico corrige: para VAC-101 el equipo exige además experiencia demostrada en FastAPI
    mem.registrar_aprendizaje(
        "VAC-101",
        "REQUISITO_EXTRA: FastAPI",
        origen="revisión_humana_sesion_1",
    )

    # Sesión 2: el agente recupera el recuerdo episódico y filtra también por FastAPI -> solo CAND-01
    s2 = preseleccionar_con_memoria("VAC-101", mem)
    imprimir("2. Sesión 2 (con recuerdo episódico 'REQUISITO_EXTRA: FastAPI')", s2)
