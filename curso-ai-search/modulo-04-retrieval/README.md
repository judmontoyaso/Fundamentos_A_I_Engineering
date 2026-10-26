# Módulo 4 · Un retrieval que traiga el documento correcto

> **Objetivo:** medir las tres técnicas clásicas para mejorar la recuperación (un **reranker**, **late interaction** y
> **afinar el embedder**) contra la alternativa simple, y descubrir cuándo valen la pena.
>
> **Lo que te llevas:** un reranker con LLM que paga sobre la búsqueda base y no sobre la entendida, una late interaction
> sin entrenar que deja atrás a la densa, y un embedder afinado evaluado con un holdout que destapa lo que aprende.

Índice:

1. [Dónde actúa cada técnica](#1-donde)
2. [Un reranker con LLM](#2-reranker)
3. [El reranker depende de lo que hay antes](#3-depende)
4. [Late interaction](#4-late)
5. [Afinar el embedder](#5-afinar)
6. [La trampa de evaluarlo](#6-trampa)
7. [Qué elegir](#7-elegir)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-donde"></a>
## 1. Dónde actúa cada técnica

| Técnica | Qué cambia | Costo |
|---|---|---|
| **Reranker** | El orden del top N que trajo la búsqueda. No trae nada nuevo | Una llamada (o un modelo) por par consulta-documento, en cada búsqueda |
| **Late interaction** | Cómo se compara la consulta con el documento: token a token en vez de un vector por documento | Guardar un vector por token: decenas de veces más espacio |
| **Afinar el embedder** | El espacio de vectores, ajustado a tu dominio | Datos de entrenamiento, una vez; reindexar todo cuando cambie |

Las tres se miden contra la búsqueda del Módulo 1 (base: 0.69 de nDCG@10, densa: 0.55) y, cuando tiene sentido, contra
la búsqueda entendida del Módulo 2 (filtros suaves: 0.89).

---

<a name="2-reranker"></a>
## 2. Un reranker con LLM

[`code/01_reranker_llm.py`](code/01_reranker_llm.py): un reranker **puntual**. El modelo barato califica cada par
(consulta, CV) de 0 a 2 con la misma escala que las etiquetas, en paralelo, y el top 20 se reordena por esa nota.

| Tipo | base | base + rerank | suaves | suaves + rerank |
|---|---|---|---|---|
| Tecnología | 0.94 | 1.00 | 1.00 | 1.00 |
| Paráfrasis | 0.38 | **0.57** | 1.00 | 1.00 |
| Rol + nivel | 0.54 | 0.73 | 0.72 | 0.71 |
| Rol + ciudad | 0.56 | 0.70 | 0.86 | **0.79** |
| Numérica | 0.64 | 0.70 | 0.67 | **0.80** |
| En inglés | 0.44 | 0.85 | 0.91 | 0.91 |
| Exclusión | 0.39 | 0.45 | 0.63 | **0.88** |
| **Total** | 0.69 | **0.81** | 0.89 | **0.91** |

(La tabla completa, por los 12 tipos, la imprime el laboratorio.)

Sobre la base, el reranker sube 12 puntos: entiende el nivel, el inglés y el idioma de la consulta mejor que el
parecido de textos. Pero en paráfrasis se queda en 0.57: **solo puede reordenar lo que está en el top 20**, y para
"alguien que automatice despliegues" la búsqueda base no trajo a los DevOps. Un reranker no arregla la recuperación.

---

<a name="3-depende"></a>
## 3. El reranker depende de lo que hay antes

Comparación pareada consulta a consulta:

| | Gana | Pierde | Diferencia | IC 95 % |
|---|---|---|---|---|
| base + rerank contra base | 25 | 2 | **+0.13** | [+0.08, +0.19] |
| suaves + rerank contra suaves | 7 | 5 | +0.02 | [−0.01, +0.06] |

Sobre la búsqueda entendida, **no se distingue del ruido**: arregla la exclusión (0.63 → 0.88) y la numérica (0.67 →
0.80), y empeora rol + ciudad (0.86 → 0.79). Y cuesta 20 llamadas por consulta, unos 5 segundos la primera vez.

La lección generaliza: **el valor de una técnica depende de lo que ya hace el sistema**. El reranker y el parser
arreglan cosas parecidas (entender nivel, idioma, rol), así que el segundo que llega aporta poco. Una técnica que en un
artículo "sube 12 puntos" puede subir 2 en tu sistema. Por eso se mide en tu sistema, no en el de otro.

---

<a name="4-late"></a>
## 4. Late interaction

La búsqueda densa resume cada CV en **un vector** (el promedio de sus tokens). Un CV con diez tecnologías queda en el
"centro" de todas, y una consulta de una sola tecnología no se parece mucho a ese centro. **Late interaction** (la idea
de ColBERT) guarda un vector por **token** y puntúa con **MaxSim**: para cada token de la consulta, el token más parecido
del CV; la nota es la suma.

[`code/02_late_interaction.py`](code/02_late_interaction.py) lo hace con **el mismo MiniLM**, sin entrenar ni descargar
nada: sus vectores por token, en vez del promedio. No es ColBERT (que se entrena para esto), es su idea medida aquí:

| Tipo | densa | **MaxSim** | híbrida (densa) | híbrida (MaxSim) |
|---|---|---|---|---|
| Tecnología | 0.38 | **0.98** | 0.91 | 1.00 |
| Rol + nivel | 0.41 | 0.77 | 0.54 | 0.73 |
| Abreviatura | 0.76 | 0.94 | 0.82 | 0.94 |
| En inglés | 0.62 | **0.90** | 0.49 | 0.59 |
| Liderazgo | 0.77 | 0.95 | 0.80 | 1.00 |
| Paráfrasis | 0.55 | 0.60 | 0.38 | 0.46 |
| **Total** | 0.55 | **0.81** | 0.68 | 0.77 |

El mismo modelo, comparando token a token, pasa de 0.55 a **0.81**, por encima de BM25 (0.66) y de la híbrida (0.68). La
tecnología pasa de 0.38 a 0.98: "PyTorch" encuentra el token "pytorch" del CV en vez de diluirse en el promedio. Y
combinarla con BM25 **la empeora** (0.77): lo mismo que en el Módulo 1, fusionar no siempre suma.

El costo: 10.197 vectores en vez de 119 (86 veces más espacio), y una latencia parecida aquí (~15 ms por consulta) que
con millones de documentos exige índices especiales (PLAID, compresión de vectores).

Con el parser del Módulo 2 encima, la diferencia desaparece: filtros suaves sobre la híbrida, 0.89; sobre MaxSim, 0.90 (6
consultas ganadas y 6 perdidas). Cuando la consulta ya está entendida, el ranking de partida importa poco.

---

<a name="5-afinar"></a>
## 5. Afinar el embedder

[`code/03_afinar_el_embedder.py`](code/03_afinar_el_embedder.py) entrena MiniLM con pares (consulta, CV) generados por
plantillas **desde los hechos**, con plantillas **distintas** a las del set de prueba ("perfil de {rol}", "{skill} y
{skill}", "{rol} con experiencia en {skill}", "candidato de {ciudad} que sepa {skill}"). La pérdida es la contrastiva de
siempre (MultipleNegativesRankingLoss, escrita a mano en 15 líneas): cada consulta debe parecerse más a **su** CV que a
los otros CVs del lote. Una época, en CPU, poco más de un minuto.

Evaluado con los mismos 119 CVs: la densa pasa de **0.55 a 0.73**.

---

<a name="6-trampa"></a>
## 6. La trampa de evaluarlo

Ese 0.73 tiene trampa: el modelo se entrenó **con los mismos CVs** con los que se evalúa. Aprendió a reconocer esos 119
documentos concretos. En producción llegan CVs nuevos cada día.

Para medirlo honestamente, se entrena **sin** los CVs de cuatro roles (seguridad, móvil, QA, cloud) y se evalúa en las 11
consultas cuyos relevantes son de esos roles:

| Consulta (roles no vistos al entrenar) | densa base | afinada |
|---|---|---|
| Selenium | 0.49 | **0.93** |
| Flutter | 0.24 | **0.82** |
| desarrollador móvil | 0.78 | 0.94 |
| mobile developer | 0.77 | 0.93 |
| **quien haga pruebas automatizadas de software** | 0.64 | **0.24** |
| (las otras seis) | | sin cambios o ±0.05 |
| **Media de las 11** | 0.75 | 0.84 |

Generaliza en parte: con roles que no vio, la búsqueda por tecnología mejora mucho. Pero **la paráfrasis empeora**
(0.64 → 0.24): las plantillas de entrenamiento nombran siempre tecnologías y roles, así que el modelo aprendió a
buscar por esas palabras y desaprendió algo de lo que sabía hacer con descripciones. **Un embedder afinado aprende lo que
le enseñan tus pares, también sus sesgos.** Si las consultas reales tienen paráfrasis, los pares de entrenamiento
también tienen que tenerlas.

---

<a name="7-elegir"></a>
## 7. Qué elegir

Con los números de este módulo, para este buscador:

| Técnica | Total (nDCG@10) | Cuándo |
|---|---|---|
| Entender la consulta (Módulo 2) | 0.89 | Primero. Es la mejora más grande y la más barata de mantener |
| + reranker | 0.91 (no se distingue) | Si quedan tipos concretos que el parser no resuelve (exclusión, numérica) y la latencia lo permite |
| MaxSim en vez de densa | 0.81 sin parser · 0.90 con parser | Cuando la primera etapa importa (sin parser, o con muchos documentos que filtrar) |
| Embedder afinado | 0.73 (densa, mismo corpus) | Con datos de entrenamiento que se parezcan a las consultas reales, y evaluado con holdout |

Ninguna técnica sustituye a entender la consulta, y todas se miden en tu sistema.

---

## Resumen del módulo

- Un **reranker** solo reordena lo que se recuperó: sobre la base sube 12 puntos; sobre la búsqueda entendida, 2 (no se
  distingue del ruido), a 20 llamadas por consulta.
- **El valor de una técnica depende de lo que el sistema ya hace**: mídela en tu sistema.
- **Late interaction** con el mismo MiniLM, sin entrenar: de 0.55 a **0.81**; tecnología de 0.38 a 0.98. A cambio, 86
  veces más vectores.
- **Afinar el embedder**: 0.55 → 0.73 en el mismo corpus, una medida inflada. Con holdout, mejora en roles no vistos
  pero **empeora la paráfrasis** (0.64 → 0.24): aprende los sesgos de sus pares.
- Con la consulta entendida, el ranking de partida importa poco (0.89 contra 0.90).

Sigue con [`ejercicios.md`](ejercicios.md).
