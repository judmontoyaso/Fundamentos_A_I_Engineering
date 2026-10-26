# Módulo 6 · ¿Falló el retrieval o falló la respuesta?

> **Objetivo:** evaluar un RAG por partes, para que cada fallo apunte a lo que hay que arreglar: la búsqueda, la
> generación o la pregunta misma.
>
> **Lo que te llevas:** un set de preguntas con sus CVs relevantes y su respuesta, la recuperación medida sola, el
> sistema comparado con un oráculo, y la prueba de que una respuesta fiel puede ser falsa.

Índice:

1. [Dos sistemas en uno](#1-dos)
2. [El RAG y el set de preguntas](#2-set)
3. [Etiquetar relevancia](#3-relevancia)
4. [La recuperación, sola](#4-recuperacion)
5. [El oráculo: la generación, sola](#5-oraculo)
6. [El diagnóstico de cada pregunta](#6-diagnostico)
7. [Fiel no es correcta](#7-fiel)
8. [Las métricas de las herramientas](#8-herramientas)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-dos"></a>
## 1. Dos sistemas en uno

Un RAG son dos sistemas encadenados: una **búsqueda** que elige qué documentos ver y un **generador** que responde
con lo que ve. Cuando la respuesta sale mal, la pregunta que decide todo es cuál de los dos falló:

- Si la búsqueda no trajo el documento correcto, ningún prompt lo arregla.
- Si lo trajo y la respuesta salió mal, cambiar la búsqueda no ayuda.

Un eval que solo mira la respuesta final mezcla las dos causas. Este módulo las separa.

---

<a name="2-set"></a>
## 2. El RAG y el set de preguntas

El sistema ([`comun/ev_rag.py`](../comun/ev_rag.py)) busca en los 30 CVs del curso con las piezas del primer curso:
búsqueda densa (el embedder del Módulo 2) y BM25 (Módulo 4), fusionadas con RRF. Pasa los 3 mejores al generador, que
responde **solo** con ellos, cita sus números y avisa si no hay información. Las dos mitades (`buscar()` y
`responder()`) se pueden llamar por separado: eso es lo que hace posible el diagnóstico.

El set ([`code/01_preguntas_y_recuperacion.py`](code/01_preguntas_y_recuperacion.py)) tiene 20 preguntas de cinco
tipos, elegidos por cómo pueden fallar:

| Tipo | Ejemplo | Qué pone a prueba |
|---|---|---|
| Dato de un candidato (6) | "¿Qué correo tiene Óscar Lindo?" | Encontrar el CV por nombre y leer bien |
| Búsqueda por tecnología (6) | "¿Quiénes trabajan con PyTorch?" | La palabra exacta: lo que BM25 hace bien |
| Paráfrasis (4) | "¿Quién administra bases de datos?" (el CV dice "DBA") | El significado: lo que la búsqueda densa debería hacer bien |
| Agregación (2) | "¿Quién tiene más años de experiencia de todos?" | Preguntas sobre todo el corpus |
| Sin respuesta (2) | "¿Quién habla japonés?" | Abstenerse en vez de inventar |

---

<a name="3-relevancia"></a>
## 3. Etiquetar relevancia

Cada pregunta lleva dos etiquetas: **qué CVs hay que recuperar** y **qué debe contener la respuesta**. La primera es
la que casi nadie escribe, y sin ella no hay forma de saber si la búsqueda falló. Tres reglas:

- **Relevante = necesario para responder**, no "relacionado". Para "¿quién sabe Terraform?" solo es relevante el CV que
  dice Terraform, no los otros de cloud.
- **Las preguntas de agregación tienen muchos relevantes**: "¿cuántos trabajan con Python?" necesita los 7 CVs que lo
  mencionan.
- **Las preguntas sin respuesta tienen cero relevantes**, y lo correcto es abstenerse.

---

<a name="4-recuperacion"></a>
## 4. La recuperación, sola

La recuperación se mide **sin LLM**, gratis y en segundos: para cada pregunta, qué fracción de sus relevantes está en
el top 3 (**recall@3**).

| Tipo | Recall@3 medio |
|---|---|
| Dato de un candidato | 100 % |
| Búsqueda por tecnología | 100 % |
| **Paráfrasis** | **50 %** |
| **Agregación** | **21 %** |

- Las **paráfrasis** fallan justo donde se esperaba que la búsqueda densa ayudara: "¿quién hace pruebas automatizadas
  de software?" no recupera al CV que dice "QA automation, Selenium, Cypress", y "¿quién administra bases de datos?"
  no recupera el que dice "DBA de Oracle y PostgreSQL". El embedder multilingüe pequeño no une esos conceptos, y BM25 no
  tiene palabras en común.
- La **agregación** falla por diseño: con k = 3 es imposible traer los 7 CVs con Python. Ninguna mejora del embedder lo
  arregla. Hace falta otra forma de responder (ejercicio 4).

---

<a name="5-oraculo"></a>
## 5. El oráculo: la generación, sola

Para medir la generación sin el ruido de la búsqueda se usa un **oráculo**: se le pasan al generador exactamente los
CVs relevantes, la recuperación perfecta. Si con el oráculo responde mal, el fallo es suyo.
[`code/02_recuperacion_o_respuesta.py`](code/02_recuperacion_o_respuesta.py) responde cada pregunta dos veces (con lo
recuperado y con el oráculo) y lo repite dos veces:

| | Respuestas correctas |
|---|---|
| **Oráculo** (recuperación perfecta) | **40 / 40 (100 %)** |
| **Sistema** (recuperación real) | 32 / 40 (80 %) |

Con el contexto correcto, el generador acierta todo, incluidas las dos agregaciones y las dos abstenciones. **Los 8
fallos del sistema son de recuperación.** Esta tabla te ahorra una semana de ajustar el prompt del generador, que no
tiene nada que arreglar.

---

<a name="6-diagnostico"></a>
## 6. El diagnóstico de cada pregunta

Con la recuperación y la respuesta medidas, cada pregunta cae en una casilla:

| Casilla | Significado | En el laboratorio |
|---|---|---|
| ok | Recuperó todo lo necesario y respondió bien | 32 |
| **falla la recuperación** | Faltaban relevantes y la respuesta salió mal | **8** (las 2 paráfrasis y las 2 agregaciones, en las dos pasadas) |
| falla la respuesta | Estaban los relevantes y aun así respondió mal | 0 |
| acierta sin recuperar todo | Faltaban relevantes y acertó igual | 0 |

La cuarta casilla merece atención cuando aparece: o la pregunta se podía responder con menos documentos de los que
etiquetaste (revisa la etiqueta), o el modelo respondió con lo que sabe de su entrenamiento, no con tus documentos (y
eso, en un RAG, es un fallo aunque la respuesta sea correcta).

---

<a name="7-fiel"></a>
## 7. Fiel no es correcta

La métrica más usada para evaluar un RAG es la **fidelidad** (*faithfulness*): ¿todo lo que afirma la respuesta está en
los documentos que recibió? [`code/03_fiel_no_es_correcta.py`](code/03_fiel_no_es_correcta.py) la mide con un juez y
la cruza con la corrección:

| | Correcta | Incorrecta |
|---|---|---|
| **Fiel** | 16 | **4** |
| **No fiel** | 0 | 0 |

**Las 4 respuestas incorrectas eran fieles.** Un eval de solo fidelidad habría dado 20 de 20. Y no todas valen lo
mismo:

- "Sin información: ninguno de los CVs menciona pruebas automatizadas" es fiel, incorrecta y **honesta**: el usuario
  sabe que no encontró nada y puede reformular.
- "Gabriel Rojas tiene más años de experiencia: 5 años" es fiel a los 3 CVs que vio, incorrecta y **dañina**: afirma
  algo sobre *todos* los candidatos habiendo visto tres. El juez de fidelidad no lo detecta, porque el número 5 sí está
  en el contexto.

Un eval de RAG necesita tres medidas: **recuperación** (por qué falla), **corrección** (si sirve) y **fidelidad** (si
inventa). Cualquiera de las tres sola te engaña.

---

<a name="8-herramientas"></a>
## 8. Las métricas de las herramientas

Ragas, DeepEval o Phoenix traen estas métricas listas, con otros nombres:

| Herramienta (nombre típico) | Lo que mide | En este módulo |
|---|---|---|
| *context recall* | ¿Están en el contexto los datos que necesita la respuesta de referencia? | recall@k con relevancia etiquetada |
| *context precision* | ¿Lo recuperado es relevante y está arriba? | (ejercicio 2) |
| *faithfulness* | ¿La respuesta está respaldada por el contexto? | el juez del §7 |
| *answer correctness* | ¿Coincide con la respuesta de referencia? | el chequeo por código del §5 |

Son útiles cuando ya sabes qué quieres medir. Muchas usan un LLM para *inferir* la relevancia en lugar de etiquetarla,
lo que convierte una medida gratis y exacta (¿está el CV 13 en el top 3?) en una estimación con sus propios errores
(Módulo 5). Si puedes etiquetar la relevancia, etiquétala.

---

## Resumen del módulo

- Un RAG son **dos sistemas**: mide la búsqueda y la generación **por separado**.
- Etiqueta **qué documentos hay que recuperar**, no solo la respuesta.
- La recuperación se mide **sin LLM**: recall@k por tipo de pregunta (aquí: 100 % en datos y tecnologías, 50 % en
  paráfrasis, 21 % en agregación).
- El **oráculo** aísla la generación: con el contexto correcto acertó 40/40, así que **todos** los fallos eran de
  recuperación.
- Hay preguntas que un RAG con k fijo **no puede** responder (las agregaciones).
- **Fiel no es correcta**: las 4 respuestas incorrectas eran fieles a su contexto; una de ellas afirmaba algo falso
  sobre todo el corpus.

Sigue con [`ejercicios.md`](ejercicios.md).
