# Módulo 2 · Error analysis sobre un pipeline de extracción

> **Objetivo:** encontrar los fallos que importan **leyendo salidas**, convertirlos en una taxonomía contada y
> priorizada, y solo entonces decidir qué medir.
>
> **Lo que te llevas:** una revisión de 30 salidas con notas abiertas, una taxonomía de 8 categorías con su paso y su
> gravedad, dos evals automáticos validados contra la revisión, y un v2 del pipeline medido con ellos.

Índice:

1. [Por qué antes que cualquier métrica](#1-por-que)
2. [El pipeline: dos de tres pasos sin etiquetas](#2-pipeline)
3. [Leer: la codificación abierta](#3-leer)
4. [Agrupar: la codificación axial](#4-agrupar)
5. [¿Puede agrupar un LLM?](#5-llm)
6. [De fallos a evals](#6-evals)
7. [Medir el arreglo](#7-medir)
8. [Errores comunes](#8-errores)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-por-que"></a>
## 1. Por qué antes que cualquier métrica

La tentación es abrir un catálogo de métricas y elegir las que suenan bien: *faithfulness*, *relevancy*, *toxicity*.
El problema es que una métrica genérica mide un fallo genérico, y tu sistema tiene fallos concretos. Si mides lo que
no falla, el número sale bien y el sistema sigue roto.

El **error analysis** invierte el orden: primero lees salidas reales hasta entender cómo falla el sistema, después
cuentas cada tipo de fallo, y solo para los que importan escribes un eval. Es lento la primera vez y es, con
diferencia, la actividad con más retorno de todo el curso.

---

<a name="2-pipeline"></a>
## 2. El pipeline: dos de tres pasos sin etiquetas

El extractor del Módulo 1 es ahora el primer paso de un pipeline ([`comun/ev_comun.py`](../comun/ev_comun.py),
`pipeline()`), sobre el modelo barato (`gpt-5.4-nano`):

```
texto del CV ─► extraer (FichaCV) ─► clasificar nivel (junior / semi-senior / senior) ─► redactar perfil (≤ 40 palabras)
```

Para la ficha hay etiquetas (Módulo 1). Para el nivel y el perfil **no hay**: nadie escribió cuál es el nivel
correcto de cada candidato ni cuál es el perfil bueno. No se puede calcular una exactitud. Solo se puede leer.

Cada paso tiene su span en la traza: cuando un error aparece en el perfil, la traza dice si nació ahí o si venía de la
extracción.

---

<a name="3-leer"></a>
## 3. Leer: la codificación abierta

[`code/01_correr_y_leer.py`](code/01_correr_y_leer.py) corre el pipeline sobre los 30 CVs y muestra cada caso como
una ficha de lectura: el CV, lo extraído, el nivel con su razón y el perfil. La regla para leer:

- **Una nota por problema, con tus palabras**, en el momento. "El perfil termina con el correo" sirve; "mala calidad"
  no sirve.
- **Sin categorías todavía.** Si empiezas con una lista de categorías, solo ves lo que ya esperabas.
- **Anota el primer error aguas arriba.** Si los años salen mal y por eso el nivel sale mal, el problema es la
  extracción; el nivel solo lo hereda.
- **"ok" también es una nota.** Saber qué funciona es la mitad del análisis.

Las salidas exactas que se leyeron al escribir el curso están en
[`comun/m2_salidas_revisadas.jsonl`](../comun/m2_salidas_revisadas.jsonl) y las notas en
[`comun/m2_notas.py`](../comun/m2_notas.py): 30 casos, **19 con algún problema** y 25 notas. Algunas:

- #2: "8 años de arquitecto cloud y sale semi-senior; el #1 con 9 años es senior".
- #6: "el perfil dice 'Certificación ... ISO 27001': el CV no menciona ninguna certificación".
- #11: "el perfil incluye 'Contacto: ricardo.salas@mail.com'".
- #26: "el perfil menciona 'graduada 2010': deja inferir la edad".

El dato más importante del módulo sale aquí: el eval del Módulo 1 sacaba 27-28 de 30 fichas perfectas con este mismo
modelo. **Los fallos graves no estaban en la ficha**, que era lo único que se medía, sino en los dos pasos que nadie
medía.

---

<a name="4-agrupar"></a>
## 4. Agrupar: la codificación axial

Con todas las notas escritas, se agrupan por **causa** (no por caso) y a cada grupo se le asigna el paso donde nace y
una gravedad para el reclutador (1 = molesta, 3 = daña). [`code/02_de_notas_a_categorias.py`](code/02_de_notas_a_categorias.py)
cuenta y ordena:

| Categoría | Paso | Gravedad | Casos | Prioridad (casos × gravedad) |
|---|---|---|---|---|
| **Nivel sin criterio** (mismos años, distinto nivel; liderazgo ignorado) | nivel | 3 | 6 (20 %) | 18 |
| **Contacto en el perfil** | perfil | 3 | 4 (13 %) | 12 |
| **El perfil inventa** (certificación, intereses, cualidades) | perfil | 3 | 4 (13 %) | 12 |
| Skills mal formadas (cargos como skills, espacios) | extracción | 1 | 5 (17 %) | 5 |
| Error de extracción propagado | extracción | 2 | 2 | 4 |
| Dato sensible en el perfil (año de grado) | perfil | 2 | 1 | 2 |
| Nombre sin normalizar | extracción | 1 | 2 | 2 |
| Relleno genérico | perfil | 1 | 1 | 1 |

Tres lecturas:

- **El fallo más frecuente es de especificación, no del modelo.** Nadie definió qué es senior. El modelo improvisa un
  criterio distinto en cada caso.
- **La prioridad es una guía, no una fórmula.** Un perfil que inventa una certificación puede hacer que contraten a la
  persona equivocada: aunque salga en el puesto 3, nadie lo dejaría para después.
- **La curva de saturación aún sube.** Las categorías distintas vistas tras leer 5, 10, 15, 20, 25 y 30 casos fueron
  4, 5, 5, 6, 7 y 8: la última apareció en el caso #26. Con 30 casos todavía no se ha visto todo. La regla práctica es
  seguir leyendo hasta que pasen 20 o 30 casos sin una categoría nueva.

---

<a name="5-llm"></a>
## 5. ¿Puede agrupar un LLM?

Agrupar 25 notas es mecánico; agrupar 500 no. [`code/03_agrupar_con_llm.py`](code/03_agrupar_con_llm.py) le da al LLM
**solo las notas** (leer sigue siendo trabajo de una persona) y compara su agrupación con la manual mediante el índice
de Rand (de todos los pares de notas, la fracción que las dos agrupaciones tratan igual).

En dos ejecuciones dio **0.95 y 0.97**: casi la misma agrupación. Las diferencias son las interesantes:

- **Juntó "el perfil inventa" con "relleno genérico"** ("contenido no sustentado o genérico"). Suena razonable, pero
  una categoría es gravedad 3 y la otra gravedad 1: fusionarlas infla la gravedad del relleno o diluye la de los
  inventos. **Las fronteras de una categoría son una decisión de prioridad**, no de vocabulario.
- **Juntó el contacto con el año de grado** ("exposición de datos personales"). Es defendible: los dos son privacidad.
- **Separó por síntoma lo que la persona agrupó por causa**: el error propagado del #19 quedó en "cálculo de años" y
  el del #23 en "inconsistencia entre skills y perfil".

Conclusión: el LLM ahorra el trabajo mecánico y propone buenos nombres, pero **revisa cada frontera** antes de contar.
Y nunca le dejes la lectura: si el LLM escribe las notas, solo encuentras los fallos que el LLM sabe reconocer.

---

<a name="6-evals"></a>
## 6. De fallos a evals

Las dos primeras categorías se pueden comprobar con código. Para la tercera hace falta un juez (Módulo 5).
[`code/04_de_fallos_a_evals.py`](code/04_de_fallos_a_evals.py):

- **Contacto en el perfil:** una expresión regular (correos, teléfonos, "linkedin", "contacto"). Gratis y exacta.
- **Nivel sin criterio:** antes del chequeo hay que escribir **la regla que faltaba**
  (`RUBRICA_NIVEL`: menos de 3 años, junior; de 3 a 6, semi-senior; 7 o más, senior, o 5 o más con liderazgo). Con la
  regla, el chequeo es código: aplica la regla a los años correctos de las etiquetas y compara.

Un eval nuevo **se valida antes de usarlo**: ¿encuentra lo mismo que la persona en las salidas ya revisadas?

| Chequeo | Encuentra | La persona encontró | Diferencia |
|---|---|---|---|
| Contacto en el perfil | #4, #11, #16, #22 | los mismos | ninguna |
| Nivel según la regla | 9 casos | 6 casos | +#19, +#22, +#26 |

Las tres diferencias valen más que las coincidencias:

- **#26 (8 años, semi-senior): el chequeo tenía razón y la persona no lo vio.** Leer cansa; el código no.
- **#19: el chequeo marca como fallo de nivel un error que nació en la extracción** (5 años en vez de 7). Detecta bien,
  pero atribuye al paso equivocado. Por eso la revisión humana anota el paso de origen.
- **#22 ("analista junior de SQL", 3 años): el sistema dijo junior y la regla dice semi-senior.** Al leerlo, la
  persona lo dio por bueno: el propio CV dice "junior". La regla contradice el criterio de quien la escribió. **La regla
  está incompleta** (no dice qué hacer cuando el CV declara el nivel) y es el ejercicio 3.

---

<a name="7-medir"></a>
## 7. Medir el arreglo

Con los dos chequeos validados, el v2 del pipeline (`PROMPTS_NIVEL["v2"]` con la regla y `PROMPTS_PERFIL["v2"]` sin
contacto, sin datos que dejen inferir la edad y sin cualidades no escritas) se compara con v1 en una corrida nueva:

| Chequeo | v1 | v2 |
|---|---|---|
| Nivel según la regla | 8/30 fallan | **1/30** (#19: el error de extracción, que v2 no toca) |
| Sin contacto en el perfil | 1/30 | **0/30** |

Y una advertencia que la tabla esconde: en las salidas revisadas, v1 ponía contacto en **4** perfiles; en esta
corrida nueva, en **1**. Es el mismo sistema. La frecuencia de un fallo medida en una sola corrida de 30 casos es una
estimación con mucho ruido: sirve para priorizar, no para afirmar "el 13 % de los perfiles filtra contactos".

Lo que v2 **no** demuestra: que el perfil ya no invente. Ningún chequeo lo mide todavía, y un prompt que pasa los dos
chequeos puede seguir inventando. Hasta tener el juez del Módulo 5, la única forma de saberlo es leer una muestra de
perfiles v2.

---

<a name="8-errores"></a>
## 8. Errores comunes

- **Empezar con categorías prefabricadas** ("alucinación", "toxicidad"): solo encuentras lo que buscabas.
- **Leer diez casos y parar.** La curva de saturación dice cuándo parar, y con 30 todavía subía.
- **Dejar que un LLM lea y anote.** Encuentra lo que sabe reconocer, no lo que le importa a tu usuario.
- **Contar sin gravedad.** Cinco skills mal formadas no pesan lo que una certificación inventada.
- **No anotar el paso de origen.** Arreglarías el perfil cuando el error venía de la extracción.
- **Escribir el eval y no validarlo** contra la revisión manual.

---

## Resumen del módulo

- **Lee antes de medir:** el error analysis decide qué medir.
- **Codificación abierta** (una nota por problema, con tus palabras, sin categorías) y después **axial** (grupos por
  causa, con paso y gravedad).
- Los fallos graves estaban en los pasos **que nadie medía**.
- El fallo más frecuente era una **regla que no existía**: escribe la especificación antes del eval.
- Un LLM puede **agrupar** notas (Rand 0.95-0.97), no **leer** por ti; revisa sus fronteras.
- **Valida cada eval** contra la revisión humana: las diferencias te enseñan sobre el eval, la regla y la persona.
- La frecuencia de un fallo en una corrida es **una estimación ruidosa**.

Sigue con [`ejercicios.md`](ejercicios.md).
