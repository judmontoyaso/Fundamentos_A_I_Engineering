# Módulo 5 · Context engineering y long context

> **Objetivo:** decidir qué va al contexto del generador (los mejores resultados, todo el corpus o una versión
> compacta) midiendo aciertos, tokens y latencia, y comprobar si los efectos famosos del contexto largo se dan en tu
> sistema.
>
> **Lo que te llevas:** cuatro formas de armar el contexto comparadas en preguntas con respuesta conocida, y la medición
> de dónde se pierden los candidatos cuando todo el corpus va en el contexto.

Índice:

1. [La tentación del contexto largo](#1-tentacion)
2. [Preguntas que piden listas, cuentas y máximos](#2-preguntas)
3. [Cuatro contextos](#3-contextos)
4. [Lo que pasó](#4-resultados)
5. [Compactar no salvó al contexto largo](#5-compactar)
6. [¿Se pierde lo del medio?](#6-medio)
7. [Qué va al contexto](#7-reglas)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-tentacion"></a>
## 1. La tentación del contexto largo

Los 119 CVs del curso ocupan unos 10.000 tokens: caben de sobra en el contexto de cualquier modelo actual. La tentación
es obvia: **¿para qué buscar, si se le puede dar todo al modelo?** Sin recuperación no hay recall que perder, ni
filtros que fallen, ni ranking que ordenar mal.

Las objeciones habituales son el costo (diez veces más tokens por pregunta), la latencia y que los modelos "se pierden"
en contextos largos. Este módulo las mide en lugar de darlas por sabidas.

---

<a name="2-preguntas"></a>
## 2. Preguntas que piden listas, cuentas y máximos

[`code/01_que_va_al_contexto.py`](code/01_que_va_al_contexto.py) tiene 10 preguntas cuya respuesta exacta se calcula
desde los hechos:

- **Listas:** "¿Quiénes trabajan con Kafka?" (8 personas), "¿Quiénes son de Medellín y tienen inglés C1 o nativo?" (5).
- **Cuentas:** "¿Cuántos candidatos han liderado equipos?" (18), "¿Cuántos son junior?" (20).
- **Máximos:** "¿Quién es el analista de datos con más años de experiencia?".

Una respuesta es correcta solo si la lista es **exacta** (ni uno de más, ni uno de menos) o la cuenta es exacta. Es una
vara alta a propósito: para un reclutador, una lista a la que le falta un candidato es una lista con un candidato
perdido.

---

<a name="3-contextos"></a>
## 3. Cuatro contextos

| Contexto | Qué recibe el generador | Tokens de entrada |
|---|---|---|
| **top 5** | Los 5 CVs que trae la búsqueda entendida (filtros suaves del Módulo 2) | ~600 |
| **top 15** | Los 15 mejores | ~1.500 |
| **todo (texto)** | Los 119 CVs completos | ~9.700 |
| **todo (fichas)** | Las 119 fichas del índice, una línea cada una (rol, años, ciudad, remoto, inglés, skills, certificación, liderazgo) | ~5.000 |

El generador es el mismo (`gpt-6-luna`) en los cuatro casos.

---

<a name="4-resultados"></a>
## 4. Lo que pasó

Dos corridas completas:

| Contexto | Aciertos (corrida 1 · 2) | Tokens | Segundos por pregunta |
|---|---|---|---|
| top 5 | 6 · 6 | 614 | 2.4 · 4.0 |
| **top 15** | **8 · 8** | 1.469 | 2.4 · 3.2 |
| todo (texto) | 5 · 7 | 9.701 | 4.7 · 5.2 |
| todo (fichas) | 5 · 5 | 5.022 | 3.2 · 3.3 |

**Darle todo al modelo no ganó.** El top 15 acertó más que el corpus completo en las dos corridas, con seis veces menos
tokens y algo menos de latencia. Mirando pregunta por pregunta:

- **Las listas con todo el corpus pierden a alguien.** "¿Quiénes trabajan con Kafka?" devolvió 7 de los 8 en las dos
  corridas; "¿quiénes saben dbt?", 4 de 5. El top 15 los encontró todos: con menos candidatos delante, recorrer la lista
  completa es más fácil.
- **Las cuentas sobre todo el corpus fallan casi siempre**, con cualquier contexto: 16 en vez de 18 líderes, 22 en vez de
  20 juniors. Contar 119 elementos leyéndolos es exactamente lo que un LLM hace mal y una consulta sobre las fichas hace
  bien (Módulo 6).
- **El top 5 falla por recall**: "¿cuántos analistas de seguridad hay?" no se puede responder bien viendo 5 CVs si hay 10.
- **El contexto largo varía más**: 5 y 7 aciertos en dos corridas idénticas, contra 8 y 8 del top 15.

---

<a name="5-compactar"></a>
## 5. Compactar no salvó al contexto largo

La idea de *context engineering* más común es compactar: en vez de los textos, una línea por candidato con lo esencial.
Bajó los tokens a la mitad (5.000) y **no mejoró los aciertos** (5 y 5). Las listas siguieron perdiendo candidatos y las
cuentas siguieron desviándose. El problema no era el ruido de los textos: era pedirle al modelo que recorra 119
elementos sin saltarse ninguno. Compactar ahorra dinero; no le da al modelo una capacidad que no tiene.

---

<a name="6-medio"></a>
## 6. ¿Se pierde lo del medio?

El efecto más citado del contexto largo es *lost in the middle*: los modelos usan peor la información del centro del
contexto que la de los extremos. [`code/02_donde_se_pierde.py`](code/02_donde_se_pierde.py) lo pone a prueba: cuatro
preguntas de lista, los 119 CVs en cinco órdenes barajados distintos, y para cada candidato esperado, si apareció y
dónde estaba.

| Posición en el contexto | Encontrados |
|---|---|
| Primer tercio | 35 / 40 (88 %) |
| Tercio del medio | 30 / 32 (**94 %**) |
| Último tercio | 32 / 38 (84 %) |

**No hubo efecto "lost in the middle"**: el centro salió incluso mejor que los extremos (con estos tamaños, las
diferencias son ruido). Lo que sí hubo es una pérdida **pareja**: alrededor de 1 de cada 8 candidatos esperados no
apareció, estuviera donde estuviera, y solo 11 de 20 listas salieron exactas. El problema de este modelo con este
contexto es la **exhaustividad**, no la posición.

Es la razón de medir los efectos famosos en tu sistema: el efecto existe en otros modelos y otras tareas, y aquí no
apareció. Si hubieras reordenado el contexto para poner lo importante en los extremos, habrías arreglado un problema que
no tenías y dejado el que sí tenías.

---

<a name="7-reglas"></a>
## 7. Qué va al contexto

Con estos números, para este sistema:

- **Recupera y pasa pocos, pero los suficientes**: el top 15 de una buena búsqueda ganó a todo el corpus en aciertos,
  costo y latencia. Con 5, se pierden respuestas por recall.
- **No le pidas al LLM que cuente ni que sea exhaustivo sobre muchos elementos**: cuentas y listas completas se
  resuelven con código sobre datos estructurados (Módulo 6).
- **Compactar ahorra tokens; no arregla lo que el modelo no sabe hacer.**
- **Mide los efectos del contexto largo en tu tarea** antes de diseñar alrededor de ellos.
- **El contexto largo sirve** cuando la pregunta exige leer muchos documentos con atención (comparar dos CVs en
  profundidad, resumir un expediente) y la recuperación no sabe qué elegir. Para "encontrar los que cumplen X", la
  búsqueda sigue ganando.

---

## Resumen del módulo

- Los 119 CVs caben en el contexto, y **darle todo al modelo no ganó**: top 15 acertó 8 de 10 dos veces; todo el
  corpus, 5 y 7, con seis veces más tokens.
- Con todo el corpus, **las listas pierden candidatos** y **las cuentas se desvían**: tareas de exhaustividad.
- **Compactar a fichas** bajó los tokens a la mitad y no mejoró los aciertos.
- **No hubo "lost in the middle"**: el medio se encontró igual o mejor (94 %) que los extremos; la pérdida fue pareja,
  ~1 de cada 8.
- Para listas completas y cuentas, **código sobre datos estructurados**, no lectura del LLM.

Sigue con [`ejercicios.md`](ejercicios.md).
