"""
09 · Un cliente MCP: descubrir herramientas en tiempo de ejecución y usarlas.

Arranca el servidor de 08 como subproceso, le pregunta qué herramientas tiene, las
llama, y al final convierte lo que descubrió al formato de herramientas del script
06 (function calling). Ese último paso es todo lo que hace falta para que el bucle
del agente use herramientas MCP en vez de funciones locales.

No llama a ningún modelo ni necesita API key: aquí se ve el protocolo desnudo.

    python 09_mcp_cliente.py
"""
from __future__ import annotations
import asyncio
import json
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVIDOR = pathlib.Path(__file__).resolve().parent / "08_mcp_servidor.py"


def texto(resultado) -> str:
    """Un resultado MCP es una lista de bloques de contenido; aquí solo hay texto."""
    return "\n".join(b.text for b in resultado.content if getattr(b, "type", "") == "text")


def a_function_calling(tool) -> dict:
    """Herramienta MCP -> definición de herramienta de la API de Responses (la de 06).

    El input_schema de MCP ya es JSON Schema, así que casi no hay nada que traducir. No se marca
    strict=True: el modo estricto exige que todas las propiedades sean obligatorias, y el esquema
    que genera un servidor ajeno no tiene por qué cumplirlo.
    """
    return {"type": "function", "name": tool.name, "description": tool.description or "",
            "parameters": tool.input_schema}


async def main() -> None:
    # sys.executable: el mismo Python (y el mismo entorno virtual) con el que corre este script.
    parametros = StdioServerParameters(command=sys.executable, args=[str(SERVIDOR)])

    async with stdio_client(parametros) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            info = await sesion.initialize()                 # apretón de manos: versiones y capacidades
            print(f"Conectado a '{info.server_info.name}' · protocolo {info.protocol_version}\n")

            # 1) Descubrimiento. El cliente no sabía qué herramientas había hasta este momento.
            herramientas = (await sesion.list_tools()).tools
            print(f"El servidor ofrece {len(herramientas)} herramientas:")
            for t in herramientas:
                requeridos = t.input_schema.get("required", [])
                print(f"  - {t.name}({', '.join(t.input_schema['properties'])})  obligatorios: {requeridos}")
                print(f"      {(t.description or '').splitlines()[0]}")

            # 2) Llamadas. Es lo que haría tu bucle cuando el modelo pide una herramienta.
            print("\n--- buscar_cvs: streaming, solo seniors")
            r = await sesion.call_tool("buscar_cvs", {"consulta": "streaming kafka tiempo real", "nivel": "senior"})
            print(texto(r))

            print("\n--- ver_cv del primer resultado")
            r = await sesion.call_tool("ver_cv", {"cv_id": 1})
            print(texto(r))

            # 3) Dos formas de fallar, y no son la misma.
            print("\n--- un id que no existe: la herramienta responde con un error accionable")
            r = await sesion.call_tool("ver_cv", {"cv_id": 99})
            print(f"is_error={r.is_error} · {texto(r)}")

            print("\n--- un argumento con el tipo equivocado: lo rechaza la validación, antes de tu función")
            r = await sesion.call_tool("ver_cv", {"cv_id": "el de Laura"})
            print(f"is_error={r.is_error} · {texto(r)[:160]}")

            # 4) El puente hacia el agente de 06.
            print("\n--- las mismas herramientas, en el formato de function calling de 06")
            print(json.dumps([a_function_calling(t) for t in herramientas], ensure_ascii=False, indent=1)[:900])


if __name__ == "__main__":
    asyncio.run(main())
