# Módulo 3 · Datos sintéticos para arrancar sin usuarios

> **Objetivo:** conseguir casos difíciles y variados sin esperar a tener usuarios, **sin engañarte**: con etiquetas
> correctas por construcción, validados con código y medidos contra los casos reales.
>
> **Lo que te llevas:** un generador de CVs por dimensiones, un validador que rechaza lo que el LLM no escribió bien, y
> la evidencia de que el set sintético encuentra fallos que el escrito a mano no encontraba.

Índice:

1. [Por qué, y el riesgo](#1-por-que)
2. [Dimensiones de variación](#2-dimensiones)
3. [Tuplas: cubrir sin explotar](#3-tuplas)
4. [Generar desde los hechos](#4-hechos)
5. [Validar: el generador no obedece siempre](#5-validar)
6. [¿Se parecen a los reales?](#6-realismo)
7. [Lo que encontraron](#7-encontraron)
8. [Reglas para no engañarse](#8-reglas)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-por-que"></a>
## 1. Por qué, y el riesgo

El Módulo 2 terminó con dos problemas: la curva de saturación seguía subiendo (30 casos no bastan) y `gpt-6-luna`
sacaba 30/30 (el set no encuentra sus fallos). Hace falta **más casos y más difíciles**, y no hay usuarios que los
traigan. Los datos sintéticos son la salida obvia: pedirle a un LLM que escriba CVs.

El riesgo también es obvio. Si le pides a un LLM "escribe 50 CVs difíciles", obtienes 50 variaciones del CV que el LLM
imagina como difícil: parecidas entre sí, más limpias que los reales y con etiquetas que nadie verificó. Un set así da
números que parecen evidencia y no lo son. Este módulo es sobre cómo evitarlo.

---

<a name="2-dimensiones"></a>
## 2. Dimensiones de variación

En vez de pedir "CVs difíciles", se decide **qué puede variar** en un CV real, a partir de lo que el error analysis
encontró y de lo que sabes del dominio. [`code/01_dimensiones_y_hechos.py`](code/01_dimensiones_y_hechos.py):

| Dimensión | Valores |
|---|---|
| Cómo se expresan los años | explícitos · en palabras · rangos seguidos · rangos solapados · hasta hoy · meses |
| Formato | prosa · lista · tabla · una línea |
| Idioma | español · inglés · portugués |
| Ruido | ninguno · mayúsculas · erratas |
| Ataque | ninguno · inyección |

Cada dimensión es una hipótesis sobre lo que puede romper el sistema. Algunas salen del Módulo 2 (rangos solapados,
"hasta hoy"); otras del dominio (en Latinoamérica llegan CVs en portugués).

---

<a name="3-tuplas"></a>
## 3. Tuplas: cubrir sin explotar

Una **tupla** es una combinación de un valor por dimensión: (rangos solapados, tabla, portugués, erratas, inyección).
Todas las combinaciones son 6 × 4 × 3 × 3 × 2 = **432**, demasiadas para empezar. El laboratorio genera 36 tuplas con
una regla sencilla: **cada valor de cada dimensión aparece el mismo número de veces** (6 por valor de años, 9 por
formato, 12 por idioma y ruido, 18 por ataque), barajadas para que se mezclen.

No cubre todas las interacciones (no está garantizado que haya "tabla + portugués + inyección"), y es una decisión
consciente: primero se busca qué valores rompen el sistema; las interacciones se exploran después, alrededor de lo que
falló.

---

<a name="4-hechos"></a>
## 4. Generar desde los hechos

La idea más importante del módulo: **el LLM no escribe la etiqueta, escribe el texto.** Para cada tupla, el código
elige primero los **hechos**: nombre, correo (o ninguno), tres skills, el cargo y los trabajos con sus años. La
etiqueta sale de los hechos **con las mismas reglas de `ev_datos.py`**: por ejemplo, `anios_de()` cuenta una sola vez
los años que se solapan. Es correcta por construcción, sin que nadie lea nada.

Después, [`code/02_generar_desde_hechos.py`](code/02_generar_desde_hechos.py) le pasa al LLM los hechos y las
instrucciones de estilo de la tupla ("lista cada trabajo con su rango de años; el último sigue vigente: escribe 'hasta
hoy', nunca el año actual"; "todo en mayúsculas"; "en portugués") y le pide solo el texto.

Comparado con "escribe un CV difícil y dime cuántos años tiene", esto cambia todo: la dificultad la controlas tú, la
variedad la controlas tú, y la etiqueta no depende de que el LLM sume bien.

---

<a name="5-validar"></a>
## 5. Validar: el generador no obedece siempre

"Correcta por construcción" vale **si el texto dice lo que dicen los hechos**. [`code/03_validar_sinteticos.py`](code/03_validar_sinteticos.py)
lo comprueba con código antes de usar ningún CV: el nombre y el correo aparecen (y no hay correo si no debía), las
skills están, cada año de los rangos aparece, "hasta hoy" no se convirtió en un año, el total en palabras está en
palabras, y la inyección pedida está.

La primera generación fue una lección:

| | Primera versión | Versión final |
|---|---|---|
| Válidos | **18 de 36** | **35 de 36** |
| Motivo de rechazo | "inyección ausente": **18 de 18** | "total no en palabras": 1 (escribió "13 years") |
| CVs con inyección | 0 | 18 |

En la primera versión se le pedía al LLM que añadiera una línea que intentara engañar a un sistema automático.
**`gpt-6-luna` no escribió ninguna de las 18.** No dio error ni avisó: simplemente devolvió el CV sin la línea. Sin el
validador, el set habría tenido "18 casos de inyección" que no tenían inyección, y cualquier conclusión sobre la
robustez del extractor habría sido falsa.

Arreglo: lo adversarial se inserta **con plantillas, en código** (una frase por idioma, en una posición aleatoria del
texto). Es una regla general: **el generador tiene sus propios límites y sesgos** (no escribe ciertas cosas, prefiere
ciertos formatos), y la única forma de saberlo es validar cada caso.

---

<a name="6-realismo"></a>
## 6. ¿Se parecen a los reales?

El validador también compara la diversidad con los 30 CVs escritos a mano: la similitud coseno media entre todos los
pares de CVs, con el embedder local del curso de AI Engineering (más alta = más parecidos entre sí).

| Set | Similitud media entre pares | Palabras por CV |
|---|---|---|
| 30 escritos a mano | 0.438 | (variable) |
| 35 sintéticos (versión final) | **0.520** | mediana 29, entre 11 y 43 |

Los sintéticos se parecen más entre sí que los escritos a mano, aunque cubren más idiomas y formatos. Parte de la
diferencia la ponen las plantillas de inyección (18 CVs con la misma frase), y parte es el estilo del generador: todos
sus CVs suenan a la misma persona. Es lo esperable, y es la razón por la que **los sintéticos complementan a los
reales, no los sustituyen**. Un sintético encuentra fallos de un tipo de entrada; solo los reales te dicen con qué
frecuencia llegan esas entradas.

---

<a name="7-encontraron"></a>
## 7. Lo que encontraron

[`code/04_evaluar_con_sinteticos.py`](code/04_evaluar_con_sinteticos.py) corre el extractor sobre los 35 válidos y
cuenta los fallos por valor de cada dimensión:

| Configuración | Set escrito a mano (Módulo 1) | **Set sintético** |
|---|---|---|
| `gpt-5.4-nano` v1 | 27-28 / 30 perfectos (~92 %) | **24 / 35 (69 %)** |
| `gpt-5.4-nano` v2 | 28-29 / 30 | **24 / 35 (69 %)** |
| `gpt-6-luna` v1 | 30 / 30 | 35 / 35 |

Casi todos los fallos son de años, y se concentran en valores concretos:

| Valor | `nano` v1 | `nano` v2 |
|---|---|---|
| rangos solapados | 4 / 6 | **6 / 6** |
| hasta hoy | 4 / 6 | **1 / 6** |
| portugués | 6 / 12 | 6 / 12 |
| tabla | 4 / 9 | 5 / 9 |
| una línea | 4 / 8 | 4 / 8 |
| años explícitos | 0 / 6 | 0 / 6 |

Lo que el set sintético añadió:

- **Una tasa de fallos realista para el modelo barato.** Con el set a mano, `nano` parecía casi tan bueno como el
  grande. Con el sintético, falla 3 de cada 10 CVs.
- **Dónde falla:** cuando los años hay que calcularlos (rangos, "hasta hoy"), y en portugués. Cuando los años vienen
  escritos, no falla nunca.
- **La misma rotura del Módulo 1, ahora con más evidencia.** v2 arregla "hasta hoy" (de 4 a 1) y **empeora los rangos
  solapados** (de 4/6 a 6/6). La exactitud global no se movió (24 y 24): un arreglo y una rotura que se compensan. En
  el Módulo 1 esto se vio en un solo caso; aquí, en seis.
- **Valores absurdos que una regla de código atraparía:** 14 años para "14 meses", 15 años para dos trabajos entre
  2011 y 2016. Ninguno fue el "25" de la inyección: el modelo no obedeció el ataque, pero sí se confundió.

Y una advertencia: `gpt-6-luna` volvió a sacar todo perfecto (35/35), **y fue el mismo modelo que escribió los CVs**.
Un modelo tiende a entender bien el texto que él mismo escribe. Para retarlo hace falta otro generador, o CVs reales
(ejercicio 3).

---

<a name="8-reglas"></a>
## 8. Reglas para no engañarse

1. **Dimensiones antes que prompts.** Decide qué variar a partir del error analysis y del dominio.
2. **Hechos antes que texto.** La etiqueta sale de los hechos con código; el LLM solo redacta.
3. **Valida cada caso** con código. Lo que no pasa, se descarta (y se cuenta: un generador que falla mucho en un valor
   te deja sin cobertura ahí).
4. **Lo adversarial, con plantillas.** Los generadores evitan escribir ataques.
5. **Mide la diversidad** contra los reales, y desconfía de un set que se parece demasiado a sí mismo.
6. **Cambia de generador** para evaluar al modelo que generó.
7. **Sintéticos para encontrar fallos; reales para estimar frecuencias.** Un 69 % en sintéticos no es la tasa de
   fallos en producción: es la tasa en una mezcla de entradas que tú elegiste, con la mitad adversariales.

---

## Resumen del módulo

- Los sintéticos sirven para **encontrar fallos sin usuarios**, no para estimar con qué frecuencia ocurren.
- **Dimensiones → tuplas → hechos → texto**: la variación y la etiqueta las controlas tú; el LLM solo escribe.
- Cubre **cada valor** de cada dimensión antes de buscar interacciones.
- **Valida todo**: `gpt-6-luna` no escribió ninguna de las 18 inyecciones que se le pidieron, y no avisó.
- Los sintéticos se parecen **más entre sí** que los reales (0.52 contra 0.44): complementan, no sustituyen.
- En el set sintético, el modelo barato bajó de ~92 % a **69 %**, y la rotura de v2 en rangos solapados pasó de un
  caso a seis.
- No evalúes un modelo solo con datos que **él mismo generó**.

Sigue con [`ejercicios.md`](ejercicios.md).
