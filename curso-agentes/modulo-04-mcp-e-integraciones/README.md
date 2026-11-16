# Módulo 4 · Protocolo MCP y servidores de herramientas

> **Objetivo:** separar las herramientas del agente en un proceso propio que habla un protocolo estándar, para que
> el agente no vea credenciales y para que la misma integración sirva a varios clientes.
>
> **Lo que te llevas:** qué es MCP y qué no es, un servidor y un cliente escritos a mano sobre JSON-RPC 2.0 por stdio
> (para ver cada mensaje del protocolo), el agente del curso corriendo sobre ese servidor sin conocer el secreto de la base
> de datos, y cómo pasar al SDK oficial.

Índice:

1. [El problema: N agentes × M integraciones](#1-problema)
2. [Qué es MCP](#2-que-es)
3. [El protocolo por dentro](#3-protocolo)
4. [Laboratorio 1: un servidor MCP del ATS](#4-lab1)
5. [Laboratorio 2: el agente como cliente MCP](#5-lab2)
6. [Seguridad: lo que MCP resuelve y lo que no](#6-seguridad)
7. [Del laboratorio al SDK oficial](#7-sdk)
8. [Lista de revisión](#8-lista)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 4 · Arquitectura MCP con cliente anfitrión, JSON-RPC 2.0 y aislamiento de credenciales](/infografias/agentes-m4-protocolo-mcp.png)

---

<a name="1-problema"></a>
## 1. El problema: N agentes × M integraciones

Hasta ahora las herramientas son funciones de Python importadas en el mismo proceso que el agente. Funciona con un
agente y un sistema. En una empresa hay varios agentes (el de preselección, un asistente interno, un pipeline de
evaluación) y varios sistemas (ATS, calendario, correo, base de sueldos). Integrar cada agente con cada sistema son
N × M integraciones, cada una con su copia de las credenciales.

Y hay un problema de seguridad: si el proceso del agente importa el conector del ATS, ese proceso tiene el
`DATABASE_URL`. Cualquier fallo del agente (una inyección, una herramienta mal escrita, un log descuidado) puede
filtrarlo.

---

<a name="2-que-es"></a>
## 2. Qué es MCP

El **Model Context Protocol** (publicado por Anthropic en noviembre de 2024 y adoptado después por los principales
proveedores y editores) estandariza la conversación entre una aplicación con LLM (el **cliente**, dentro de un
*host*) y un **servidor** que expone capacidades. Con un estándar, cada sistema se integra una vez como servidor y
cualquier cliente compatible lo usa: N + M en lugar de N × M.

Un servidor puede exponer tres primitivas:

| Primitiva | Quién decide usarla | Para qué, en el ATS |
|---|---|---|
| **Tools** (`tools/list`, `tools/call`) | El modelo, bajo las políticas del host | `buscar_candidatos`, `verificar_elegibilidad` |
| **Resources** (`resources/list`, `resources/read`) | La aplicación o el usuario | Contexto de solo lectura por URI: `ats://vacantes/VAC-101`, `ats://politicas/enfriamiento` |
| **Prompts** (`prompts/list`, `prompts/get`) | El usuario | Plantillas: "auditar la terna de una vacante" |

Lo que MCP **no** es: no es un framework de agentes (no decide cuándo llamar a qué), no reemplaza el *tool calling*
del proveedor (el host sigue pasando las herramientas al modelo en el formato de su API) y no trae seguridad por sí
solo (sección 6).

---

<a name="3-protocolo"></a>
## 3. El protocolo por dentro

MCP usa mensajes **JSON-RPC 2.0**: peticiones con `id`, `method` y `params`; respuestas con el mismo `id` y `result`
o `error`; notificaciones sin `id` que no se responden. Dos transportes estándar:

- **stdio**: el cliente lanza el servidor como subproceso y se hablan por stdin y stdout, un mensaje JSON por línea.
  Es el habitual para servidores locales.
- **Streamable HTTP**: el servidor es un servicio HTTP (puede usar SSE para enviar varios mensajes). Es el de
  servidores remotos, compartidos por varios clientes y con autenticación OAuth.

Una sesión empieza siempre igual:

```text
cliente → {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"...","clientInfo":{...}}}
servidor ← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"...","capabilities":{"tools":{}},"serverInfo":{...}}}
cliente → {"jsonrpc":"2.0","method":"notifications/initialized"}
cliente → {"jsonrpc":"2.0","id":2,"method":"tools/list"}
cliente → {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"...","arguments":{...}}}
```

En `initialize` se negocian la versión del protocolo y las capacidades. La especificación tiene versiones con fecha
(la primera fue `2024-11-05`, y hay revisiones posteriores que añadieron, entre otras cosas, el transporte Streamable
HTTP y la autorización con OAuth). Un cliente y un servidor reales acuerdan la más reciente que ambos soportan.

El resultado de `tools/call` trae una lista `content` (texto, imágenes u otros) e `isError`. Un error de la
herramienta (vacante inexistente) es un **resultado con `isError: true`**, que el modelo debe ver para corregirse; un
error del protocolo (método desconocido) es un `error` JSON-RPC, que trata el cliente.

---

<a name="4-lab1"></a>
## 4. Laboratorio 1: un servidor MCP del ATS

[`code/01_servidor_mcp_ats.py`](code/01_servidor_mcp_ats.py) implementa `initialize`, `tools/list` y `tools/call` a
mano, en unas 80 líneas, para que veas cada mensaje. Las herramientas son las del ATS con prefijo `ats_`, y sus
`inputSchema` son los mismos JSON Schema del módulo 1.

Corrido directamente, hace el handshake y una llamada:

```json
{"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": false}},
 "serverInfo": {"name": "mcp-ats-reclutamiento", "version": "1.0.0"}}
```

```text
tools/list → ats_obtener_vacante, ats_buscar_candidatos, ats_consultar_ficha_candidato,
             ats_verificar_elegibilidad, ats_entregar_terna
```

Con `--stdio`, entra en el bucle de transporte: lee una línea JSON-RPC por stdin y responde por stdout. Fíjate en dos
detalles:

- **El servidor exige `ATS_DB_SECRET` en su propio entorno** y responde con error si no lo tiene. La credencial vive en
  el servidor.
- **Solo se ejecuta lo que se publica.** `tools/call` rechaza cualquier nombre que no esté en `tools/list`. La
  función del ATS conoce las 7 herramientas, y sin esta comprobación un cliente podría llamar a `ats_enviar_oferta`
  aunque el servidor no la anuncie (ejercicio 1).
- **En stdio, stdout es del protocolo.** Cualquier `print` de depuración en el servidor corrompe la comunicación; los
  logs van a stderr.

---

<a name="5-lab2"></a>
## 5. Laboratorio 2: el agente como cliente MCP

[`code/02_cliente_mcp.py`](code/02_cliente_mcp.py) lanza el servidor como subproceso con
`subprocess.Popen([..., "--stdio"])`, le pasa el secreto **solo en el entorno del hijo**, hace el handshake, descubre
las herramientas con `tools/list`, las traduce al formato de *tool calling* del modelo y corre el bucle del agente,
enviando cada llamada con `tools/call`.

Resultado:

| | |
|---|---|
| Servidor | `mcp-ats-reclutamiento` 1.0.0, protocolo `2024-11-05` |
| ¿Credencial visible en el proceso del agente? | **No** |
| Herramientas descubiertas | 5, con prefijo `ats_` |
| Llamadas MCP | 11 (las mismas del módulo 0) |
| Terna | `CAND-01`, `CAND-03` |

El agente no cambió: el mismo modelo, el mismo bucle, la misma terna. Cambió **dónde viven las herramientas**. Ahora
puedes reemplazar el servidor (otro lenguaje, otra base de datos, otro equipo que lo mantiene) sin tocar el agente.

La traducción de MCP al formato del proveedor es mecánica: `name` → `name`, `description` → `description`,
`inputSchema` → `parameters`.

---

<a name="6-seguridad"></a>
## 6. Seguridad: lo que MCP resuelve y lo que no

**Lo que resuelve:** aislamiento de credenciales (el agente no tiene el secreto) y un punto único donde aplicar
permisos, auditoría y límites de uso por servidor.

**Lo que no resuelve:**

- **Un servidor MCP es código de terceros que ejecutas.** Instalar uno desde un repositorio desconocido es como
  instalar cualquier dependencia: puede leer tu disco o tu red. Revisa el origen y fija versiones.
- **Las descripciones de herramientas son texto que lee el modelo.** Un servidor malicioso puede esconder
  instrucciones en una descripción (*tool poisoning*) o cambiarla después de que la aprobaste. Trata los catálogos de
  servidores externos como datos no confiables (módulo 6).
- **Demasiadas herramientas.** Conectar cinco servidores puede poner 60 herramientas en cada llamada. El cliente debe
  filtrar y exponer solo las de la etapa actual (ejercicio 2).
- **Las acciones con efectos siguen necesitando política y aprobación humana**, se ejecuten por MCP o no.

---

<a name="7-sdk"></a>
## 7. Del laboratorio al SDK oficial

El servidor del laboratorio está escrito a mano para enseñar el protocolo; no negocia versiones, ni implementa
resources, prompts, cancelación ni progreso. En producción usa el SDK oficial (`pip install mcp`). En la versión 2 del
SDK de Python, la clase de alto nivel se llama `MCPServer` (en la 1 era `FastMCP`), y una herramienta se declara con un
decorador; el schema sale de los tipos de la función:

```python
from mcp.server.mcpserver import MCPServer

servidor = MCPServer("mcp-ats-reclutamiento")

@servidor.tool()
def verificar_elegibilidad(vacante_id: str, candidato_id: str) -> dict:
    """Evalúa con las reglas de negocio si el candidato cumple los requisitos de la vacante."""
    return ejecutar_herramienta_ats("verificar_elegibilidad", {"vacante_id": vacante_id, "candidato_id": candidato_id})

if __name__ == "__main__":
    servidor.run("stdio")
```

Y el cliente, con `mcp.Client` (acepta parámetros de stdio, una URL de Streamable HTTP o, en tests, el servidor en el
mismo proceso). Las APIs del SDK cambian entre versiones mayores: revisa la documentación de la versión que instales.
Portar este laboratorio al SDK es el ejercicio 4.

---

<a name="8-lista"></a>
## 8. Lista de revisión

- [ ] Las credenciales de cada sistema viven solo en su servidor MCP.
- [ ] El servidor devuelve los errores de negocio como `isError: true` con mensajes accionables.
- [ ] El cliente expone al modelo solo las herramientas de la etapa actual.
- [ ] Los servidores de terceros se revisan, se fijan en versión y sus descripciones se tratan como no confiables.
- [ ] Las herramientas con efectos pasan por la política del host, aunque lleguen por MCP.
- [ ] En stdio, el servidor no escribe nada en stdout que no sea protocolo.

En el siguiente módulo dividimos el trabajo entre varios agentes, y medimos cuándo vale la pena.
