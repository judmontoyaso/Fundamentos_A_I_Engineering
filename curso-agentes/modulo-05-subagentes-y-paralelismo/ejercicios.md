# Módulo 5 · Ejercicios

---

### Ejercicio 1 — Por qué limitar `max_workers` ante APIs de LLMs
En `code/02_map_reduce_cvs.py` usamos `ThreadPoolExecutor(max_workers=8)`. Si tuvieras que evaluar `500` candidatos contra una vacante usando `ModeloOpenAI`, ¿qué pasaría si lanzaras `max_workers=500` simultáneamente y cómo debes dimensionar la concurrencia?

<details>
<summary>Ver solución</summary>

Con `500` hilos simultáneos agotarías en menos de un segundo las cuotas de *Requests Per Minute (RPM)* y *Tokens Per Minute (TPM)* del proveedor, recibiendo una cascada de errores `429 Too Many Requests` que dispararían reintentos y multiplicarían la latencia. En producción se acota `max_workers` (típicamente entre `4` y `16`) según la fórmula:

$$\text{Concurrencia máxima segura} = \min\left(\frac{\text{RPM límite}}{60 / \text{latencia\_s}}, \frac{\text{TPM límite}}{\text{tokens\_por\_trabajador} \times (60 / \text{latencia\_s})}\right)$$
</details>

---

### Ejercicio 2 — Cuándo NO usar subagentes en paralelo
Menciona un caso dentro de nuestro flujo de reclutamiento donde dos pasos **no** se puedan ejecutar en paralelo con `map`.

<details>
<summary>Ver solución</summary>

Cuando existe una **dependencia de datos secuencial** o un **recurso compartido con bloqueo**: por ejemplo, no puedes ejecutar `buscar_candidatos` antes de conocer los `requisitos_obligatorios` que devuelve `obtener_vacante`, ni puedes asignar el único horario libre de las `15:00` del entrevistador a dos candidatos distintos en paralelo sin coordinación centralizada.
</details>
