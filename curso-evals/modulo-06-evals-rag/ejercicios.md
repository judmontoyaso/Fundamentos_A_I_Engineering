# Módulo 6 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas).

---

### Ejercicio 1 — ¿Cuánto k hace falta?
Mide la recuperación de `01` con k = 1, 3, 5 y 10. Dibuja (o imprime) el recall medio por tipo para cada k. ¿Desde qué
k se resuelven las paráfrasis? ¿Y la agregación de Python? ¿Qué le cuesta al generador recibir 10 CVs?

### Ejercicio 2 — Precisión del contexto
Añade a `01` la **precisión@3**: de los 3 recuperados, cuántos son relevantes. ¿Qué tipo de pregunta tiene la precisión
más baja? ¿Importa una precisión baja si el generador acierta con el oráculo?

### Ejercicio 3 — Arreglar las paráfrasis
Prueba dos cambios en `ev_rag.buscar()` y mide recall@3 en las paráfrasis con cada uno: (a) solo búsqueda densa, sin
BM25; (b) reescribir la pregunta con un LLM antes de buscar ("¿quién administra bases de datos?" → "DBA administrador
de bases de datos Oracle PostgreSQL"). ¿Cuál ayuda? ¿Rompe algún otro tipo?

### Ejercicio 4 — Las agregaciones, sin RAG
Las preguntas de agregación no se pueden responder con 3 CVs. Escribe una ruta alternativa: extrae la ficha de los 30
CVs con el extractor (Módulo 1), guárdalas, y responde "¿quién tiene más años?" y "¿cuántos trabajan con Python?" con
código sobre las fichas. ¿Aciertan? ¿Cómo decidiría el sistema qué ruta usar?

### Ejercicio 5 — Un juez de "afirma sobre todo el corpus"
El juez de fidelidad aprobó "Gabriel Rojas tiene más años de experiencia". Escribe un chequeo (por código o con un
juez) que detecte respuestas que afirman algo sobre **todos** los candidatos ("el que más", "ninguno", "todos")
habiendo visto solo unos pocos. Pruébalo con las respuestas del sistema.

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Lo habitual: las paráfrasis mejoran con k = 5 o 10 (el CV correcto suele estar en los primeros 10, solo que no
arriba); la agregación de Python necesita k ≥ 7 en el mejor caso y, en la práctica, más, porque los 7 no salen todos
arriba. Recibir 10 CVs cuesta tokens en cada pregunta y, en contextos largos, el generador empieza a ignorar lo que
queda en medio. Subir k es un parche: arregla el recall a costa de todo lo demás.

**2.** La precisión más baja suele estar en las preguntas con un solo relevante (dato, tecnología): 1 de 3 = 33 % aunque
la recuperación sea perfecta. Por eso la precisión sola engaña con k fijo. Importa menos si el generador acierta con el
oráculo **y** con el sistema: el ruido no le molestó. Importaría si el contexto fuera largo o si el ruido contuviera
datos contradictorios.

**3.** Quitar BM25 rara vez ayuda a las paráfrasis y suele romper las búsquedas por tecnología exacta (Módulo 4 de AI
Engineering). Reescribir la pregunta con un LLM sí suele ayudar, porque traduce la paráfrasis al vocabulario de los
CVs, a cambio de una llamada más por pregunta. Es el tema del curso de AI search (*query understanding*). Mide siempre
todos los tipos: un arreglo para un tipo puede romper otro.

**4.** Con fichas extraídas, las agregaciones son código: `max(fichas, key=años)` y `sum("python" in skills)`.
Aciertan si la extracción es buena (con el modelo grande, 30/30 en el Módulo 1). La ruta se decide con un enrutador
(Módulo 5 de AI Engineering): una clasificación de la pregunta ("¿pide un dato de alguien, buscar candidatos o algo
sobre todos?"). El enrutador también se evalúa: ¿manda cada pregunta a la ruta correcta?

**5.** Un chequeo barato por código: buscar expresiones de totalidad ("más años de todos", "el que más", "ninguno",
"todos los candidatos") en respuestas cuyo contexto tenía menos CVs que el corpus. Marca la respuesta de Gabriel Rojas.
Uno con juez: preguntarle "¿la respuesta afirma algo sobre el conjunto de todos los candidatos que no se puede saber con
estos CVs?". Lo que no hace falta es que el juez de fidelidad lo haga todo: **un juez por fallo**.

</details>
