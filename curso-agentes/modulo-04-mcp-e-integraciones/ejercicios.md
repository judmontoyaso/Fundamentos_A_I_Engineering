# Módulo 4 · Ejercicios

---

### Ejercicio 1. ¿Por qué `NOMBRES_EXPUESTOS` en el servidor MCP no incluye `enviar_oferta`?
Revisa `NOMBRES_EXPUESTOS` en `code/01_servidor_mcp_ats.py`. En `comun/ag_comun.py` existen 7 herramientas, pero el servidor MCP de preselección solo expone 5 en `tools/list` (omite `agendar_entrevista` y `enviar_oferta`). ¿Qué principio de seguridad aplica aquí y qué ocurre si el modelo intenta invocar `ats_enviar_oferta` vía `tools/call`?

<details>
<summary>Ver solución</summary>

Aplica el **principio de mínimo privilegio por perfil de servidor MCP**: un agente cuya misión es elaborar una terna de preselección solo debe recibir herramientas de lectura y dictamen. Para evitar que un cliente comprometido invoque una herramienta no listada, en `procesar_mensaje_jsonrpc` conviene validar explícitamente que `nombre` esté dentro de `{f"ats_{n}" for n in NOMBRES_EXPUESTOS}` antes de llamar a `ejecutar_herramienta_ats`.
</details>

---

### Ejercicio 2. Filtrar herramientas en el cliente cuando un servidor MCP expone decenas
Si conectas tu agente a un servidor MCP corporativo que devuelve 45 herramientas en `tools/list`, ¿por qué no debes pasar las 45 definiciones directamente al parámetro `tools` del modelo en cada llamada?

<details>
<summary>Ver solución</summary>

Por dos razones medidas en producción:
1. **Costo y latencia de prefill**: 45 esquemas JSON Schema suman entre `4.000` y `8.000` tokens que se facturan en **cada paso** del bucle.
2. **Caída en precisión de selección de herramienta**: cuando el catálogo supera ~15–20 herramientas similares, aumenta la confusión del modelo entre funciones parecidas. El cliente MCP debe filtrar la lista devuelta por `tools/list` según la etapa actual de la máquina de estados.
</details>

---

### Ejercicio 3. Exponer las vacantes como resources
Añade al servidor los métodos `resources/list` y `resources/read` con URIs `ats://vacantes/VAC-101`. Declara la
capacidad `resources` en `initialize`. ¿En qué se diferencia que el cliente lea la vacante como resource a que el
modelo llame `obtener_vacante`?

<details>
<summary>Ver solución</summary>

`resources/list` devuelve `{"resources": [{"uri", "name", "mimeType"}]}` y `resources/read` devuelve
`{"contents": [{"uri", "mimeType", "text"}]}`. La diferencia es quién decide: un resource lo carga la aplicación (por
ejemplo, la vacante que la reclutadora abrió) y lo pone en el contexto desde el inicio, sin gastar un paso del modelo;
una tool la decide el modelo. Para datos que siempre hacen falta, el resource ahorra un paso y una decisión.
</details>

---

### Ejercicio 4. Portar el servidor al SDK oficial
Reescribe `01_servidor_mcp_ats.py` con el SDK oficial (`pip install mcp`) y conecta el cliente con `mcp.Client`. ¿Qué
desaparece de tu código y qué tienes que seguir haciendo tú?

<details>
<summary>Ver solución</summary>

Con la versión 2 del SDK: `MCPServer("mcp-ats-reclutamiento")`, una función por herramienta decorada con
`@servidor.tool()` y `servidor.run("stdio")`. Desaparecen el bucle de transporte, el parseo de JSON-RPC, la negociación
de versión y la generación de `inputSchema` (sale de los tipos de la función). Sigues siendo responsable de validar
argumentos de negocio, de los mensajes de error accionables, de no escribir en stdout y de las credenciales. Comprueba
los nombres exactos de la API en la documentación de la versión que instales: cambian entre versiones mayores.
</details>
