# Módulo 1 · El primer eval en una tarde

> **Objetivo:** construir un eval completo, de los casos a la decisión, para responder una pregunta concreta: **¿puedo
> pasar el extractor a un modelo más barato sin perder calidad?**
>
> **Lo que te llevas:** un eval de 30 casos con chequeos por código, resultados versionados y una comparación caso por
> caso entre dos versiones del sistema.

Índice:

1. [La pregunta](#1-pregunta)
2. [Anatomía del eval](#2-anatomia)
3. [Qué chequear, y con cuánta tolerancia](#3-chequeos)
4. [La primera corrida](#4-corrida)
5. [Leer cada fallo](#5-leer)
6. [Una segunda versión, guiada por los fallos](#6-v2)
7. [Comparar caso por caso, no por promedio](#7-comparar)
8. [La decisión, y cuánto vale](#8-decision)
9. [Lo que este eval no ve](#9-no-ve)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-pregunta"></a>
## 1. La pregunta

El extractor corre con el modelo de tu `.env` (`gpt-6-luna` al escribir esto), un modelo de razonamiento capaz y
caro. Procesar 100.000 CVs con él cuesta, y tarda. Alguien propone un modelo pequeño. La discusión sin eval suena así:
"yo lo probé con tres CVs y anda igual" contra "los modelos pequeños alucinan". Con eval, la discusión es otra:
**en estos 30 casos, en estos campos, falla en estos y no en estos.**

Un buen primer eval empieza por una pregunta así: concreta, con una decisión detrás. "Evaluar el sistema" no es una
pregunta.

---

<a name="2-anatomia"></a>
## 2. Anatomía del eval

[`code/01_primer_eval.py`](code/01_primer_eval.py) tiene las cinco piezas del Módulo 0 en unas 50 líneas:

```python
def uno(cv):
    ficha = ev.extraer(cv["texto"], version, modelo)               # el sistema
    return {"id": cv["id"], "tipo": cv["tipo"], "version": version, "modelo": modelo,
            "esperado": cv["esperado"], "obtenido": ficha.model_dump(),
            "ok": ev.comparar_ficha(ficha, cv["esperado"])}        # el chequeo, un booleano por campo
```

- **Casos y lo esperado:** los 30 CVs de [`comun/ev_datos.py`](../comun/ev_datos.py).
- **Chequeo:** `comparar_ficha()`, un booleano por campo, solo con código.
- **Agregación:** exactitud por campo, casos perfectos y fallos por tipo.
- **Registro:** cada fila se guarda en `salida/extractor_v1.jsonl` con versión y modelo. Guardar lo **obtenido**, no
  solo el sí o no, es lo que te deja releer un fallo semanas después sin volver a pagar la llamada.

Todo se ejecuta dentro de una traza del trazador del Módulo 7 de AI Engineering, así que cada corrida deja tokens y
latencia por llamada.

---

<a name="3-chequeos"></a>
## 3. Qué chequear, y con cuánta tolerancia

Cada campo necesita una decisión explícita sobre qué cuenta como acierto:

| Campo | Chequeo | Por qué |
|---|---|---|
| `nombre` | Igual tras normalizar (minúsculas, sin tildes, espacios) | "MARÍA JOSÉ PEÑA" y "María José Peña" son el mismo dato |
| `correo` | Igual tras normalizar; `None` si no hay | Un correo equivocado es peor que ninguno |
| `anios` | Igualdad exacta | 7 y 9 no son "parecidos" para un filtro de "más de 8 años" |
| `skills` | Cada skill esperada aparece **dentro** de alguna extraída | "python" vale dentro de "python 3.12"; extraer de más no se castiga |

Las tolerancias son decisiones de producto, no detalles técnicos. Un chequeo demasiado estricto llena el informe de
falsos fallos ("Python 3.12" ≠ "python") y acabas ignorándolo. Uno demasiado laxo deja pasar errores reales. El
laboratorio mostró un caso en la frontera: el §5.

---

<a name="4-corrida"></a>
## 4. La primera corrida

Cuatro modelos, prompt `v1`, dos pasadas cada uno, sobre los 30 casos:

| Modelo | Casos perfectos (pasada 1 / 2) | Casos que fallan |
|---|---|---|
| `gpt-6-luna` (el actual) | 30 / 30 | ninguno |
| `gpt-4.1-mini` | 28 / 28 | #4 (`.net`), #19 (hasta la fecha) |
| `gpt-5.4-nano` | 27 / 28 | #19, #23 (mayúsculas) y, en una pasada, #18 (rangos solapados) |
| `gpt-4o-mini` | 28 / 28 | #19, #30 (experiencia mixta) |
| `gpt-4.1-nano` | no disponible | el 22 de octubre de 2026 respondía; el 26 devolvía *404: deprecated* |

Cuatro lecciones antes de leer un solo fallo:

1. **Un eval perfecto no informa.** `gpt-6-luna` sacó 30/30 dos veces. No significa que no falle: significa que este
   set no encuentra sus fallos. Para el modelo actual hace falta un set más difícil (Módulos 2 y 3).
2. **Los modelos baratos fallan en casos distintos.** Una exactitud global parecida (93-97 % por campo) esconde
   fallos que no se parecen entre sí, y que piden arreglos distintos.
3. **Casi todos los fallos se repiten en las dos pasadas.** Eso los hace **sistemáticos**: no es mala suerte, es algo
   que el modelo hace así. Lo ocasional (el #18 de `nano`, una vez de dos) se trata distinto (§7).
4. **Los modelos se retiran.** Un eval que nombra un modelo tiene fecha de caducidad. Fija versiones
   (`gpt-4.1-mini-2025-04-14`) y vuelve a correrlo cuando el proveedor cambie algo.

---

<a name="5-leer"></a>
## 5. Leer cada fallo

El número no dice qué arreglar. Lo dice la fila:

| Caso | Modelo | Esperado | Obtenido | Qué pasa |
|---|---|---|---|---|
| #19 "desde 2019 hasta la fecha" | los tres baratos | 7 | 4 o 5 | El modelo no sabe qué año es: cuenta hasta su fecha de corte de entrenamiento |
| #30 mesero 2012-2015, frontend 2015-2023 | `gpt-4o-mini` | 11 | 8 | Solo cuenta la experiencia del área. Es una interpretación razonable: **el prompt nunca dijo qué cuenta** |
| #23 CV en mayúsculas | `gpt-5.4-nano` | `['sas', 'r']` | `[]` | No reconoce "SAS, R." en mayúsculas como tecnologías |
| #4 "C#, .NET y SQL Server" | `gpt-4.1-mini` | `.net` | `net` | Quitó el punto |

El #4 es la pregunta más importante del módulo: **¿falló el sistema o falló el chequeo?** El chequeo busca `.net`
dentro de las skills y encuentra `net`. Se podría relajar. Pero para un buscador de CVs, "net" es ambiguo (¿.NET?
¿redes?), así que es un dato peor. Se decidió mantener el chequeo y tratarlo como fallo. La regla: **relaja un
chequeo solo si lo obtenido es igual de útil que lo esperado**, no porque te moleste ver el fallo.

Y el #30 muestra algo que se repetirá todo el curso: muchas veces el fallo no es del modelo sino de **una regla que
existía en tu cabeza** (y en las etiquetas) y nunca llegó al prompt.

---

<a name="6-v2"></a>
## 6. Una segunda versión, guiada por los fallos

El prompt `v2` (en [`comun/ev_comun.py`](../comun/ev_comun.py)) añade exactamente lo que los fallos pidieron, ni más
ni menos:

- la fecha de hoy (para el #19);
- las reglas de conteo de años, que eran las reglas de las etiquetas (para el #30 y el #18);
- conservar la puntuación de las skills y leerlas aunque el CV esté en mayúsculas (para el #4 y el #23).

¿Es hacer trampa poner en el prompt las reglas de las etiquetas? No: esas reglas **son la especificación**. Lo que sí
sería trampa es escribir reglas para casos concretos del set ("si el CV dice Banco Andino, son 7 años"). El riesgo de
sobreajustarse al eval existe y tiene solución (un set de validación aparte, Módulo 11); por ahora, la defensa es que
cada regla de `v2` sea general.

---

<a name="7-comparar"></a>
## 7. Comparar caso por caso, no por promedio

[`code/02_comparar_versiones.py`](code/02_comparar_versiones.py) corre `v1` y `v2` dos veces cada uno y clasifica
**cada caso**:

| Clase | Significado | Qué haces |
|---|---|---|
| siempre bien | Bien en todas las pasadas de las dos versiones | Nada |
| **arreglado** | Mal siempre con v1, bien siempre con v2 | Es la mejora que buscabas |
| **roto** | Bien siempre con v1, mal siempre con v2 | Lo investigas antes de cambiar nada |
| inestable | Unas pasadas bien y otras mal | Necesita más pasadas para saber |
| siempre mal | Mal en todo | Sigue pendiente |

Resultado:

| Modelo | Perfectos v1 | Perfectos v2 | Arreglados | **Rotos** | Inestables | Siempre mal |
|---|---|---|---|---|---|---|
| `gpt-4.1-mini` | 29 / 28 | **30 / 30** | #19 | — | #4 | — |
| `gpt-4o-mini` | 27 / 28 | 29 / 29 | #19 | — | #4 | #30 |
| `gpt-5.4-nano` | 28 / 28 | 28 / 29 | #19, #23 | **#18** | #21 | — |

Tres cosas que un promedio nunca te habría dicho:

- **`v2` rompió un caso en `nano`.** Con `v1`, el caso de rangos solapados daba 7 en las cuatro llamadas que se
  hicieron para investigarlo. Con `v2`, que tiene justo la regla de los solapes, dio **7, 6, 10 y 12**. Más
  instrucciones no hicieron al modelo pequeño más preciso: lo **desestabilizaron**. La exactitud global de `nano`
  apenas cambió (28 → 28-29), y escondía un arreglo de dos casos y una rotura.
- **Una rotura puede esconderse en una pasada con suerte.** Al correr `02` otra vez, ya desde la app, el #18 salió
  bien en las dos pasadas de `v2` y el informe dijo "v2 no rompe nada". Para salir de dudas se midió solo ese caso,
  10 llamadas por versión: `v1` acertó **9 de 10**; `v2`, **3 de 10** (dio 8 cuatro veces y 9 tres). La rotura es
  real, pero no es "siempre mal": es una caída fuerte de la probabilidad de acertar, y con dos pasadas a veces no se
  ve. Cuando un caso importa, **mídelo solo y muchas veces**: es barato (una llamada por repetición) y responde la
  pregunta que el eval completo deja abierta.
- **Una regla escrita no es una regla obedecida.** `gpt-4o-mini` siguió dando 8 en el #30 en las cuatro llamadas,
  con "suma todo trabajo, aunque no sea del área" en el prompt. El ejercicio 4 prueba otra forma de decírselo.
- **"Inestable" no es "arreglado".** El #4 pasó de mal a bien en `gpt-4.1-mini`, pero con `v1` ya había salido bien
  una vez. Con dos pasadas no se puede distinguir una mejora de la suerte.

---

<a name="8-decision"></a>
## 8. La decisión, y cuánto vale

Con estos números, el candidato es **`gpt-4.1-mini` con `v2`**: 30/30 en dos pasadas, ningún caso roto. ¿Cuánto vale
esa afirmación? Son 60 extracciones sin fallos. La regla del tres (AI Engineering, Módulo 7) dice que, con 95 % de
confianza, la tasa real de casos con algún error está por debajo de 3/60 = **5 %**. No es "0 %": es "menos de 5 %
**en casos como estos**". Si te hace falta saber que es menos de 1 %, necesitas unos 300 casos sin fallos.

Antes de cambiar de modelo faltan dos cosas que el eval no mide todavía y que debes medir tú:

- **Costo y latencia.** Las trazas guardan los tokens de cada llamada; multiplica por el precio de tu cuenta (ejercicio
  5). Un modelo "barato" que razona mucho puede no serlo tanto.
- **Fijar la versión** del modelo elegido, y volver a correr el eval cuando cambie.

---

<a name="9-no-ve"></a>
## 9. Lo que este eval no ve

Este eval es útil y tiene límites claros, que son el índice del resto del curso:

- **Casos que no imaginaste.** Los 30 casos los escribió una persona. El Módulo 2 busca los fallos en salidas reales,
  y el Módulo 3 genera casos que no se te ocurrieron.
- **Etiquetas discutibles.** ¿El mesero cuenta? Lo decidimos nosotros. Otra persona podría etiquetar distinto, y
  entonces el "fallo" de `gpt-4o-mini` sería una diferencia de criterio. El Módulo 4 mide eso.
- **Tareas sin una respuesta única.** Comparar un correo es fácil; juzgar si una recomendación está bien justificada
  no lo es. Eso es el Módulo 5.

---

## Resumen del módulo

- Un primer eval empieza con **una pregunta y una decisión** detrás.
- Cinco piezas: **casos, lo esperado, chequeo, agregación, registro** (guarda lo obtenido, no solo el sí o no).
- Las **tolerancias** de cada chequeo son decisiones de producto: relaja solo si lo obtenido es igual de útil.
- **Un eval perfecto no informa**: hace falta un set que encuentre fallos.
- Lee cada fallo: muchos son **reglas que nunca llegaron al prompt**.
- Compara versiones **caso por caso**: arreglados, **rotos**, inestables. Un promedio igual puede esconder roturas.
- **Repite**: dos pasadas separan lo sistemático de lo ocasional; para "arreglado" hacen falta más. Un caso que
  importa se mide **solo y muchas veces** (en el #18: 9/10 con v1 contra 3/10 con v2).
- 0 fallos en n intentos acota la tasa por debajo de **3/n**, no la hace cero.

Sigue con [`ejercicios.md`](ejercicios.md).
