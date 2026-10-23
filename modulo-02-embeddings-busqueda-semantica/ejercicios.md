# Módulo 2 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas).

---

### Ejercicio 1 — La métrica correcta
Corre [`code/04_similitud.py`](code/04_similitud.py). Explica con tus palabras por qué el `dot` entre `corto` y
`largo` sale "inflado" frente al coseno, y en qué caso real de CVs eso te daría un ranking equivocado.

### Ejercicio 2 — Semántica vence a léxica
Corre [`code/06_embeddings_reales.py`](code/06_embeddings_reales.py). Cambia la consulta por una tuya cuyo candidato
ideal **no comparta palabras** con el CV. ¿Gana el documento correcto? Ahora rompe la búsqueda semántica: escribe
dos documentos que a un humano le parezcan opuestos pero que el modelo ponga cercanos. ¿Por qué pasa?

### Ejercicio 3 — Matryoshka (costo vs. calidad)
En `06`, observa el ranking al truncar a 512, 256 y 128 dims. ¿A partir de qué dimensión cambia el top-1? Calcula
cuánta RAM ahorrarías en 1 millón de vectores al pasar de dim completa a 512 (float32 = 4 bytes/componente).

### Ejercicio 4 — Query vs. documento
Busca la tarjeta del modelo de embeddings que uses. ¿Pide prefijos distintos para query y documento (p. ej.
`"query:"` / `"passage:"`)? Añádelos en `06` y mide si el ranking mejora. Si tu modelo no los usa, explica por qué
igual importa saberlo.

### Ejercicio 5 — Qdrant a mano
Con [`code/09_qdrant_basico.py`](code/09_qdrant_basico.py) corriendo, agrega 5 CVs más al array `docs`. Luego haz 3
consultas y para cada una anota el `score` del primer resultado. ¿Qué rango de `score` separa "claramente relevante"
de "dudoso" en tu caso? (No hay número universal; se calibra por dominio.)

### Ejercicio 6 — Recrear = perder
En `09`, cambia `Distance.COSINE` por `Distance.EUCLID` **sin** normalizar los vectores y vuelve a buscar. ¿Cambia
el ranking? Ahora normaliza los vectores antes de subirlos y repite con EUCLID. ¿Qué observas y por qué (pista: §4)?

### Ejercicio 7 — Eval de retrieval
Con [`code/11_eval_retrieval.py`](code/11_eval_retrieval.py), arma un set de **10 consultas reales** sobre tus CVs,
etiqueta a mano los relevantes, corre tu buscador del proyecto y calcula `recall@5` y `MRR`. Guarda el número: es tu
línea base. En el Módulo 3 lo tienes que superar con chunking.

### Ejercicio 8 — Proyecto
Completa [`code/10_indexar_cvs.py`](code/10_indexar_cvs.py): (a) usa el modelo `CV` de Pydantic del Módulo 1 en vez
del dataclass de juguete; (b) añade caché de embeddings por `hash(texto+modelo)`; (c) prueba dos versiones de
`texto_para_embedding` —una que incluya solo skills y otra que incluya todo— y mide con el Ejercicio 7 cuál da mejor
`recall@5`. Documenta qué texto indexado funcionó mejor y tu hipótesis de por qué.

### Ejercicio 9 — Elige tu modelo de embeddings
Ejecuta [`code/12_elegir_modelo.py`](code/12_elegir_modelo.py). Añade a `CONSULTAS` cinco paráfrasis tuyas con su
candidato correcto y vuelve a correr. Para cada modelo anota recall@1, MRR, tiempo y **qué consultas falla**. ¿Cambia
algo E5 con y sin prefijos? ¿Te quedarías con el modelo local o con el de la API, y por qué?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** `dot` crece con la **magnitud** de los vectores; `largo` tiene norma grande, así que su producto punto con
cualquier cosa sale inflado aunque la *dirección* (el significado) sea la misma que `corto`. En CVs: un CV muy largo
(más tokens → a veces vector de mayor norma) podría rankear artificialmente alto solo por ser largo, no por ser más
relevante. El coseno, al mirar solo el ángulo, lo evita. Por eso coseno es el default.

**2.** Normalmente gana el documento correcto (ese es el punto del módulo). Para "romperlo": el modelo a veces acerca
textos que comparten **tema/forma** aunque signifiquen lo opuesto — p. ej. "me encantó la película" y "odié la
película" quedan *cercanos* porque hablan de lo mismo con estructura parecida; el embedding de propósito general
captura *aboutness* (de qué trata), no siempre *polaridad*. Lección: los embeddings codifican similitud temática, y
el matiz (negación, sentimiento) puede perderse. Para eso están los re-rankers y la búsqueda híbrida (Módulo 4).

**3.** Depende del modelo, pero típicamente el top-1 aguanta hasta 256–512 dims. RAM: 1M × (dim_completa − 512) × 4
bytes. Si pasas de 1536 a 512: 1M × 1024 × 4 B = ~4.1 GB ahorrados **solo en vectores** (sin contar el grafo HNSW).
A escala, Matryoshka es dinero real.

**4.** Modelos como la familia E5/BGE sí usan prefijos; omitirlos degrada el recall porque el modelo fue entrenado
esperándolos: query y documento se embedean en "sub-espacios" alineados solo con el prefijo correcto. Aunque tu
modelo no los pida, saberlo evita el bug de aplicar un modelo asimétrico sin su convención.

**5.** No hay umbral universal: `0.8` puede ser "alto" para un modelo y "medio" para otro. Lo calibras mirando pares
que tú sabes relevantes vs. irrelevantes y viendo dónde cae la frontera. Por eso en producción se define un **umbral
de score** por dominio, o mejor, se usa un re-ranker en vez de un corte fijo.

**6.** Con EUCLID **sin** normalizar, el ranking puede cambiar porque la magnitud entra en juego (igual que `dot`).
Al **normalizar** y usar EUCLID, el ranking coincide con el de COSINE: sobre vectores unitarios, L2 y coseno inducen
el mismo orden de vecinos (solo cambia la escala del score). Confirma la regla de §4: lo que importa es casar
métrica + normalización con lo que el modelo espera.

**7.** No hay solución "correcta": el entregable es el *número* y el set etiquetado. Si tu `recall@5` es, digamos,
0.6, significa que en 4 de cada 10 consultas el candidato bueno no está en el top 5 — mucho margen, que el chunking
del Módulo 3 debería cerrar.

**8.** Hipótesis típica: incluir skills **y** cargos suele ganar frente a solo skills, porque da más contexto
semántico para emparejar consultas sobre responsabilidades ("lideró equipos"), no solo tecnologías. Pero depende de
tus consultas: si siempre buscan por tecnología, "solo skills" puede ser más limpio (menos ruido). El punto del
ejercicio es que **lo decidas con el número de recall, no con intuición**.

**9.** Como referencia, con las 10 consultas originales los cinco modelos empataron en recall@1 = 0.90 (manual §6):
el set no discrimina. Tus consultas nuevas son las que pueden separarlos, sobre todo si son largas o combinan
requisitos. No hay una respuesta única: depende de tus consultas. Lo que importa es el criterio. (a) Mira las consultas
que falla cada modelo, no solo la media: con 15 consultas, una diferencia de una consulta son ~7 puntos. (b) Si E5 sin
prefijos rinde peor que con ellos, es el recordatorio de usar el modelo como se entrenó. (c) El modelo de API suele
ganar en calidad y cuesta por consulta y por reindexación; el local es gratis y privado, y su tiempo incluye la
carga. Elige el más barato que no pierda consultas importantes.

</details>
