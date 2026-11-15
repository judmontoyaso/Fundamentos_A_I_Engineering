"""Cliente MCP real: levanta el servidor en un subproceso aislado por stdio, descubre sus herramientas y corre el agente."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import PresupuestoAgente, imprimir, terna_correcta
from comun.ag_modelo import crear_modelo

RUTA_SERVIDOR = Path(__file__).with_name("01_servidor_mcp_ats.py")


class ClienteMCPStdio:
    """Cliente JSON-RPC 2.0 que se comunica con el servidor MCP hijo por tuberías stdin/stdout."""

    def __init__(self, script_servidor: Path) -> None:
        # El proceso padre (el agente) NO tiene ATS_DB_SECRET en su entorno; solo se le inyecta al subproceso MCP.
        entorno_hijo = {**os.environ, "ATS_DB_SECRET": "vault-ats-prod-token-7741"}
        self._proc = subprocess.Popen(
            [sys.executable, str(script_servidor), "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=entorno_hijo,
        )
        self._id = 0

    def _rpc(self, metodo: str, params: dict | None = None) -> dict:
        self._id += 1
        mensaje = {"jsonrpc": "2.0", "id": self._id, "method": metodo, "params": params or {}}
        assert self._proc.stdin and self._proc.stdout
        self._proc.stdin.write(json.dumps(mensaje, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()
        linea = self._proc.stdout.readline()
        if not linea:
            raise RuntimeError("El servidor MCP cerró la tubería inesperadamente.")
        resp = json.loads(linea)
        if "error" in resp:
            raise RuntimeError(f"Error MCP {resp['error']}")
        return resp["result"]

    def inicializar(self) -> dict:
        info = self._rpc("initialize", {"clientInfo": {"name": "agente-reclutador", "version": "1.0.0"}})
        assert self._proc.stdin
        self._proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self._proc.stdin.flush()
        return info

    def esquemas_openai(self) -> list[dict]:
        """Descubre las herramientas por MCP (tools/list) y las adapta al formato de tool calling del modelo."""
        lista = self._rpc("tools/list")["tools"]
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"],
                },
            }
            for t in lista
        ]

    def llamar_herramienta(self, nombre: str, argumentos: dict) -> dict:
        res = self._rpc("tools/call", {"name": nombre, "arguments": argumentos})
        texto = res["content"][0]["text"]
        return json.loads(texto)

    def cerrar(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            self._proc.wait(timeout=3)


def correr_agente_sobre_mcp(vacante_id: str) -> dict:
    # Verificamos que el proceso del agente NO conoce la credencial de la base de datos
    credencial_en_agente = os.getenv("ATS_DB_SECRET")
    cliente = ClienteMCPStdio(RUTA_SERVIDOR)
    try:
        handshake = cliente.inicializar()
        esquemas = cliente.esquemas_openai()
        modelo = crear_modelo()
        presupuesto = PresupuestoAgente(max_pasos=16)
        mensajes: list[dict] = [
            {"role": "system", "content": "Usa las herramientas MCP del servidor ATS para entregar la terna."},
            {"role": "user", "content": f"Preselecciona la vacante {vacante_id}."},
        ]
        terna: list[str] = []
        llamadas_mcp: list[str] = []

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
                llamadas_mcp.append(tc.nombre)
                salida = cliente.llamar_herramienta(tc.nombre, tc.argumentos)
                mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(salida, ensure_ascii=False)})
                if tc.nombre.endswith("entregar_terna"):
                    terna = sorted(salida.get("candidatos") or [])
                    fin = True
            if fin:
                break

        return {
            "servidor_mcp": handshake["serverInfo"],
            "protocolo": handshake["protocolVersion"],
            "credencial_visible_en_proceso_agente": credencial_en_agente is not None,
            "herramientas_descubiertas": [e["function"]["name"] for e in esquemas],
            "llamadas_mcp": llamadas_mcp,
            "terna": terna,
            "exacta": terna == terna_correcta(vacante_id),
        }
    finally:
        cliente.cerrar()


if __name__ == "__main__":
    imprimir("Agente ejecutado sobre subproceso MCP stdio con aislamiento de credenciales", correr_agente_sobre_mcp("VAC-101"))
