# Módulo 1 · Antes de modificar algo, hay que medir

> **Objetivo:** saber dónde está el buscador **hoy**, por tipo de consulta, con métricas que entienden la relevancia
> graduada, y aprender a decidir si una versión le gana a otra de verdad.
>
> **Lo que te llevas:** la línea base de tres modos de búsqueda en 41 consultas, los fallos leídos uno por uno y una
> comparación pareada que muestra por qué un promedio puede mentir.

Índice:

1. [La línea base](#1-base)
2. [Tres métricas y lo que dice cada una](#2-metricas)
3. [Los tres modos](#3-modos)
4. [Lo que dice la línea base](#4-resultados)
5. [Leer los fallos](#5-fallos)
6. [¿Gana de verdad?](#6-gana)
7. [El mapa del curso, visto desde aquí](#7-mapa)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-base"></a>
## 1. La línea base

Cada técnica de este curso se va a comparar contra algo. Ese algo es la **línea base**: el buscador tal como está, medido
con el set de consultas del Módulo 0, guardado por consulta y por modo (`salida/linea_base.jsonl`). Sin ella, "mejoró"
no significa nada.

El buscador ([`comun/as_buscador.py`](../comun/as_buscador.py)) indexa el texto completo de los 119 CVs y busca en tres
modos, todos con piezas del curso de AI Engineering: BM25, densa (MiniLM multilingüe) e híbrida (RRF de las dos).

---

<a name="2-metricas"></a>
## 2. Tres métricas y lo que dice cada una

| Métrica | Pregunta | Por qué |
|---|---|---|
| **nDCG@10** | ¿Los más relevantes están arriba, considerando que un 2 vale más que un 1? | La única de las tres que usa la relevancia graduada. Es la principal del curso |
| **Recall@10** | ¿Qué fracción de los CVs con relevancia 2 está en el top 10? | Si un candidato ideal no está en el top 10, para el reclutador no existe |
| **MRR** | ¿En qué puesto aparece el primer CV con relevancia 2? | Lo que ve quien solo mira el primer resultado |

nDCG suma la ganancia de cada resultado (`2^rel − 1`: 3 para un 2, 1 para un 1) dividida por el logaritmo de su
puesto, y la normaliza por la del orden ideal. Un 1 vale: un CV que cumple el rol pero no el nivel no es inútil, pero
vale menos que uno que cumple todo. Recall y MRR, en cambio, solo cuentan los 2.

---

<a name="3-modos"></a>
## 3. Los tres modos

[`code/01_linea_base.py`](code/01_linea_base.py) mide los tres modos sin ninguna llamada a un LLM: gratis, en segundos y
determinista (la misma corrida da siempre lo mismo). Es la ventaja de medir la búsqueda sola: aquí no hay ruido entre
corridas, y las diferencias son las del sistema.

---

<a name="4-resultados"></a>
## 4. Lo que dice la línea base

| Tipo | BM25 | Densa | Híbrida | n |
|---|---|---|---|---|
| Tecnología | **1.00** | 0.38 | 0.91 | 8 |
| Rol | **0.94** | 0.84 | 0.90 | 4 |
| Paráfrasis | **0.00** | **0.55** | 0.38 | 6 |
| Rol + nivel | 0.68 | 0.41 | 0.54 | 3 |
| Rol + ciudad | 0.74 | 0.46 | 0.56 | 3 |
| Rol + idioma | 0.79 | 0.72 | 0.75 | 2 |
| Numérica | 0.80 | 0.35 | 0.58 | 3 |
| Certificación | 0.96 | 0.69 | 0.90 | 2 |
| Abreviatura | 0.67 | 0.76 | 0.82 | 3 |
| En inglés | 0.44 | 0.62 | 0.49 | 3 |
| Liderazgo | 0.50 | 0.77 | 0.80 | 2 |
| Exclusión | 0.44 | 0.25 | 0.39 | 2 |
| **Total (nDCG@10)** | 0.66 | 0.55 | **0.68** | 41 |
| Recall@10 | 0.62 | 0.53 | 0.65 | |
| MRR | 0.67 | 0.62 | 0.69 | |
| ms por consulta | 0.6 | 14.5 | 14.4 | |

Tres lecturas:

- **BM25 es muy fuerte aquí.** Los CVs del curso nombran sus tecnologías y sus cargos: si la consulta usa las mismas
  palabras, BM25 acierta (1.00 en tecnología). La densa con un embedder pequeño queda atrás en casi todo.
- **La densa solo gana donde no hay palabras en común**: paráfrasis (0.55 contra 0.00), en inglés y liderazgo.
- **La híbrida no es "lo mejor de los dos".** En paráfrasis baja de 0.55 (densa) a 0.38: BM25 mete ruido en el ranking
  fusionado. En tecnología baja de 1.00 (BM25) a 0.91: la densa mete ruido en el otro sentido. Su total es el mejor
  por poco, y el §6 dice cuánto vale ese "por poco".

---

<a name="5-fallos"></a>
## 5. Leer los fallos

[`code/02_leer_los_fallos.py`](code/02_leer_los_fallos.py) muestra, para la peor consulta de cada tipo, los 5 primeros
resultados con su relevancia y sus hechos. Algunos:

- **"Alguien que automatice despliegues y administre contenedores"** → los cinco primeros son **QA automation**. El falso
  amigo "automat" (automation, automatizadas) engaña a BM25 y al embedder a la vez. Ningún ingeniero DevOps en el top 5.
- **"Ingeniero de datos senior"** → tres **analistas de datos senior** antes que el primer ingeniero de datos. El
  buscador entiende "datos" y "muchos años", pero no que "ingeniero de datos" es un rol, y no sabe que senior significa
  7 años o más: el nivel no está escrito en los CVs.
- **"Desarrollador backend que no use Java"** → los cinco primeros **usan Java**. La negación no existe para BM25 (la
  palabra "Java" suma puntos) ni para el embedder.
- **"Recién egresado de desarrollo"** → juniors de QA y ciencia de datos, y en el quinto puesto un desarrollador .NET
  de 12 años.
- **"Ingeniero devops que trabaje remoto"** → el primero no acepta remoto.

Ninguno de estos fallos se arregla con un embedder mejor. Son fallos de **entender la consulta**: un rol, un nivel, un
filtro, una negación. Es el tema del Módulo 2.

---

<a name="6-gana"></a>
## 6. ¿Gana de verdad?

La híbrida tiene el mejor nDCG total (0.68 contra 0.66 de BM25). ¿Es mejor? [`code/03_gana_de_verdad.py`](code/03_gana_de_verdad.py)
compara **consulta a consulta** (las dos se midieron sobre las mismas 41) y calcula un intervalo bootstrap de la
diferencia:

| Comparación | Gana | Pierde | Empata | Diferencia media | IC 95 % | Veredicto |
|---|---|---|---|---|---|---|
| Híbrida contra BM25 | 10 | **20** | 11 | +0.017 | [−0.064, +0.106] | **no se distingue** |
| Densa contra BM25 | 12 | 28 | 1 | −0.115 | [−0.256, +0.034] | no se distingue |
| Híbrida contra densa | 28 | 6 | 7 | +0.132 | [+0.034, +0.228] | **mejor** |

La primera fila es la lección del módulo: **la híbrida pierde en el doble de consultas de las que gana**, y aun así su
media es mayor, porque gana por mucho en pocas (paráfrasis: +0.38 de media) y pierde por poco en muchas (tecnología:
−0.09; numérica: −0.22). El intervalo incluye el cero: con 41 consultas no se puede afirmar que sea mejor.

Elegir "la de mayor promedio" habría escondido que, para la mitad de los reclutadores, la híbrida es peor. Lo que dice
el desglose es otra cosa: **no hay un modo mejor; hay tipos de consulta que necesitan cosas distintas**. Eso apunta a
decidir el modo según la consulta (Módulo 2: *routing*).

---

<a name="7-mapa"></a>
## 7. El mapa del curso, visto desde aquí

| Lo que falla | Dónde se ataca |
|---|---|
| Rol, nivel, ciudad, idioma, negación dentro de la consulta | Módulo 2: entender la consulta y extraer filtros |
| Paráfrasis y falsos amigos ("automat") | Módulos 2 (reescritura) y 4 (reranker, embeddings) |
| Datos que no están en el texto (nivel), tablas | Módulo 3: parsing y lo que se pierde |
| Preguntas numéricas y de agregación | Módulo 6: SQL sobre los hechos |
| El orden de los que sí se encuentran | Módulos 4 (reranker) y 7 (learning to rank) |

---

## Resumen del módulo

- **Mide antes de tocar**: la línea base por consulta y por modo es contra lo que se compara todo.
- **nDCG@10** usa la relevancia graduada; recall@10 y MRR solo cuentan los 2.
- Medir la búsqueda sola es **gratis y determinista**: sin LLM, sin ruido entre corridas.
- **BM25 es fuerte** con un corpus que nombra sus tecnologías; la densa solo gana sin palabras en común.
- **La híbrida no suma lo mejor de los dos**: pierde frente a BM25 en 20 de 41 consultas, y su media mayor no se
  distingue del cero.
- **Los peores fallos son de entender la consulta**: rol, nivel, filtros y negación.

Sigue con [`ejercicios.md`](ejercicios.md).
