"""Servidor MCP minimalista sobre JSON-RPC 2.0 para el sistema ATS (resources/list, resources/read, tools/list, tools/call)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import VACANTES, CANDIDATOS


class ServidorMCPATS:
    def manejar_rpc(self, peticion: dict) -> dict:
        req_id = peticion.get("id", 1)
        metodo = peticion.get("method")
        params = peticion.get("params") or {}

        if metodo == "resources/list":
            recursos = [
                {"uri": f"ats://vacantes/{vid}", "name": v["titulo"], "mimeType": "application/json"}
                for vid, v in VACANTES.items()
            ]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": recursos}}

        if metodo == "resources/read":
            uri = params.get("uri", "")
            vid = uri.removeprefix("ats://vacantes/")
            if vid not in VACANTES:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32002, "message": f"Recurso no encontrado: {uri}"}}
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(VACANTES[vid], ensure_ascii=False)}]},
            }

        if metodo == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {
                            "name": "ats_buscar_candidatos",
                            "description": "Busca candidatos activos que cumplan habilidades y tope salarial.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "habilidades": {"type": "array", "items": {"type": "string"}},
                                    "max_usd": {"type": "integer"},
                                },
                                "required": ["habilidades", "max_usd"],
                            },
                        }
                    ]
                },
            }

        if metodo == "tools/call":
            nombre = params.get("name")
            args = params.get("arguments") or {}
            if nombre == "ats_buscar_candidatos":
                reqs = set(args.get("habilidades", []))
                max_usd = int(args.get("max_usd", 10000))
                hallados = [
                    {"id": c["id"], "nombre": c["nombre"], "aspiracion_usd": c["aspiracion_usd"]}
                    for c in CANDIDATOS.values()
                    if c["estado_ats"] == "activo" and c["aspiracion_usd"] <= max_usd and reqs.issubset(c["habilidades"])
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(hallados, ensure_ascii=False)}], "isError": False},
                }

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Método no soportado: {metodo}"}}


if __name__ == "__main__":
    srv = ServidorMCPATS()
    print("1. resources/list ->", json.dumps(srv.manejar_rpc({"jsonrpc": "2.0", "id": 1, "method": "resources/list"}), indent=2, ensure_ascii=False))
    print("2. tools/call ->", json.dumps(srv.manejar_rpc({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "ats_buscar_candidatos", "arguments": {"habilidades": ["Python", "SQL", "RAG"], "max_usd": 6500}},
    }), indent=2, ensure_ascii=False))
