"""Servidor MCP (Model Context Protocol) sobre JSON-RPC 2.0 y transporte stdio con aislamiento de credenciales."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import ESQUEMAS_HERRAMIENTAS, ejecutar_herramienta_ats, imprimir

PROTOCOLO_MCP = "2024-11-05"
NOMBRES_EXPUESTOS = (
    "obtener_vacante",
    "buscar_candidatos",
    "consultar_ficha_candidato",
    "verificar_elegibilidad",
    "entregar_terna",
)


def catalogo_mcp_tools() -> list[dict]:
    """Traduce los esquemas del ATS al formato estándar de tools/list del protocolo MCP."""
    tools = []
    for base in NOMBRES_EXPUESTOS:
        fn = ESQUEMAS_HERRAMIENTAS[base]["function"]
        tools.append(
            {
                "name": f"ats_{base}",
                "description": fn["description"],
                "inputSchema": fn["parameters"],
            }
        )
    return tools


def procesar_mensaje_jsonrpc(msg: dict) -> dict | None:
    """Atiende una petición JSON-RPC 2.0 del protocolo MCP (initialize, tools/list, tools/call)."""
    metodo = msg.get("method", "")
    req_id = msg.get("id")

    # Las notificaciones (sin id) no devuelven respuesta JSON-RPC
    if req_id is None:
        return None

    # Comprueba que el servidor tenga su credencial privada inyectada en su propio proceso
    if not os.getenv("ATS_DB_SECRET"):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32001, "message": "Servidor MCP sin credencial ATS_DB_SECRET configurada."},
        }

    if metodo == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOLO_MCP,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "mcp-ats-reclutamiento", "version": "1.0.0"},
            },
        }

    if metodo == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": catalogo_mcp_tools()}}

    if metodo == "tools/call":
        params = msg.get("params") or {}
        nombre = str(params.get("name") or "")
        argumentos = params.get("arguments") or {}
        resultado = ejecutar_herramienta_ats(nombre, argumentos)
        es_error = not bool(resultado.get("ok", True))
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(resultado, ensure_ascii=False)}],
                "isError": es_error,
            },
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Método no soportado: {metodo}"}}


def bucle_stdio() -> None:
    """Bucle de transporte stdio: lee una línea JSON-RPC por stdin y responde por stdout."""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        peticion = json.loads(linea)
        respuesta = procesar_mensaje_jsonrpc(peticion)
        if respuesta is not None:
            sys.stdout.write(json.dumps(respuesta, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        bucle_stdio()
    else:
        # Demostración autónoma cuando se ejecuta directamente desde la terminal
        os.environ.setdefault("ATS_DB_SECRET", "sec-demo-local-ats-9981")
        init_resp = procesar_mensaje_jsonrpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        list_resp = procesar_mensaje_jsonrpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        call_resp = procesar_mensaje_jsonrpc({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "ats_obtener_vacante", "arguments": {"vacante_id": "VAC-101"}},
        })
        imprimir("1. Handshake MCP (initialize)", init_resp)
        imprimir("2. Catálogo descubierto (tools/list)", [t["name"] for t in list_resp["result"]["tools"]])
        imprimir("3. Ejecución JSON-RPC (tools/call -> ats_obtener_vacante)", call_resp)
