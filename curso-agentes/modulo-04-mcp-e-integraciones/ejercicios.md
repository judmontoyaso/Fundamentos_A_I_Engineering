# Módulo 4 · Ejercicios

---

### Ejercicio 1 — ¿Por qué `NOMBRES_EXPUESTOS` en el servidor MCP no incluye `enviar_oferta`?
Revisa `NOMBRES_EXPUESTOS` en `code/01_servidor_mcp_ats.py`. En `comun/ag_comun.py` existen 7 herramientas, pero el servidor MCP de preselección solo expone 5 en `tools/list` (omite `agendar_entrevista` y `enviar_oferta`). ¿Qué principio de seguridad aplica aquí y qué ocurre si el modelo intenta invocar `ats_enviar_oferta` vía `tools/call`?

<details>
<summary>Ver solución</summary>

Aplica el **principio de mínimo privilegio por perfil de servidor MCP**: un agente cuya misión es elaborar una terna de preselección solo debe recibir herramientas de lectura y dictamen. Para evitar que un cliente comprometido invoque una herramienta no listada, en `procesar_mensaje_jsonrpc` conviene validar explícitamente que `nombre` esté dentro de `{f"ats_{n}" for n in NOMBRES_EXPUESTOS}` antes de llamar a `ejecutar_herramienta_ats`.
</details>

---

### Ejercicio 2 — Filtrar herramientas en el cliente cuando un servidor MCP expone decenas
Si conectas tu agente a un servidor MCP corporativo que devuelve 45 herramientas en `tools/list`, ¿por qué no debes pasar las 45 definiciones directamente al parámetro `tools` del modelo en cada llamada?

<details>
<summary>Ver solución</summary>

Por dos razones medidas en producción:
1. **Costo y latencia de prefill**: 45 esquemas JSON Schema suman entre `4.000` y `8.000` tokens que se facturan en **cada paso** del bucle.
2. **Caída en precisión de selección de herramienta**: cuando el catálogo supera ~15–20 herramientas similares, aumenta la confusión del modelo entre funciones parecidas. El cliente MCP debe filtrar la lista devuelta por `tools/list` según la etapa actual de la máquina de estados.
</details>
