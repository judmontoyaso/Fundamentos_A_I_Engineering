# Ejercicios · Módulo 5

## Ejercicio 1: Cuándo usar un subagente vs. una herramienta normal

Si una operación consiste en consultar el salario aspirado de un candidato en una tabla SQL, ¿debe ser un subagente o una herramienta determinista? ¿Y si consiste en leer 3 entrevistas abiertas, contrastarlas con el CV y redactar una matriz de riesgos con citas?

<details>
<summary>Solución comentada</summary>

- Consultar el salario en SQL es una **herramienta determinista** de 5 ms: envolverla en un subagente añadiría segundos de latencia y costo de LLM sin ningún beneficio.
- Contrastar 3 entrevistas abiertas con el CV requiere síntesis multi-documento que llenaría de ruido el contexto del orquestador: ahí sí brilla un **subagente con contexto aislado** que devuelve únicamente el `DictamenCandidato` resumido.

</details>

---

## Ejercicio 2: Control de concurrencia frente a Rate Limits (HTTP 429)

Lanzas 25 subagentes en paralelo con `asyncio.gather` y la mitad falla con error `429 Too Many Requests`. ¿Cómo lo evitas en código?

<details>
<summary>Solución comentada</summary>

Envolviendo cada ejecución de subagente en un `asyncio.Semaphore(max_concurrencia)` (por ejemplo, `max_concurrencia=5`) combinado con un presupuesto global compartido para que el enjambre completo nunca supere el límite de tokens por minuto (TPM).

</details>
