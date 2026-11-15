# Ejercicios · Módulo 4

## Ejercicio 1: Resource vs. Tool en MCP

Para cada caso del ATS, decide si debe modelarse como un **Resource** (`resources/read`) o como un **Tool** (`tools/call`):
1. El documento estático con la política de contratación y periodos de enfriamiento de la empresa.
2. Una búsqueda filtrada por habilidades, salario máximo y modalidad.
3. Registrar una solicitud de entrevista técnica para un candidato.

<details>
<summary>Solución comentada</summary>

1. **Resource** (`ats://politicas/contratacion`): es un documento de referencia identificable por URI que la aplicación puede adjuntar al inicio sin que el modelo tenga que «descubrirlo» mediante una llamada de herramienta.
2. **Tool** (`buscar_candidatos`): requiere parámetros dinámicos decididos por el modelo según la consulta.
3. **Tool con confirmación** (`solicitar_entrevista`): produce un efecto secundario en el sistema externo.

</details>

---

## Ejercicio 2: Sobrecarga del catálogo de herramientas

Conectas 4 servidores MCP a tu agente y juntos exponen **52 herramientas**. La precisión de selección de herramientas cae del 94 % al 68 %. ¿Cómo lo solucionas sin reescribir los servidores MCP?

<details>
<summary>Solución comentada</summary>

En el **cliente MCP**, filtra por lista blanca (`allowlist`) según la etapa de la máquina de estados o el rol de la tarea antes de pasar el arreglo `tools` al LLM. Por ejemplo, durante la fase de exploración solo se exponen las 3 herramientas de lectura del ATS.

</details>
