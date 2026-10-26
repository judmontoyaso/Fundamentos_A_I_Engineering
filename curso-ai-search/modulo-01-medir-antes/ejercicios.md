# Módulo 1 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Todos se hacen sin LLM: son gratis y deterministas.

---

### Ejercicio 1 — nDCG a mano
Una consulta tiene 2 CVs con relevancia 2 y 1 con relevancia 1. El buscador devuelve, en orden: un 1, un 0, un 2, un 2.
Calcula el nDCG@4.

### Ejercicio 2 — Ponderar la fusión
RRF trata igual a BM25 y a la densa. Cambia `ranking()` para que BM25 pese el doble (suma `2 / (60 + puesto)` para BM25).
¿Sube el total? ¿Qué pasa con las paráfrasis?

### Ejercicio 3 — Otro embedder
Cambia `EMB_MODEL` en `app/backend/.env` por `intfloat/multilingual-e5-small` (y añade los prefijos `query: ` y
`passage: ` en `as_buscador`) o usa el backend de OpenAI. Re-mide la línea base. ¿Qué tipos mejoran?

### Ejercicio 4 — Tus propias consultas
Añade a `as_consultas.py` cinco consultas como las escribiría un reclutador de tu empresa, con su función de relevancia.
¿En qué tipo caen? ¿Cómo les va con la línea base?

### Ejercicio 5 — El promedio que miente
Con `linea_base.jsonl`, calcula la mediana de la diferencia de nDCG entre la híbrida y BM25, y no solo la media. ¿Qué
signo tiene? ¿Qué te dice que la media y la mediana tengan signos distintos?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Ganancias: 1 (rel 1), 0, 3, 3 (rel 2). DCG = 1/log2(2) + 0 + 3/log2(4) + 3/log2(5) = 1 + 1.5 + 1.29 = 3.79. Orden
ideal: 2, 2, 1 → IDCG = 3/1 + 3/1.585 + 1/2 = 3 + 1.89 + 0.5 = 5.39. nDCG@4 = 3.79 / 5.39 ≈ **0.70**.

**2.** Lo habitual es que el total se acerque al de BM25 (0.66) y que las paráfrasis caigan hacia 0, porque BM25 domina
el ranking fusionado. Ponderar mueve el punto medio, pero no resuelve que cada tipo de consulta necesite un modo
distinto: un peso fijo es un compromiso, y el desglose por tipo lo muestra.

**3.** Un embedder mejor suele subir paráfrasis, inglés y liderazgo (los tipos sin palabras en común) y la densa se
acerca a BM25. Lo que no cambia: exclusión, rol + nivel, rol + ciudad y numérica, porque no son problemas de similitud.
Es la evidencia de que esos fallos son de entender la consulta, no del modelo de embeddings.

**4.** No hay una única solución. Lo valioso es descubrir un tipo que el set no tenía (por ejemplo, "disponibilidad
inmediata", "que haya trabajado en banca") y escribir su regla de relevancia antes de medir.

**5.** La mediana suele ser negativa (la híbrida pierde en la consulta típica) aunque la media sea positiva (gana mucho
en pocas). Signos distintos significan una distribución sesgada: unas pocas consultas con grandes ganancias tapan muchas
con pérdidas pequeñas. Para un producto, eso es "peor para la mayoría, mucho mejor para algunos": una decisión que
el promedio no deja ver.

</details>
