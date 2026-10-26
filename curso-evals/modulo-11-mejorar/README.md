# Módulo 11 · Mejorar el sistema con lo que dicen los evals

> **Objetivo:** usar los evals para mejorar el sistema **sin engañarte**: iterar sobre un set de desarrollo, confirmar
> en un holdout que nadie miró, y preferir los cambios que superan el ruido con claridad.
>
> **Lo que te llevas:** cinco versiones del extractor, cada una nacida de un fallo medido; la prueba de que con 30
> casos el ruido iguala a la diferencia entre prompts; y un cambio estructural (sumar en código) que sí la supera.

Índice:

1. [El ciclo](#1-ciclo)
2. [El problema que no se arreglaba](#2-problema)
3. [Cinco versiones](#3-versiones)
4. [Desarrollo y holdout](#4-holdout)
5. [Lo que no cabe en el schema se pierde](#5-schema)
6. [El ruido y el sobreajuste](#6-ruido)
7. [Reglas para mejorar](#7-reglas)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-ciclo"></a>
## 1. El ciclo

Mejorar con evals es un ciclo de cinco pasos, y cada uno tiene su error típico:

| Paso | Qué haces | El error típico |
|---|---|---|
| 1. Leer los fallos | Error analysis (Módulo 2) | Saltártelo y cambiar el prompt "por si acaso" |
| 2. Hipótesis | "Falla porque X" | Arreglar el síntoma, no la causa |
| 3. Cambio | El más pequeño que ataque la causa | Cambiar varias cosas a la vez |
| 4. Medir en desarrollo | Caso por caso, con repeticiones (Módulo 1) | Una sola corrida |
| 5. Confirmar en holdout | Un set que no se miró al iterar | No tener holdout, o mirarlo en cada vuelta |

Este módulo recorre el ciclo con un problema que viene del principio del curso.

---

<a name="2-problema"></a>
## 2. El problema que no se arreglaba

Con el modelo barato (`gpt-5.4-nano`), el cálculo de años falló en tres módulos seguidos:

- **Módulo 1:** el prompt v2 arregló "hasta hoy" y **rompió** los rangos solapados (#18: 9 de 10 aciertos con v1, 3
  de 10 con v2).
- **Módulo 3:** en los sintéticos, v2 empeoró los rangos solapados de 4/6 a 6/6 fallidos.
- **Módulo 9:** la regla de McNemar volvió a encontrar el #18 entre los rotos.

Hipótesis: **sumar años a partir de rangos es aritmética, y un modelo pequeño la hace mal**. Más instrucciones sobre
cómo sumar (v2) le dan más trabajo, no menos.

---

<a name="3-versiones"></a>
## 3. Cinco versiones

[`code/01_versiones_del_extractor.py`](code/01_versiones_del_extractor.py):

| Versión | Qué cambia | De dónde sale |
|---|---|---|
| v1 | El prompt inicial | Módulo 1 |
| v2 | + fecha de hoy, reglas de conteo y regla de skills | Los fallos de v1 (Módulo 1) |
| v3 | v1 + **solo** la fecha y la regla de skills | La hipótesis de que la línea de reglas de conteo desestabiliza (Módulo 1, ejercicio 6) |
| **v4** | El modelo **no suma**: extrae cada trabajo con sus años (o un total declarado) y el total **se calcula en código** con la regla de las etiquetas | La hipótesis del §2 |
| v5 | v4 + un campo para la **duración** de un trabajo sin fechas | Los fallos de v4 (§5) |

v4 es un tipo de cambio distinto: no le pide al modelo que haga mejor la suma, **se la quita**. El modelo hace lo que
hace bien (leer y copiar fechas) y el código hace lo que hace bien (contar años sin solapes, con la misma función que
calculó las etiquetas en el Módulo 3).

---

<a name="4-holdout"></a>
## 4. Desarrollo y holdout

[`code/02_desarrollo_y_holdout.py`](code/02_desarrollo_y_holdout.py) mide cada versión en dos sets:

- **Desarrollo:** los 30 CVs del Módulo 1. Todas las versiones nacieron de mirar sus fallos.
- **Holdout:** los 36 CVs sintéticos del Módulo 3, con otra mezcla de formatos e idiomas. Ninguna versión se escribió
  mirándolos.

Un caso cuenta como bien solo si sale perfecto en las dos repeticiones. Dos ejecuciones completas:

| Versión | Desarrollo (30) | Holdout (36) |
|---|---|---|
| v1 | 27 · 27 | 23 · 21 |
| v2 | 27 · 27 | 24 · 26 |
| v3 | 28 · 28 | 24 · 27 |
| **v4** | 28 · 28 | **30 · 32** |
| **v5** | — · **29** | — · **31** |

Y en el holdout, por cómo vienen expresados los años (segunda ejecución):

| Versión | Hasta hoy | Rangos seguidos | **Rangos solapados** | Meses |
|---|---|---|---|---|
| v1 | 1/6 | 3/6 | 1/6 | 5/6 |
| v2 | 4/6 | 4/6 | 1/6 | 6/6 |
| v3 | 5/6 | 3/6 | 1/6 | 6/6 |
| v4 | 6/6 | 5/6 | **6/6** | 4/6 |
| v5 | 5/6 | 5/6 | **6/6** | 5/6 |

Tres lecturas:

- **En desarrollo, las versiones son indistinguibles** (27-29 de 30). Si hubieras elegido mirando solo desarrollo,
  cualquier elección habría sido una apuesta.
- **En el holdout, sumar en código gana con claridad**: 30-32 de 36 frente a 21-27, en las dos ejecuciones. La causa
  está en una columna: los rangos solapados pasan de 1/6 a 6/6. La hipótesis del §2 era correcta.
- **v3 no rompió los solapes, pero tampoco los arregló** (1/6, como v1). Quitar la línea de reglas evitó la rotura de
  v2; no resolvió el problema de fondo.

---

<a name="5-schema"></a>
## 5. Lo que no cabe en el schema se pierde

v4 también trajo fallos nuevos: en desarrollo, el #22 ("3 años como analista junior", con la inyección) y, en el
holdout, los CVs en meses. Antes de suponer lo peor (¿obedecía la inyección?), se midieron esos casos solos, 6 veces
cada uno:

- El #22 acertó 2 de 6. Los otros 4 dieron **0 años**, nunca 30: **no obedeció la inyección**.
- "14 meses de experiencia" dio 0 en 2 de 6, y otro CV en meses, 0 en 6 de 6.

La causa: v4 tenía un campo para los años de inicio y fin de cada trabajo, otro para los meses y otro para un total
declarado, pero **ninguno para "3 años como analista"**, una duración en años sin fechas. Ese hecho no cabía en el
schema, y el modelo a veces lo dejaba fuera. Es la misma lección del Módulo 8 (las certificaciones que no se extraían):
**lo que no cabe en el schema, se pierde**. v5 añade el campo `anios` por trabajo, y en desarrollo pasó a 29/30 (falla
solo el #23, el de las skills en mayúsculas).

---

<a name="6-ruido"></a>
## 6. El ruido y el sobreajuste

La tentación al iterar sobre un set es ir escribiendo reglas para sus casos concretos. Para ver qué pasa,
[`code/03_sobreajustar_a_proposito.py`](code/03_sobreajustar_a_proposito.py) crea "v-trampa": v2 más pistas literales
de los casos de desarrollo que fallaban ("un consultor freelance de 2015 a 2020 que fue líder técnico de 2018 a 2022
tiene 7 años", "si el CV dice 'SAS, R', las skills son 'sas' y 'r'"…).

| Versión | Desarrollo | Holdout |
|---|---|---|
| v2 | **29** / 30 | 28 / 36 |
| v-trampa | 29 / 30 | 27 / 36 |

El resultado esperado era "sube en desarrollo y no en el holdout". **No pasó**: no subió ni en desarrollo. El modelo
pequeño no aplicó ni las pistas literales. Y v2, que en el §4 sacó 27 de 30 dos veces, sacó aquí 29.

Esa última cifra es la lección: **con 30 casos y dos repeticiones, la misma versión varía de 27 a 29 entre
ejecuciones**, tanto como varían las versiones de prompt entre sí. En esas condiciones, iterar prompts mirando el set de
desarrollo es elegir entre ruidos, y el sobreajuste llega solo: te quedas con la versión que tuvo una buena corrida. Las
defensas:

- **Un holdout que no se mira al iterar**, y que se usa una vez al final (como el set de prueba del juez en el Módulo 5).
- **Cambios grandes antes que retoques**: v4 superó el ruido por 5-10 casos en el holdout; las versiones de prompt, por
  0-3.
- **Más casos y más repeticiones** cuando la diferencia que buscas es pequeña (el poder de McNemar, Módulo 9).

---

<a name="7-reglas"></a>
## 7. Reglas para mejorar

1. **Lee antes de cambiar**: cada versión de este módulo sale de un fallo leído.
2. **Ataca la causa**: "un modelo pequeño suma mal" llevó a quitarle la suma, no a explicársela mejor.
3. **Lo que el código hace bien, que lo haga el código**: contar, comparar, validar formatos.
4. **Cada campo nuevo del schema es un hecho que deja de perderse**, y cada hecho sin campo es uno que puede perderse.
5. **Desarrollo para iterar, holdout para decidir.**
6. **Desconfía de las mejoras del tamaño del ruido**: si una versión gana por un caso en 30, no ha ganado.
7. **Re-mide lo crítico** después de cada cambio: v4 mejoró el holdout y empezó a fallar el #22.

---

## Resumen del módulo

- Mejorar es un **ciclo**: leer, hipótesis, cambio pequeño, medir en desarrollo, confirmar en holdout.
- En desarrollo, cinco versiones quedaron entre 27 y 29 de 30: **indistinguibles**.
- En el holdout, **sumar en código** (v4, v5) ganó con claridad: 30-32 de 36 frente a 21-27, con los rangos solapados
  de 1/6 a 6/6.
- v4 perdía las duraciones sin fechas: **lo que no cabe en el schema se pierde** (v5 lo arregla).
- El prompt con pistas literales **no mejoró ni en desarrollo**, y la misma versión varió de 27 a 29 entre ejecuciones:
  con 30 casos, **el ruido iguala a la diferencia entre prompts**.
- Prefiere **cambios estructurales** que superen el ruido por mucho, y decide con un **holdout**.

Sigue con [`ejercicios.md`](ejercicios.md).
