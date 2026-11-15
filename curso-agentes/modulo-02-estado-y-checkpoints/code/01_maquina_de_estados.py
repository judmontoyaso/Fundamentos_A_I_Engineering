"""Máquina de estados e invariantes en el controlador: impide cerrar la terna sin verificar elegibilidad."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import PresupuestoAgente, ejecutar_herramienta_ats, herramientas_ats, imprimir, terna_correcta
from comun.ag_modelo import crear_modelo


@dataclass
class EstadoPreseleccion:
    vacante_id: str
    vacante_cargada: bool = False
    candidatos_buscados: list[str] = field(default_factory=list)
    verificados: dict[str, bool] = field(default_factory=dict)

    def validar_transicion(self, herramienta: str, args: dict) -> str | None:
        """Devuelve un mensaje de bloqueo si la llamada viola las precondiciones del flujo, o None si es válida."""
        if herramienta == "buscar_candidatos" and not self.vacante_cargada:
            return "Precondición incumplida: primero debes llamar a obtener_vacante."
        if herramienta == "entregar_terna":
            propuestos = list(args.get("candidatos") or [])
            sin_verificar = [c for c in propuestos if c not in self.verificados]
            if sin_verificar:
                return (
                    f"Transición bloqueada: intentaste incluir {sin_verificar} en la terna sin haber llamado antes "
                    f"a verificar_elegibilidad para comprobar enfriamiento, inglés y modalidad."
                )
            no_elegibles = [c for c in propuestos if not self.verificados.get(c, False)]
            if no_elegibles:
                return f"Transición bloqueada: {no_elegibles} tienen motivos de bloqueo activos y no son elegibles."
        return None

    def registrar_resultado(self, herramienta: str, args: dict, res: dict) -> None:
        if herramienta == "obtener_vacante" and res.get("ok"):
            self.vacante_cargada = True
        elif herramienta == "buscar_candidatos" and res.get("ok"):
            self.candidatos_buscados = [c["id"] for c in res.get("candidatos", [])]
        elif herramienta == "verificar_elegibilidad" and res.get("ok"):
            self.verificados[str(args.get("candidato_id"))] = bool(res.get("elegible"))


def ejecutar_con_o_sin_guarda(*, usar_guarda: bool) -> dict:
    # Un modelo descuidado (p_descuido=1.0) da por elegibles a todos los candidatos de la búsqueda sin verificarlos.
    modelo = crear_modelo(p_descuido=1.0)
    estado = EstadoPreseleccion(vacante_id="VAC-101")
    presupuesto = PresupuestoAgente(max_pasos=20)
    esquemas = herramientas_ats()
    mensajes: list[dict] = [
        {"role": "system", "content": "Preselecciona la terna de candidatos elegibles para VAC-101."},
        {"role": "user", "content": "Preselecciona la vacante VAC-101."},
    ]
    terna: list[str] = []
    bloqueos_guarda: list[str] = []

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
            error_guarda = estado.validar_transicion(tc.nombre, tc.argumentos) if usar_guarda else None
            if error_guarda:
                bloqueos_guarda.append(error_guarda)
                # Si el modelo intentó cerrar sin verificar, el controlador fuerza la verificación pendiente
                sin_verif = [c for c in (tc.argumentos.get("candidatos") or []) if c not in estado.verificados]
                for cid in sin_verif:
                    ver = ejecutar_herramienta_ats("verificar_elegibilidad", {"vacante_id": "VAC-101", "candidato_id": cid})
                    estado.registrar_resultado("verificar_elegibilidad", {"candidato_id": cid}, ver)
                elegibles_reales = sorted(c for c, ok in estado.verificados.items() if ok)
                res = ejecutar_herramienta_ats(
                    "entregar_terna",
                    {"vacante_id": "VAC-101", "candidatos": elegibles_reales, "justificacion": "Filtrada por invariante de estado."},
                )
                terna = elegibles_reales
                mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
                fin = True
            else:
                res = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
                estado.registrar_resultado(tc.nombre, tc.argumentos, res)
                mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)})
                if tc.nombre == "entregar_terna":
                    terna = sorted(res.get("candidatos") or [])
                    fin = True
        if fin:
            break

    return {
        "guarda_activa": usar_guarda,
        "bloqueos_activados": bloqueos_guarda,
        "terna_entregada": terna,
        "terna_esperada": terna_correcta("VAC-101"),
        "exacta": terna == terna_correcta("VAC-101"),
    }


if __name__ == "__main__":
    imprimir("1. Sin máquina de estados (modelo descuidado cuela a CAND-04 y CAND-07)", ejecutar_con_o_sin_guarda(usar_guarda=False))
    imprimir("2. Con máquina de estados e invariantes (solo pasan candidatos verificados)", ejecutar_con_o_sin_guarda(usar_guarda=True))
