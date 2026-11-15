"""Cliente MCP con filtro de herramientas (allowlist por etapa) para no saturar el contexto del agente."""
from __future__ import annotations

import json
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "servidor_mcp_ats",
    Path(__file__).resolve().parent / "01_servidor_mcp_ats.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ServidorMCPATS = mod.ServidorMCPATS


class ClienteMCPConFiltro:
    def __init__(self, servidor: ServidorMCPATS, herramientas_permitidas: set[str]) -> None:
        self.servidor = servidor
        self.permitidas = herramientas_permitidas

    def obtener_herramientas_para_llm(self) -> list[dict]:
        resp = self.servidor.manejar_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        todas = resp["result"]["tools"]
        return [t for t in todas if t["name"] in self.permitidas]

    def llamar_herramienta(self, nombre: str, argumentos: dict) -> dict:
        if nombre not in self.permitidas:
            raise PermissionError(f"La herramienta '{nombre}' no está autorizada en esta etapa del agente.")
        return self.servidor.manejar_rpc({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": nombre, "arguments": argumentos},
        })


if __name__ == "__main__":
    cliente = ClienteMCPConFiltro(ServidorMCPATS(), herramientas_permitidas={"ats_buscar_candidatos"})
    print("Herramientas expuestas al modelo:", json.dumps(cliente.obtener_herramientas_para_llm(), indent=2, ensure_ascii=False))
