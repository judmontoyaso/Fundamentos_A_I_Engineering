# Módulo 4 · Protocolo MCP y servidores de herramientas

Cuando construyes un solo agente pequeño, importar funciones de Python directamente en el mismo proceso funciona. Cuando tienes tres equipos, cinco fuentes de datos (ATS, calendario, repositorio GitHub, base de sueldos) y varios clientes (tu backend web, un asistente interno en el IDE y un pipeline de evaluación), acoplar las credenciales y el código de cada integración dentro del bucle del agente se vuelve insostenible.

El **Model Context Protocol (MCP)** estandariza la frontera entre el **anfitrión del agente (cliente)** y los **servidores de capacidades** mediante JSON-RPC 2.0.

![Módulo 4 · Arquitectura Model Context Protocol (MCP) con cliente anfitrión, JSON-RPC 2.0 y aislamiento de credenciales](/infografias/agentes-m4-protocolo-mcp.png)

---

## Las tres primitivas de MCP

| Primitiva | Quién la controla | Para qué sirve en nuestro ATS |
|---|---|---|
| **Resources (`resources/read`)** | La aplicación / usuario | Exponer contexto de solo lectura direccionable por URI (`ats://vacantes/VAC-101`, `ats://politicas/bandas-salariales`) sin gastar llamadas de herramienta |
| **Tools (`tools/call`)** | El modelo (bajo políticas del host) | Ejecutar acciones parametrizadas con validación JSON Schema (`buscar_candidatos`, `verificar_enfriamiento`) |
| **Prompts (`prompts/get`)** | El usuario / plantilla | Plantillas estandarizadas de auditoría o evaluación (`auditar_terna_vacante`) |

---

## Ventajas de seguridad y arquitectura en producción

1. **Aislamiento de credenciales**: el proceso del agente nunca ve el `DATABASE_URL` ni el token maestro del ATS; solo envía mensajes JSON-RPC al servidor MCP, que aplica permisos por rol.
2. **Descubrimiento dinámico con filtro de herramientas**: si un servidor MCP expone 40 herramientas, el cliente debe filtrar y presentar al LLM **solo las 4 a 6 relevantes** para la tarea actual. Pasar 40 esquemas de herramientas degrada la selección del modelo y dispara el consumo de tokens de entrada.
