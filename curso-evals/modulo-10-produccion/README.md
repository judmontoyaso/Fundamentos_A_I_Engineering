# Módulo 10 · Evals y guardrails en producción

> **Objetivo:** medir el sistema cuando **ya no tienes la respuesta correcta**: chequeos sin referencia, alertas que
> distinguen un cambio real del ruido, y el mismo chequeo usado como guardrail que decide cuándo pagar un modelo más
> caro.
>
> **Lo que te llevas:** tres días de tráfico simulado con un cambio en la mezcla de entradas, la cobertura real de los
> chequeos sin referencia (medida contra etiquetas), una alerta estadística y una cascada barato → caro con su costo.

Índice:

1. [Lo que cambia en producción](#1-cambia)
2. [Chequeos sin referencia](#2-sin-referencia)
3. [Tres días de tráfico](#3-dias)
4. [¿Cuánto ven los chequeos?](#4-cobertura)
5. [Alertar sin perseguir ruido](#5-alertas)
6. [El chequeo como guardrail: la cascada](#6-cascada)
7. [Las otras señales de producción](#7-senales)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-cambia"></a>
## 1. Lo que cambia en producción

Todos los evals anteriores tenían algo que producción no tiene: **la respuesta correcta**. En producción llegan CVs que
nadie etiquetó, a un ritmo que nadie puede revisar. Y llegan entradas que tu set nunca tuvo: el día que el área de
selección empieza a recibir CVs de Brasil, la mezcla de entradas cambia (*drift*) y el sistema puede empeorar sin que
cambie una línea de código.

Las preguntas pasan a ser otras: ¿qué puedo comprobar **sin etiqueta**?, ¿cuándo un aumento de fallos es real?, y ¿qué
hago con una salida sospechosa **antes** de mostrarla?

---

<a name="2-sin-referencia"></a>
## 2. Chequeos sin referencia

Un chequeo **sin referencia** compara la salida con **la propia entrada**, no con una etiqueta. Para el extractor
([`code/01_monitoreo_sin_referencia.py`](code/01_monitoreo_sin_referencia.py)):

| Chequeo | Qué detecta | Ejemplo |
|---|---|---|
| Correo inventado | El correo extraído no aparece en el CV | Un correo "normalizado" que no existe |
| Nombre ausente | Alguna palabra del nombre no está en el CV | Un nombre corregido o inventado |
| **Años imposibles** | Más años que los que caben entre la primera y la última fecha del CV (o hasta hoy, si dice "actual") | 9 años con trabajos entre 2011 y 2016 |
| Skills vacías | No extrajo ninguna tecnología | El CV en mayúsculas del Módulo 1 |

No dicen si la salida es **correcta**: dicen si es **imposible** o **sospechosa**. Son gratis, instantáneos y se pueden
correr sobre el 100 % del tráfico.

---

<a name="3-dias"></a>
## 3. Tres días de tráfico

El laboratorio simula 25 CVs por día con el candidato barato (`gpt-5.4-nano`, prompt `v2`):

- **Días 1 y 2:** CVs como los del set del Módulo 1.
- **Día 3:** la mezcla cambia: 20 de los 25 son CVs sintéticos del Módulo 3 (portugués, tablas, rangos solapados,
  inyecciones).

Como los CVs vienen de sets etiquetados, aquí **sí** se conoce la tasa de error real. Es lo que permite responder la
pregunta que en producción no se puede responder: ¿cuánto de lo que falla ven los chequeos?

---

<a name="4-cobertura"></a>
## 4. ¿Cuánto ven los chequeos?

| Día | Alertas | Errores reales | Errores con alerta |
|---|---|---|---|
| 1 | 2 / 25 | 2 / 25 | 2 / 2 |
| 2 | 1 / 25 | 2 / 25 | 1 / 2 |
| 3 (drift) | **6 / 25** | **7 / 25** | 6 / 7 |

En total, **9 de los 11 errores reales tuvieron alerta, y no hubo ninguna falsa alarma.** Es una cobertura alta, y
tiene una explicación que hay que entender antes de generalizarla: el error dominante del modelo barato es **sumar
rangos que se solapan** (2011-2013 y 2012-2016 → 9 años en vez de 5), y eso da más años de los que caben entre las
fechas del CV. El error viola una invariante, así que un chequeo de imposibilidad lo atrapa. Y como el chequeo solo
marca lo imposible, no da falsas alarmas.

Los 2 errores que **no** se vieron son la otra cara: "12 años en vez de 13" y "10 en vez de 11". Son errores
**plausibles**: caben en las fechas. Ningún chequeo sin referencia distingue un 12 correcto de un 12 incorrecto. Es lo
que producción no te cuenta, y por eso los evals con etiquetas (nocturnos, sobre una muestra) siguen haciendo falta
aunque tengas monitoreo.

Regla: **la cobertura de un chequeo sin referencia depende del tipo de error**. Aquí fue alta porque el error típico
era imposible. En un sistema cuyos errores son plausibles (un resumen que omite algo, un nivel mal asignado), la
cobertura puede ser casi nula. Mídela una vez con datos etiquetados, como aquí, antes de confiar en el monitoreo.

---

<a name="5-alertas"></a>
## 5. Alertar sin perseguir ruido

Un día con 6 alertas en vez de 1 o 2, ¿es un cambio real? Con 25 CVs por día, la variación de un día a otro es grande.
El laboratorio usa la tasa de alertas de los días 1 y 2 (6 %) como referencia y calcula qué tan raro sería ver 6 o
más en 25 si la tasa no hubiera cambiado (cola de una binomial):

```
P(≥ 6 alertas de 25 | tasa del 6 %) = 0.003
```

Es muy improbable por azar: **la alerta está justificada**, y señala justo el día del drift. Con la misma regla, un día
con 3 alertas no la dispararía. Dos ideas que generalizan:

- **Alerta sobre tasas con su incertidumbre**, no sobre conteos crudos ("¡hoy hubo 3 alertas!").
- **Mira también las entradas**, no solo las salidas: el drift se ve antes en la mezcla (idioma, formato, longitud)
  que en los errores. Un aumento de CVs en portugués es una alerta útil aunque todavía no haya fallos.

---

<a name="6-cascada"></a>
## 6. El chequeo como guardrail: la cascada

El mismo chequeo que alerta puede **actuar** antes de mostrar la salida. [`code/02_cascada_con_guardrail.py`](code/02_cascada_con_guardrail.py)
compara tres políticas sobre los 75 CVs:

| Política | Errores reales (corrida 1 · 2) | Llamadas al modelo grande | Llamadas totales |
|---|---|---|---|
| Siempre el barato (`gpt-5.4-nano`) | 7 · 9 de 75 | 0 | 75 |
| **Cascada**: el barato, y el grande solo si salta un chequeo | **2 · 3** de 75 | **7 · 6** de 75 | 82 · 81 |
| Siempre el grande (`gpt-6-luna`) | 0 · 0 de 75 | 75 | 75 |

La cascada elimina cerca de dos tercios de los errores del modelo barato y paga el modelo grande en menos del 10 % de
los CVs. Los errores que quedan son exactamente los plausibles del §4: la cascada **no puede arreglar lo que el chequeo
no ve**. Si esos errores son aceptables para el producto, la cascada es casi tan buena como el modelo grande a una
fracción del costo. Si no lo son, el modelo grande siempre.

Esta es la conexión con el Módulo 8 de AI Engineering: **un guardrail es un eval que corre en línea y actúa**. Se mide
igual (cobertura, falsas alarmas, costo) y cada activación se registra, porque cada caso que saltó es un candidato a
entrar en el set de evaluación.

---

<a name="7-senales"></a>
## 7. Las otras señales de producción

Los chequeos sin referencia no son la única fuente:

- **Jueces sobre una muestra.** El juez calibrado del Módulo 5, sobre un 5-10 % del tráfico cada día, con la tasa
  corregida por Rogan-Gladen. Cuesta, así que se muestrea.
- **Señales del usuario.** Un reclutador que corrige el nivel extraído, descarta una recomendación o vuelve a
  preguntar lo mismo. Son ruidosas, pero gratis y numerosas.
- **Muestras para personas.** Las salidas con alerta, las que el usuario corrigió y una muestra aleatoria (para no ver
  solo lo que ya sospechabas) van a revisión humana, y lo que se etiqueta entra al set del Módulo 1. Así el set de
  evaluación crece con lo que de verdad llega.
- **Herramientas.** Langfuse, Phoenix o los paneles de los proveedores guardan trazas, corren evaluadores sobre
  muestras y permiten anotar. Lo que no hacen por ti es decidir qué chequear ni medir la cobertura de tus chequeos.

---

## Resumen del módulo

- En producción **no hay respuesta correcta**: usa chequeos **sin referencia** (salida contra entrada).
- Detectan lo **imposible**, no lo **plausible**: aquí vieron 9 de 11 errores con 0 falsas alarmas, porque el error
  típico violaba una invariante. **Mide su cobertura** una vez con datos etiquetados.
- El drift del día 3 subió las alertas a 6/25; con la tasa previa del 6 %, **p = 0.003**: alerta justificada.
- **Alerta sobre tasas con incertidumbre**, y vigila también la mezcla de entradas.
- El chequeo como **guardrail en cascada**: de 7-9 errores a 2-3, pagando el modelo grande en menos del 10 % de los
  casos. No arregla lo que no ve.
- Juez sobre muestras, señales del usuario y revisión humana completan el monitoreo, y **alimentan el set** de
  evaluación.

Sigue con [`ejercicios.md`](ejercicios.md).
