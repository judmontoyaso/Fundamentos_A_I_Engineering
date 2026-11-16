# Módulo 4 · Ejercicios

---

### Ejercicio 1. ¿Por qué `NOMBRES_EXPUESTOS` en el servidor MCP no incluye `enviar_oferta`?
Revisa `NOMBRES_EXPUESTOS` en `code/01_servidor_mcp_ats.py`. En `comun/ag_comun.py` existen 7 herramientas, pero el servidor MCP de preselección solo expone 5 en `tools/list` (omite `agendar_entrevista` y `enviar_oferta`). ¿Qué principio de seguridad aplica aquí y qué ocurre si el modelo intenta invocar `ats_enviar_oferta` vía `tools/call`?

<details>
<summary>Ver solución</summary>

Se aplica el **principio de mínimo privilegio**: un agente que arma una terna solo necesita herramientas de lectura y de dictamen, así que el servidor de preselección no publica las que tienen efectos. Pero publicar menos herramientas no basta. En una versión anterior del laboratorio, `tools/call` ejecutaba cualquier nombre que conociera la función del ATS, y una llamada directa a `ats_enviar_oferta` emitía la oferta aunque la herramienta no apareciera en `tools/list`. Ahora `procesar_mensaje_jsonrpc` comprueba que el nombre esté entre las herramientas publicadas y, si no, responde con `isError: true` y la lista de las disponibles. Compruébalo enviando esa llamada a mano al servidor: el catálogo que se anuncia y lo que se permite ejecutar tienen que coincidir, y eso se verifica en el servidor.
</details>

---

### Ejercicio 2. Filtrar herramientas en el cliente cuando un servidor MCP expone decenas
Si conectas tu agente a un servidor MCP corporativo que devuelve 45 herramientas en `tools/list`, ¿por qué no debes pasar las 45 definiciones directamente al parámetro `tools` del modelo en cada llamada?

<details>
<summary>Ver solución</summary>

Por dos razones:
1. **Costo y latencia**: cada esquema del ATS ocupa unos 120 tokens, así que 45 herramientas parecidas suman del orden de 5.000 tokens que se vuelven a enviar en **cada paso** del bucle.
2. **Peor elección de herramienta**: con muchas herramientas parecidas, el modelo se confunde más al elegir. Cuántas son demasiadas depende del modelo y de las herramientas, así que conviene medirlo con tus tareas. El cliente MCP debe filtrar la lista que devuelve `tools/list` y pasarle al modelo solo las de la etapa actual de la máquina de estados.
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
