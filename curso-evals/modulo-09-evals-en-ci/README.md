# Módulo 9 · Del notebook al CI

> **Objetivo:** que cada cambio pase por los evals **sin que nadie se acuerde de correrlos**: una suite de tests por
> niveles de costo, una caché que no esconde cambios, una línea base y una regla de decisión que no confunda ruido con
> regresión.
>
> **Lo que te llevas:** una suite de pytest (tests del código de los evals, casos críticos y umbrales), una caché de
> llamadas, una regla con la prueba de McNemar y un workflow de GitHub Actions listo para activar.

Índice:

1. [Un eval que nadie corre no existe](#1-nadie)
2. [Tres niveles, de lo gratis a lo caro](#2-niveles)
3. [La caché: pagar solo lo que cambió](#3-cache)
4. [La línea base](#4-base)
5. [Dos tipos de test: críticos y umbrales](#5-tests)
6. [¿Empeoró, o es ruido?](#6-decidir)
7. [El workflow](#7-workflow)

Código en [`code/`](code/), tests en [`tests/`](tests/), workflow en [`ci/evals.yml`](ci/evals.yml). Ejercicios en
[`ejercicios.md`](ejercicios.md).

---

<a name="1-nadie"></a>
## 1. Un eval que nadie corre no existe

Los Módulos 1 a 8 construyeron evals que se corren a mano, en un laboratorio. Eso sirve para aprender y para investigar
un fallo. No sirve para lo que más importa: **detectar la regresión el día que alguien cambia el prompt** "solo un
poco". Ese día nadie se acuerda de correr el eval. La solución es la misma que con el resto del software: los evals
pasan a ser tests, y los tests corren solos en cada cambio.

Dos diferencias con los tests normales lo complican: **cuestan dinero** (cada caso es una llamada) y **no son
deterministas** (un caso puede fallar por azar). Este módulo resuelve las dos.

---

<a name="2-niveles"></a>
## 2. Tres niveles, de lo gratis a lo caro

| Nivel | Qué corre | Cuándo | Costo |
|---|---|---|---|
| **Sin LLM** | Tests del **código de los evals**: chequeos, regex, kappa, Rogan-Gladen | Cada commit | Gratis, segundos |
| **Con LLM y caché** | Casos críticos y umbrales sobre el set del Módulo 1 | Cada pull request | Solo lo que cambió |
| **Nocturno, sin caché** | Lo mismo, sin caché y con repeticiones | Cada noche | El eval completo |

El primer nivel sorprende: **los evals también tienen bugs**. Un chequeo mal escrito da resultados falsos con total
seguridad, y nadie lo nota porque el número "sale bien".
[`tests/test_chequeos.py`](tests/test_chequeos.py) fija las decisiones de los módulos anteriores: que "net" no vale por
".net" (Módulo 1), que la regex de contacto marca "LinkedIn" y no marca "2016-2024" (Módulo 2), que el kappa de la
paradoja es negativo (Módulo 4), que Rogan-Gladen da 1/7 en el ejemplo del Módulo 5. Si alguien "arregla" un chequeo y
cambia su significado, estos tests avisan. Son 10 y corren en menos de un segundo; en una máquina limpia, con solo las
dependencias del workflow, tardan unos 6 segundos.

---

<a name="3-cache"></a>
## 3. La caché: pagar solo lo que cambió

`llm_cache()` ([`comun/ev_comun.py`](../comun/ev_comun.py)) guarda cada respuesta con una clave que incluye **el modelo,
el schema, el prompt y la entrada**. [`code/01_cache_y_linea_base.py`](code/01_cache_y_linea_base.py) lo muestra con el
eval del extractor:

| Corrida | Llamadas pagadas | Desde la caché | Tiempo |
|---|---|---|---|
| Primera | 30 | 0 | 10.2 s |
| Segunda, idéntica | **0** | 30 | **0.1 s** |
| Con una palabra cambiada en el prompt ("No inventes nada.") | 30 | 0 | 9.1 s |

Que cambiar el prompt invalide la caché es la propiedad que importa: **la caché nunca esconde un cambio**. Lo que sí
esconde es la **variación entre corridas**: con caché, la segunda corrida es idéntica a la primera por construcción. Por
eso el pull request usa caché (¿rompió algo mi cambio?) y la corrida nocturna no (¿cuánto varía el sistema?).

---

<a name="4-base"></a>
## 4. La línea base

Un test de eval no compara con un número mágico ("la exactitud debe ser ≥ 90 %"), sino con **lo que el sistema hacía
antes del cambio**: la línea base. El laboratorio 01 la guarda en [`linea_base.json`](linea_base.json), con el modelo,
la versión del prompt y la fecha. Con `gpt-6-luna` y el prompt `v1` es 100 % en los cuatro campos (el set del Módulo 1
no le encuentra fallos).

La línea base se **actualiza a propósito**, nunca sola: cuando un cambio mejora el sistema y se acepta, se fija la
nueva (`ACTUALIZAR_LINEA_BASE = True`). Si se actualizara en cada corrida, una degradación lenta (un punto por semana)
nunca fallaría.

---

<a name="5-tests"></a>
## 5. Dos tipos de test: críticos y umbrales

[`tests/test_extractor.py`](tests/test_extractor.py) tiene dos clases de test, con reglas distintas:

- **Críticos:** casos que no pueden fallar **nunca**. La inyección (#22: 3 años, no 30), el correo que el candidato
  dice no usar (#24), el CV sin correo (#16), las prácticas que no cuentan como experiencia (#25). Un fallo bloquea el
  cambio, sin estadística: un sistema que obedece una inyección una vez de cada cien no está bien "en promedio".
- **Umbral:** la exactitud de cada campo sobre los 30 casos no puede bajar de la línea base **menos una tolerancia**
  del 7 % (unos 2 casos). La tolerancia existe porque, con 30 casos, uno solo son 3 puntos, y el ruido no es una
  regresión.

Los tests que llaman al modelo llevan la marca `llm`: `pytest -m "not llm"` corre solo los gratis, y sin
`OPENAI_API_KEY` se saltan en vez de fallar. [`code/02_correr_la_suite.py`](code/02_correr_la_suite.py) corre las dos
cosas: 10 tests sin LLM en 0.9 s, y los 15 en 0.04 s con la caché llena.

---

<a name="6-decidir"></a>
## 6. ¿Empeoró, o es ruido?

Para comparar dos versiones de forma justa, se corren **sobre los mismos casos** y se miran solo los casos
**discordantes**: los arreglados (fallaba y ya no) y los rotos (acertaba y ya no). Los casos en que las dos aciertan o
las dos fallan no dicen nada sobre la diferencia. La **prueba exacta de McNemar** responde: si romper y arreglar fueran
igual de probables, ¿qué tan raro sería ver tantos rotos?

[`code/03_decidir_contra_la_linea_base.py`](code/03_decidir_contra_la_linea_base.py) aplica la regla al cambio del
Módulo 1 (v1 → v2 con el modelo barato), sin caché y con tres corridas por versión (un caso cuenta como bien solo si
sale bien en las tres):

| | Resultado |
|---|---|
| Casos perfectos | v1: 28 · v2: 28 |
| Arreglados | #19 (hasta hoy), #23 (mayúsculas) |
| Rotos | **#18 (rangos solapados)**, #28 (tabla aplanada) |
| McNemar | p = 0.688 |
| Decisión | **PASAR, pero lee los rotos** |

El #18 se rompe otra vez, como en los Módulos 1 y 3: tres módulos, tres métodos, la misma rotura. La regla no bloquea,
porque dos arreglados y dos rotos no son evidencia de que v2 sea peor. Pero sí obliga a leerlos.

Y la regla tiene un límite que hay que conocer: con 30 casos, McNemar necesita mucho para bloquear.

| Arreglados | Rotos | p |
|---|---|---|
| 1 | 3 | 0.312 |
| 0 | 4 | 0.062 (no bloquea) |
| 0 | 5 | **0.031** (bloquea) |
| 2 | 8 | 0.055 (no bloquea) |

Cuatro roturas sin ningún arreglo pasarían. Por eso la regla tiene tres partes y no una: **los casos críticos
bloquean siempre**, la estadística bloquea las degradaciones grandes, y todo lo demás pasa **con aviso** para que una
persona lea los rotos. Un CI de evals con 30 casos es una red con agujeros grandes: atrapa las regresiones fuertes y
lo explícitamente prohibido, no las sutiles.

---

<a name="7-workflow"></a>
## 7. El workflow

[`ci/evals.yml`](ci/evals.yml) es un workflow de GitHub Actions con los tres niveles. **No está activo**: para
activarlo, cópialo a `.github/workflows/evals.yml` en la raíz del repositorio y crea el secreto `OPENAI_API_KEY`.

- `sin-llm`: en cada push y pull request. Instala solo lo mínimo (sin torch ni sentence-transformers) y corre
  `pytest -m "not llm"`.
- `con-llm`: en cada pull request y cada noche, después de `sin-llm`. Guarda la caché entre ejecuciones con
  `actions/cache`, así que un pull request solo paga las llamadas que cambiaron.
- En la ejecución nocturna, la caché se desactiva (`EVALS_CACHE=0`) para medir la variación real.

Tres cuidados de producción: **fija la versión del modelo** en el workflow (un alias que cambia por debajo rompe la
comparación con la línea base); **pon un tope de gasto** (en el proveedor, no en el código); y **nunca imprimas el
secreto** en los logs.

---

## Resumen del módulo

- Un eval que nadie corre no existe: conviértelo en **tests que corren solos**.
- **Tres niveles**: sin LLM en cada commit, con caché en cada pull request, sin caché cada noche.
- **Los evals tienen bugs**: testea el código de los chequeos (10 tests, menos de un segundo).
- Una **caché** con el prompt en la clave: 30 llamadas → 0; un cambio de prompt → 30 otra vez. Nunca esconde un
  cambio; sí esconde la variación.
- Compara contra una **línea base** que se actualiza a propósito.
- **Críticos** (bloquean siempre) y **umbrales** (con tolerancia).
- Decide con los **discordantes** y **McNemar**: v2 arregló 2 y rompió 2 (p = 0.69) → pasar y leer. Con 30 casos, 4
  roturas sin arreglos no bloquean: la red tiene agujeros.

Sigue con [`ejercicios.md`](ejercicios.md).
