# Módulo 4 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). El reranker usa la caché del curso de Evals: para
medir su latencia real, desactívala.

---

### Ejercicio 1 — Reranker de lista
Cambia el reranker puntual por uno de **lista**: una sola llamada que recibe los 20 CVs y devuelve el orden (como el
reranker del Módulo 4 de AI Engineering). Mide nDCG, llamadas y latencia sobre la base. ¿Qué ganas y qué pierdes?

### Ejercicio 2 — ¿Cuántos reordenar?
Prueba `TOP` = 10, 20 y 40 sobre la base. ¿Sube la paráfrasis con 40? ¿Cuánto cuesta cada opción?

### Ejercicio 3 — MaxSim sin las palabras vacías
MaxSim suma un término por cada token de la consulta, incluidos "de", "que" y "con". Quita de la consulta los tokens
de palabras vacías (o los de menos de 3 letras) antes de sumar. ¿Cambia el total? ¿Qué tipos mejoran?

### Ejercicio 4 — Pares con paráfrasis
Añade a `pares()` plantillas que describan el rol sin nombrarlo (por ejemplo, un diccionario rol → descripción: "quien
automatice despliegues" para devops). Vuelve a entrenar en el holdout. ¿Se recupera "quien haga pruebas automatizadas
de software"? ¿Hiciste trampa? (Pista: ¿se parecen tus descripciones a las consultas de prueba?)

### Ejercicio 5 — El embedder afinado en la híbrida
Usa el modelo afinado (en `salida/minilm_afinado`) como embedder de la híbrida y de los filtros suaves. ¿Sube algo sobre
0.89?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Un reranker de lista hace una sola llamada en vez de 20, así que cuesta menos y tarda menos, pero recibe un
contexto largo (20 CVs) y tiene que devolver una permutación válida (hay que verificar que no invente ni repita ids). En
calidad suele quedar cerca del puntual. El puntual se paraleliza y sus notas se pueden cachear por par, lo que en un
buscador con consultas repetidas es una ventaja.

**2.** Con 40, la paráfrasis puede subir algo, porque los DevOps empiezan a entrar en el top que se reordena; con 10,
baja. El costo crece lineal con TOP (una llamada por CV en el puntual). Es el intercambio de siempre entre recall de la
primera etapa y costo de la segunda: un reranker no arregla lo que la primera etapa no trajo, salvo que le des más.

**3.** Quitar las palabras vacías suele subir un poco el total y sobre todo las consultas largas (paráfrasis, liderazgo),
donde "que", "de" y "con" sumaban similitud con cualquier CV. Es lo que hace ColBERT con su entrenamiento y lo que BM25
hace con el IDF: no todos los tokens de la consulta pesan lo mismo.

**4.** Con descripciones de roles en los pares, la paráfrasis suele recuperarse. La pregunta de la trampa es la buena:
si tus descripciones se parecen mucho a las consultas de prueba ("quien haga pruebas automatizadas"), estás entrenando
con el examen. Escríbelas sin mirar las consultas de prueba, o mejor, tómalas de consultas reales de usuarios
(Módulo 7) y deja las de prueba fuera.

**5.** Lo esperable es que no suba de forma distinguible: con la consulta entendida, el ranking de partida importa poco
(§4). El embedder afinado tiene sentido sin parser, o como primera etapa sobre un corpus grande. Es la misma conclusión
del módulo con otra técnica.

</details>
