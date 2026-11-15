"""Checkpoints en disco e idempotencia: reanudar tras una caída sin duplicar efectos secundarios."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import (
    SALIDA,
    clave_idempotencia,
    ejecutar_herramienta_ats,
    herramientas_ats,
    imprimir,
)
from comun.ag_modelo import crear_modelo

RUTA_CHECKPOINT = SALIDA / "m2_checkpoint.json"


class EjecutorConCheckpoint:
    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.efectos_externos: list[dict] = []  # entrevistas realmente creadas en el calendario externo

    def guardar(self, estado: dict) -> None:
        self.ruta.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")

    def cargar_o_iniciar(self, vacante_id: str) -> dict:
        if self.ruta.exists():
            return json.loads(self.ruta.read_text(encoding="utf-8"))
        return {
            "vacante_id": vacante_id,
            "paso": 0,
            "mensajes": [
                {"role": "system", "content": "Preselecciona candidatos elegibles, agenda entrevistas y entrega la terna."},
                {"role": "user", "content": f"Preselecciona y agenda entrevistas para {vacante_id}."},
            ],
            "cache_idempotencia": {},
            "completado": False,
            "terna": [],
        }

    def ejecutar_herramienta_idempotente(self, estado: dict, nombre: str, args: dict) -> tuple[dict, bool]:
        """Si la misma llamada ya se ejecutó antes, devuelve el resultado cacheado sin repetir el efecto."""
        clave = clave_idempotencia(nombre, args)
        if clave in estado["cache_idempotencia"]:
            return estado["cache_idempotencia"][clave], True
        res = ejecutar_herramienta_ats(nombre, args)
        if nombre == "agendar_entrevista" and res.get("ok"):
            self.efectos_externos.append({"clave": clave, **args})
        estado["cache_idempotencia"][clave] = res
        return res, False

    def correr(self, vacante_id: str, *, simular_caida_en_paso: int | None = None) -> dict:
        estado = self.cargar_o_iniciar(vacante_id)
        modelo = crear_modelo(agenda=True)
        esquemas = herramientas_ats(
            "obtener_vacante",
            "buscar_candidatos",
            "consultar_ficha_candidato",
            "verificar_elegibilidad",
            "agendar_entrevista",
            "entregar_terna",
        )

        while not estado["completado"]:
            if simular_caida_en_paso is not None and estado["paso"] == simular_caida_en_paso:
                self.guardar(estado)
                raise RuntimeError(f"Caída simulada del proceso en el paso {estado['paso']}")

            r = modelo.responder(estado["mensajes"], esquemas)
            estado["paso"] += 1
            if not r.llamadas:
                break

            estado["mensajes"].append(
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
            for tc in r.llamadas:
                res, _ = self.ejecutar_herramienta_idempotente(estado, tc.nombre, tc.argumentos)
                estado["mensajes"].append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
                if tc.nombre == "entregar_terna":
                    estado["terna"] = sorted(res.get("candidatos") or [])
                    estado["completado"] = True

            self.guardar(estado)

        return estado


if __name__ == "__main__":
    if RUTA_CHECKPOINT.exists():
        RUTA_CHECKPOINT.unlink()

    ejecutor = EjecutorConCheckpoint(RUTA_CHECKPOINT)

    # 1) Primera corrida: el proceso se cae justo en el paso 6 (mitad de la preselección)
    try:
        ejecutor.correr("VAC-101", simular_caida_en_paso=6)
    except RuntimeError as e:
        cp = json.loads(RUTA_CHECKPOINT.read_text(encoding="utf-8"))
        imprimir("1. Proceso interrumpido: estado guardado en checkpoint", {
            "error": str(e),
            "pasos_guardados": cp["paso"],
            "llamadas_en_cache_idempotencia": len(cp["cache_idempotencia"]),
        })

    # 2) Reanudación desde el checkpoint: continúa desde el paso 6 hasta terminar
    final = ejecutor.correr("VAC-101", simular_caida_en_paso=None)
    # 3) Probamos un reintento duplicado de agendar_entrevista con los mismos argumentos
    _, fue_cacheado = ejecutor.ejecutar_herramienta_idempotente(
        final,
        "agendar_entrevista",
        {"vacante_id": "VAC-101", "candidato_id": "CAND-01", "fecha": "2026-11-20T15:00"},
    )
    imprimir("2. Ejecución reanudada e idempotencia comprobada", {
        "pasos_totales": final["paso"],
        "terna": final["terna"],
        "entrevistas_creadas_en_calendario": len(ejecutor.efectos_externos),
        "reintento_duplicado_bloqueado_por_cache": fue_cacheado,
    })
