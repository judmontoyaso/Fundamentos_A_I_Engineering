# Módulo 5 · Ejercicios

---

### Ejercicio 1. Por qué limitar `max_workers` ante APIs de LLMs
En `code/02_map_reduce_cvs.py` usamos `ThreadPoolExecutor(max_workers=8)`. Si tuvieras que evaluar `500` candidatos contra una vacante usando `ModeloOpenAI`, ¿qué pasaría si lanzaras `max_workers=500` simultáneamente y cómo debes dimensionar la concurrencia?

<details>
<summary>Ver solución</summary>

Con 500 hilos simultáneos agotarías en segundos los límites de peticiones y de tokens por minuto del proveedor, y recibirías una avalancha de errores `429 Too Many Requests` que dispararían reintentos y alargarían la ejecución. Hay que acotar `max_workers` con los límites de tu cuenta y la latencia media de cada llamada:

$$\text{Concurrencia máxima segura} = \min\left(\frac{\text{RPM límite}}{60 / \text{latencia\_s}}, \frac{\text{TPM límite}}{\text{tokens\_por\_trabajador} \times (60 / \text{latencia\_s})}\right)$$
</details>

---

### Ejercicio 2. Cuándo NO usar subagentes en paralelo
Menciona un caso dentro de nuestro flujo de reclutamiento donde dos pasos **no** se puedan ejecutar en paralelo con `map`.

<details>
<summary>Ver solución</summary>

Cuando existe una **dependencia de datos secuencial** o un **recurso compartido con bloqueo**: por ejemplo, no puedes ejecutar `buscar_candidatos` antes de conocer los `requisitos_obligatorios` que devuelve `obtener_vacante`, ni puedes asignar el único horario libre de las `15:00` del entrevistador a dos candidatos distintos en paralelo sin coordinación centralizada.
</details>

---

### Ejercicio 3. La cuenta de tokens: monolito contra orquestador
Con 8 candidatos de 4.000 tokens cada uno, system prompt y esquemas de 1.000 tokens, dictámenes de 50 tokens y un
agente monolítico que lee las fichas una a una (11 pasos para 4 candidatos, 19 para 8), estima los tokens de entrada
de cada diseño.

<details>
<summary>Ver solución</summary>

Monolito: el paso $k$ lee el prefijo (1.000) más las fichas ya leídas. Con 8 fichas acumulándose a lo largo de 19
pasos, el total pasa de 300.000 tokens de entrada (la suma crece con el cuadrado de los pasos). Orquestador con 8
trabajadores de 2 llamadas cada uno: cada trabajador lee unos 1.000 + 4.000 por llamada, unos 10.000; en total unos
80.000, más un orquestador que lee 8 dictámenes (400 tokens) en un par de pasos. En este caso el orquestador gana en
tokens y en latencia porque las fichas son grandes y no hay que compararlas entre sí. Con fichas de 200 tokens, el
prefijo repetido en cada trabajador haría ganar al monolito.
</details>

---

### Ejercicio 4. Un trabajador que falla
Haz que `subagente_evaluador` lance una excepción para `CAND-03` una de cada dos veces. ¿Qué devuelve hoy el
orquestador? Cámbialo para que reintente una vez y, si vuelve a fallar, marque al candidato como "no evaluado".

<details>
<summary>Ver solución</summary>

Hoy la excepción sube por `pool.map` y aborta toda la preselección. Envuelve la llamada en una función que capture la
excepción, reintente con una espera corta y, si falla de nuevo, devuelva `{"candidato_id", "elegible": None, "error":
...}`. El reduce debe tratar `None` como "pendiente", no como "no elegible", e informarlo en el resultado: una terna
con un candidato sin evaluar no está completa.
</details>
