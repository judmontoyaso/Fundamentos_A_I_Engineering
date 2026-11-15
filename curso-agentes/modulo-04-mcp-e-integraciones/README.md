# Módulo 4 · Protocolo MCP y servidores de herramientas

> **Objetivo:** desacoplar el bucle del agente de la implementación y las credenciales de las herramientas construyendo un servidor y un cliente reales del **Model Context Protocol (MCP)** sobre JSON-RPC 2.0 y transporte `stdio` entre procesos aislados.

Cuando construyes un prototipo rápido, importar las funciones de base de datos directamente dentro del archivo del agente parece cómodo. En producción empresarial ese acoplamiento crea dos problemas graves:

1. **Riesgo de seguridad por credenciales compartidas**: si el proceso donde corre el agente tiene en sus variables de entorno las llaves maestras (`ATS_DB_SECRET`, `DATABASE_URL`), cualquier fallo o ejecución de código en el entorno del agente compromete la base de datos completa.
2. **Duplicación entre clientes**: si mañana necesitas exponer las mismas herramientas del ATS a tu backend web, a un asistente en el IDE y al runner de evaluación en CI, terminas manteniendo tres copias de los esquemas JSON y las validaciones.

El **Model Context Protocol (MCP)** resuelve ambos problemas definiendo un protocolo estándar sobre **JSON-RPC 2.0** entre el proceso anfitrión del agente (**Cliente MCP**) y un proceso independiente que custodia las herramientas y credenciales (**Servidor MCP**).

![Módulo 4 · Arquitectura Model Context Protocol (MCP) con cliente anfitrión, JSON-RPC 2.0 y aislamiento de credenciales](/infografias/agentes-m4-protocolo-mcp.png)

---

## 1. El contrato JSON-RPC 2.0 de un servidor MCP (`01_servidor_mcp_ats.py`)

Un servidor MCP sobre transporte `stdio` lee peticiones JSON-RPC línea por línea desde su entrada estándar (`sys.stdin`) y escribe respuestas JSON-RPC en `sys.stdout`. En `code/01_servidor_mcp_ats.py` implementamos los tres métodos nucleares del ciclo de vida de herramientas en MCP (`protocolVersion: "2024-11-05"`):

| Fase MCP | Método JSON-RPC | Qué envía el cliente | Qué responde el servidor MCP (`01_servidor_mcp_ats.py`) |
|---|---|---|---|
| **1. Handshake** | `initialize` | `{"clientInfo": {"name": "agente-reclutador"}}` | Versión de protocolo (`2024-11-05`), `capabilities.tools` y `serverInfo` |
| **2. Descubrimiento** | `tools/list` | `{}` | Lista de herramientas (`ats_obtener_vacante`, `ats_buscar_candidatos`, etc.) con su `inputSchema` JSON Schema |
| **3. Ejecución** | `tools/call` | `{"name": "ats_obtener_vacante", "arguments": {"vacante_id": "VAC-101"}}` | `{"content": [{"type": "text", "text": "{...}"}], "isError": false}` |

Además, antes de atender cualquier petición, el servidor comprueba que su propio proceso tenga configurada la variable privada `ATS_DB_SECRET`.

---

## 2. Subproceso real y aislamiento de credenciales (`02_cliente_mcp.py`)

En `code/02_cliente_mcp.py`, la clase `ClienteMCPStdio` lanza `01_servidor_mcp_ats.py --stdio` como un **proceso hijo real del sistema operativo (`subprocess.Popen`)** con tuberías `stdin`/`stdout` dedicadas:

```python
entorno_hijo = {**os.environ, "ATS_DB_SECRET": "vault-ats-prod-token-7741"}
self._proc = subprocess.Popen(
    [sys.executable, str(script_servidor), "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    env=entorno_hijo,
)
```

Observa la frontera de aislamiento que se verifica al ejecutar `python code/02_cliente_mcp.py`:

- En el **proceso del agente (padre)**: `os.getenv("ATS_DB_SECRET")` es `None` (`credencial_visible_en_proceso_agente: false`). El agente jamás tiene acceso a la llave del ATS.
- En el **proceso del servidor MCP (hijo)**: recibe `ATS_DB_SECRET` en su entorno privado, valida cada llamada JSON-RPC y devuelve únicamente la salida estructurada de las 5 herramientas autorizadas (`ats_*`).
- El cliente descubre dinámicamente los esquemas mediante `tools/list`, los traduce al formato de *tool calling* de OpenAI y ejecuta los 11 pasos de `VAC-101` a través de la tubería `stdio`, obteniendo `terna: ["CAND-01", "CAND-03"]` (`exacta: true`).
