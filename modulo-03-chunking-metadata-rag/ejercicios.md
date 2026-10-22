# Módulo 3 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas).

---

### Ejercicio 1 — Las familias en tu propio texto
Corre [`code/01_chunking_estrategias.py`](code/01_chunking_estrategias.py) con un CV tuyo. Compara chunking fijo
(sin y con overlap) contra el recursivo y el de secciones. ¿Cuál parte menos ideas por la mitad? ¿Dónde se nota el
overlap?

### Ejercicio 2 — El tamaño importa
Con el chunk fijo, prueba `tam = 80, 200, 500`. Para cada tamaño: ¿los chunks tienen un solo tema o varios? Escribe
una consulta específica ("liderazgo de equipos") y razona con cuál tamaño la recuperarías mejor y por qué (precisión
vs. contexto).

### Ejercicio 3 — Chunking semántico
Corre [`code/02_semantic_chunking.py`](code/02_semantic_chunking.py) (necesita embedder). Mete un párrafo que mezcle
tres temas sin saltos de línea. ¿Los separa en las fronteras correctas? Baja y sube `umbral_percentil` (10, 25, 50) y
observa cómo cambia el número de chunks.

### Ejercicio 4 — Pre-filtrado con metadata
Con [`code/03_metadata_filtering.py`](code/03_metadata_filtering.py) y Qdrant corriendo, haz la misma consulta con y
sin filtro `nivel="senior"`. Confirma que el conjunto recuperado cambia. Luego añade un filtro por `area` y comprueba
que combinan (AND). ¿Por qué pre-filtrar es mejor que buscar en todo y filtrar después?

### Ejercicio 5 — RAG de punta a punta
Corre [`code/04_rag_minimo.py`](code/04_rag_minimo.py) (Qdrant + API key). Haz tres preguntas: una que el contexto sí
responde, una que no (verifica que **se abstiene**), y una que mezcle dos candidatos (verifica que **cita** a cada
uno). ¿La respuesta inventa algo? ¿Las citas son correctas?

### Ejercicio 6 — Diagnóstico retrieval vs. generación
Provoca los dos fallos del §10: (a) baja `k=1` y haz una pregunta cuyo chunk relevante no sea el #1 → fallo de
**retrieval**; (b) con `k=5` quita del `SYSTEM` la frase "Responde SOLO con la información del CONTEXTO" y haz una
pregunta ajena a los CVs → fallo de **generación** (alucina). Describe cómo se ven distintos.

### Ejercicio 7 — Evaluación
Con [`code/05_eval_rag.py`](code/05_eval_rag.py) arma 10 preguntas sobre tus CVs, etiqueta los chunks relevantes, y
calcula `context_recall`. Si tienes API, calcula `faithfulness` de 5 respuestas. ¿El recall bajo explica alguna
respuesta mala?

### Ejercicio 8 — Proyecto
Monta el RAG del §12 sobre 10-15 CVs: chunking estructural con metadata, índice en Qdrant, `responder(pregunta,
filtro)` con anclaje + abstención + cita. Prueba una pregunta con pre-filtrado por nivel. Mide `recall@5` y revisa
`faithfulness` a mano en 10 preguntas. Documenta: ¿qué cambió tu `recall` al pasar de "un vector por CV" (Módulo 2) a
"chunks por sección" (este módulo)?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** El chunking **por secciones** parte menos ideas: corta en fronteras reales (Experiencia/Educación/Skills). El
**fijo sin overlap** es el que peor queda (corta a mitad de frase). Con overlap, verás texto repetido entre chunks
consecutivos: esa repetición es lo que salva las ideas de la frontera.

**2.** Con `tam=80` los chunks son muy precisos pero fragmentarios (un chunk puede decir "lidera un equipo" sin
contexto). Con `tam=500` traen contexto pero mezclan temas y el embedding se diluye. Para "liderazgo de equipos", un
tamaño medio (200-300) suele recuperar mejor: suficiente tema único, suficiente contexto. Pero **confírmalo midiendo**,
no por intuición.

**3.** Debería cortar en los valles de similitud (cambio de tema). Un `umbral_percentil` bajo (10) corta poco (chunks
grandes); alto (50) corta mucho (chunks pequeños). El punto dulce depende del documento; se calibra con el eval.

**4.** Con filtro `nivel="senior"` desaparecen los junior del resultado aunque sean semánticamente parecidos.
Pre-filtrar es mejor porque (a) reduce el espacio antes de comparar vectores → más rápido, y (b) evita que un
resultado "parecido pero no apto" ocupe un puesto del top-k que debería ser para un apto. Buscar-y-filtrar-después
puede vaciarte el top-k.

**5.** Bien configurado: responde la primera, se abstiene en la segunda ("el contexto no alcanza"), y cita a cada
candidato en la tercera. Si inventa, revisa el `SYSTEM` (anclaje) y si el chunk correcto siquiera se recuperó (§10).

**6.** (a) Fallo de **retrieval**: la respuesta es pobre o abstención, y al mirar los chunks recuperados ves que el
relevante **no está**. (b) Fallo de **generación**: el LLM responde de su memoria algo no respaldado (alucina),
aunque el contexto esté. La prueba decisiva: dale a mano el chunk correcto; si entonces responde bien, el problema
era retrieval.

**7.** Si `context_recall` es bajo en las preguntas que salieron mal, el problema es recuperación, no el LLM. Un
`faithfulness` bajo con recall alto apunta a generación (prompt o modelo).

**8.** Resultado esperado: pasar de "un vector por CV" a "chunks por sección" normalmente **sube el recall** en
preguntas específicas (liderazgo, una tecnología concreta), porque el pasaje relevante ya no está diluido en el
promedio del CV. Documenta el antes/después con tu número de `recall@5`.

</details>
