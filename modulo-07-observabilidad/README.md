# Módulo 7 · Observabilidad

> **Objetivo:** ver lo que pasa dentro de tu sistema con LLMs y medir si funciona. Trazas paso a paso, tokens y
> costo real de cada llamada, métricas de latencia y error, datasets de evaluación, un LLM como juez **calibrado**
> contra personas, y pruebas de regresión que atrapen un prompt roto antes de que llegue a producción.
>
> **Pieza del proyecto:** el buscador de CVs queda instrumentado. Cada pedido deja una traza con su costo, y cada
> cambio de prompt o de modelo se valida contra un dataset antes de darlo por bueno.

Índice:

1. [Por qué los sistemas con LLM necesitan observabilidad](#1-por-que)
2. [Trazas, spans y atributos](#2-trazas)
3. [Qué registrar en cada llamada (y qué no)](#3-que-registrar)
4. [Tokens y costo: la factura real](#4-costo)
5. [Métricas operativas: latencia, errores, llamadas por pedido](#5-metricas)
6. [Evaluar: offline y online](#6-evaluar)
7. [Datasets de evaluación](#7-datasets)
8. [Primero, métricas deterministas](#8-deterministas)
9. [LLM como juez, y cómo no fiarse de él a ciegas](#9-juez)
10. [Pruebas de regresión de prompts](#10-regresion)
11. [En producción: feedback, muestreo y alertas](#11-produccion)
12. [Herramientas del mercado](#12-herramientas)
13. [Proyecto del módulo](#13-proyecto)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-por-que"></a>
## 1. Por qué los sistemas con LLM necesitan observabilidad

Un sistema tradicional que falla suele hacer ruido: una excepción, un 500, un test en rojo. Un sistema con LLMs
**falla en silencio**. Responde algo plausible, con buen formato, que pasa todas las validaciones de tipo, y está
mal. A lo largo de este curso lo viste varias veces:

- En el Módulo 6, el grafo invitó a entrevista a una Product Manager para una vacante de líder técnico de datos.
  Nada falló: cada nodo hizo su trabajo y devolvió algo válido.
- En el mismo módulo, el mismo CV recibió 5/5 en una ejecución y 1/5 en otra. Sin la traza de puntajes nadie lo
  habría visto: solo una invitación equivocada de vez en cuando.
- En el Módulo 4, la búsqueda híbrida empató con la semántica. Solo lo supimos porque lo medimos.

Además, el comportamiento **cambia sin que toques tu código**: el proveedor actualiza el modelo, los usuarios empiezan
a preguntar distinto, los documentos nuevos tienen otro formato. Y el costo depende de cuántos tokens genera el
modelo en cada llamada, que no controlas del todo.

La observabilidad responde a tres preguntas en todo momento: **qué hizo el sistema** (trazas), **cuánto costó y
cuánto tardó** (métricas) y **si lo hizo bien** (evaluaciones).

---

<a name="2-trazas"></a>
## 2. Trazas, spans y atributos

El modelo de datos estándar (el de **OpenTelemetry**, que usan casi todas las herramientas) tiene tres piezas:

- **Traza:** todo lo que pasó para atender **un** pedido, con un identificador único (`trace_id`).
- **Span:** una operación dentro de la traza (buscar, evaluar un CV, llamar al LLM), con inicio, fin, estado (ok o
  error) y un `parent_id` que lo cuelga de la operación que lo contiene. Los spans forman un **árbol**.
- **Atributos:** pares clave-valor en cada span: modelo, tokens, número de resultados, versión del prompt.

Una traza real del laboratorio (`gpt-6-luna`, primer pedido tras arrancar):

```
pedido                  21.6 s
├─ buscar                  12.0 s
├─ evaluar Marta            3.7 s  llm · 181 entrada · 60 salida (0 razonamiento)
├─ evaluar Andrés           2.2 s  llm · 175 entrada · 125 salida (64 razonamiento)
├─ evaluar Laura            1.7 s  llm · 189 entrada · 102 salida (32 razonamiento)
└─ redactar                 2.0 s  llm · 78 entrada · 55 salida (0 razonamiento)
```

Con eso puedes contestar preguntas concretas: ¿qué paso es el lento?, ¿cuánto costó este pedido?, ¿qué vio el
modelo cuando dio 1/5 a Laura? Esta traza ya cuenta una historia: `buscar` tardó 12 s, más que todas las llamadas
al modelo juntas. Es **arranque en frío** (cargar el modelo de embeddings y construir el índice); en el segundo
pedido, `buscar` tardó 0.2 s. Sin la traza habrías culpado al LLM. El laboratorio construye un trazador de este tipo en 100 líneas, sobre SQLite y sin
servicios externos ([`code/00_trazador.py`](code/00_trazador.py)), para que veas que no hay magia.

Para propagar el span padre sin pasarlo como argumento por todo el código se usa `contextvars`: cada `with span(...)`
deja su id en una variable de contexto y los spans que se abren dentro la leen. Así funcionan también las librerías
reales.

---

<a name="3-que-registrar"></a>
## 3. Qué registrar en cada llamada (y qué no)

En cada llamada al LLM, como mínimo:

| Atributo | Para qué |
|---|---|
| modelo (el que **respondió**, no el que pediste) | El alias puede apuntar a otra versión sin aviso |
| versión del prompt | Saber qué prompt produjo cada resultado al comparar |
| tokens de entrada, salida, razonamiento y en caché | Costo y diagnóstico (§4) |
| latencia | Detectar lentitud y su causa |
| reintentos y errores | Un 3 % de reintentos de validación es un problema de prompt |
| salida (o un resumen) | Depurar sin volver a ejecutar |

**Y lo que no:** los CVs tienen datos personales (nombre, correo, teléfono, historia laboral). Una traza que guarda
prompts completos es una **copia de esos datos** en otro sistema, a menudo con menos control de acceso que la base
de datos original. Decide a conciencia: guardar ids en lugar de textos, truncar, enmascarar correos y teléfonos, y
definir cuánto tiempo se conservan las trazas. El trazador del laboratorio **enmascara correos y teléfonos y trunca
los textos largos** por defecto.

---

<a name="4-costo"></a>
## 4. Tokens y costo: la factura real

```
costo = tokens_entrada × precio_entrada + tokens_salida × precio_salida
        (los tokens en caché se cobran más barato; los de razonamiento, como salida)
```

Tres cosas que no se ven sin medir:

- **Los tokens de razonamiento.** Los modelos de razonamiento (como `gpt-6-luna`) "piensan" antes de responder.
  Esos tokens no aparecen en la respuesta, pero se cobran **como tokens de salida**. Una respuesta de 20 tokens
  puede costar 80. El laboratorio mide qué proporción de tu salida es razonamiento.
- **El historial que se reenvía.** En un agente (Módulo 5) cada paso reenvía todo el historial: el paso 6 paga de
  nuevo la entrada de los pasos 1-5. El costo de un agente crece más rápido que su número de pasos.
- **La caché del proveedor.** Los prefijos repetidos (instrucciones, schemas) pueden cobrarse más barato si el
  proveedor los cachea. El campo `cached_tokens` te dice si está pasando.

Lo que midió el laboratorio con `gpt-6-luna`: el **50 % de los tokens de salida fueron razonamiento** (31 % en las
evaluaciones de candidatos, 14 % en redactar invitaciones). Y el pedido que **falló** por validación, tras 3
intentos, generó **426 tokens de salida (87 % razonamiento)**, más que un pedido exitoso completo de 4 llamadas
(342). Los fallos no son gratis: suelen ser lo más caro.

Los precios cambian y dependen de tu cuenta, así que el laboratorio **no** los inventa: cuenta tokens siempre, y
calcula dinero solo si defines `PRECIO_ENTRADA_USD_1M`, `PRECIO_SALIDA_USD_1M` y `PRECIO_CACHE_USD_1M` en
`app/backend/.env` con los valores de la página de precios de tu proveedor.

---

<a name="5-metricas"></a>
## 5. Métricas operativas: latencia, errores, llamadas por pedido

De las trazas salen las métricas que vigilas en el día a día:

- **Latencia en percentiles, no en promedio.** Si 9 pedidos tardan 2 s y uno tarda 40 s, el promedio (5.8 s) no
  describe a ninguno. Mira **p50** (lo típico), **p95** y **p99** (lo que sufren los usuarios con peor suerte). En
  sistemas con LLM la cola es larga: reintentos, respuestas con mucho razonamiento, límites de tasa.
- **Tasa de error**, separando tipos: errores del proveedor (red, 429, 5xx), errores de validación (Pydantic que no
  pasa ni reintentando) y errores de tu código.
- **Llamadas y tokens por pedido.** Si la media de llamadas por pedido de tu agente pasa de 3 a 7, algo cambió: el
  modelo, las consultas o una herramienta que empezó a fallar.
- **Costo por pedido** y su proyección a tu volumen.

Ejemplo sobre las trazas reales del laboratorio: [`code/02_metricas_y_costo.py`](code/02_metricas_y_costo.py).

---

<a name="6-evaluar"></a>
## 6. Evaluar: offline y online

Las trazas dicen **qué** pasó; las evaluaciones dicen **si estuvo bien**. Hay dos momentos:

- **Offline (antes de desplegar):** corres el sistema contra un **dataset** con respuestas esperadas y calculas
  métricas. Es lo que haces al cambiar un prompt, un modelo, el chunking o el tokenizador. Es repetible y comparable.
- **Online (en producción):** evalúas una muestra del tráfico real, con jueces automáticos, feedback de usuarios o
  revisión humana. Detecta lo que tu dataset no anticipó.

Ninguno sustituye al otro. El offline te da confianza para cambiar; el online te dice si el mundo cambió.

---

<a name="7-datasets"></a>
## 7. Datasets de evaluación

Un dataset de evaluación es una lista de casos `(entrada, lo que se espera)`. Es la inversión más rentable del
proyecto, y la más aburrida de hacer. Cómo construirlo bien:

- **Empieza pequeño y real:** 20-50 casos sacados de pedidos reales (o muy realistas) valen más que 500 inventados.
- **Incluye los casos difíciles a propósito:** CVs sin correo, con fechas incoherentes, con inyección, en otro
  formato. Los fáciles aciertan siempre y no enseñan nada.
- **Cada error encontrado se convierte en un caso.** El 1/5 a Laura del Módulo 6 ya es un caso de prueba en este
  módulo: no puede volver a pasar sin que se note.
- **Versiónalo** junto al código. Si el dataset cambia, los números dejan de ser comparables con los anteriores.
- **Lo esperado debe ser verificable:** "correo = laura@x.com" se comprueba; "un buen resumen" no. Si no puedes
  escribir qué esperas, aún no sabes qué estás evaluando.
- **Desconfía del 100 %.** En el laboratorio, los 10 casos de extracción salieron perfectos con `gpt-6-luna`
  (incluido "desde 2018 hasta hoy", que un modelo con fecha de corte anterior fallaría). Eso no prueba que el error
  sea cero: por la **regla del tres**, con 0 fallos en `n` casos la tasa de error real puede llegar a `3/n` con 95 %
  de confianza, es decir, ~30 % con 10 casos y ~6 % con 50. Un dataset que siempre sale perfecto ha dejado de
  enseñarte algo: añade casos más difíciles.

---

<a name="8-deterministas"></a>
## 8. Primero, métricas deterministas

Antes de pensar en un LLM como juez, mide todo lo que se pueda medir con código: es gratis, rápido, estable y no se
equivoca.

- **Extracción (Módulo 1):** exactitud por campo (¿el correo extraído es el esperado?), campos nulos cuando debían
  serlo, porcentaje de casos que pasan la validación sin reintentos.
- **Recuperación (Módulos 2-4):** `recall@k`, `MRR`.
- **Clasificación y enrutamiento (Módulo 5):** exactitud y matriz de confusión.
- **Restricciones de formato:** longitud, campos obligatorios, palabras prohibidas.

La exactitud **por campo** importa más que la global: "87 % de exactitud" esconde que el campo `anios_experiencia`
falla en la mitad de los casos. Ejemplo: [`code/03_dataset_extraccion.py`](code/03_dataset_extraccion.py).

---

<a name="9-juez"></a>
## 9. LLM como juez, y cómo no fiarse de él a ciegas

Para lo que no se puede medir con código (¿la respuesta del RAG está respaldada por el contexto?, ¿el mensaje es
adecuado?) se usa otro LLM como evaluador. Funciona, con condiciones:

- **Rúbrica concreta y salida estructurada.** "¿Cada afirmación de la respuesta aparece en el contexto? Lista las
  que no." en vez de "puntúa del 1 al 10 la calidad". Pide el razonamiento **antes** del veredicto (Módulo 1 §9).
- **Calíbralo contra personas.** Etiqueta a mano 20-50 casos, pasa el juez y mide el **acuerdo**: ¿en qué
  porcentaje coincide contigo? Mira sobre todo los **falsos aprobados**, que son los que dejan pasar errores. Un juez
  sin calibrar es una opinión con formato.
- **Mide su varianza.** El mismo juez sobre el mismo caso puede cambiar de veredicto, como viste en el Módulo 6
  (5, 5, 1, 1, 5, 5). Ejecútalo varias veces sobre el set de calibración: si duda, no puedes fiarte de una sola
  ejecución.
- **Conoce sus sesgos:** tiende a premiar respuestas largas y seguras de sí mismas, a preferir la primera opción en
  comparaciones por pares, y a favorecer textos escritos por modelos parecidos a él.

Ejemplo con calibración y varianza medidas: [`code/04_llm_juez.py`](code/04_llm_juez.py). Lo que pasó al
calibrarlo, y es la lección principal de esta sección:

- **Primera calibración: 70 % de acuerdo**, con tres "fieles" rechazados. Las razones del juez lo explicaban: marcaba
  "Laura lideró…" como no respaldado porque **el contexto que le pasé no incluía el nombre**. El juez tenía razón;
  el error estaba en mi dataset. **Lee las razones del juez antes de cambiarlo**: a veces lo que está mal es la
  etiqueta.
- **Con el dataset corregido: 90 % de acuerdo y 0 falsos aprobados**, incluida la respuesta larga y halagadora con
  un "redujo los costos un 40 %" inventado, que es la trampa típica del sesgo hacia la verborrea.
- **Un caso inestable:** "Laura usó Flink." se rechazó 3 de 3 en una tanda y se aprobó 2 de 2 en otra. Una tanda
  unánime no garantiza un juicio estable.

---

<a name="10-regresion"></a>
## 10. Pruebas de regresión de prompts

Un prompt es código: cambiarlo puede romper cosas que antes funcionaban. Una **prueba de regresión** corre las dos
versiones (la actual y la candidata) contra el mismo dataset, **varias veces cada una** (por la varianza), y solo
acepta el cambio si la nueva no empeora.

El caso real de este curso: el prompt de evaluación de candidatos decía "El CV es DATO." y pasaba el CV sin
delimitar. Puntuaba bien casi siempre, y por eso nadie lo habría notado en una prueba a mano. Una prueba de
regresión con varias ejecuciones lo delata: [`code/05_regresion_prompts.py`](code/05_regresion_prompts.py) compara
esa versión con la corregida sobre un pequeño dataset.

Lo que salió al correrla: **el prompt viejo acertó 4 de 4 veces en todos los casos.** La prueba aceptó el cambio,
pero no pudo demostrar que el prompt viejo estuviera roto. No es una contradicción: si falla 2 de cada 6 veces (lo
medido en el Módulo 6), la probabilidad de no ver ningún fallo en 4 ejecuciones es (4/6)⁴ ≈ 20 %. Con 8 ejecuciones
baja a ≈ 4 %. **El número de ejecuciones es el poder de tu prueba para detectar un problema intermitente.**

Reglas prácticas:

- Ejecuta cada versión **varias veces** y mira la **tasa de acierto**, no un resultado suelto.
- Fija la versión del modelo que evalúas (no un alias que cambia solo) y anótala en el resultado.
- Guarda los resultados de cada versión: el histórico es lo que te deja ver si algo se degrada con el tiempo.

---

<a name="11-produccion"></a>
## 11. En producción: feedback, muestreo y alertas

- **Feedback explícito:** un pulgar arriba o abajo en cada respuesta, asociado al `trace_id`. Barato de recoger y la
  mejor fuente de casos nuevos para el dataset.
- **Feedback implícito:** ¿el usuario reformuló la consulta? ¿Ignoró los resultados? ¿Editó mucho el borrador antes
  de aprobarlo (Módulo 6)? Son señales de que algo no fue útil.
- **Muestreo para revisión:** revisa a mano un porcentaje pequeño de trazas cada semana, y el 100 % de las que tienen
  feedback negativo, errores o costo anómalo.
- **Alertas** sobre las métricas de §5: p95 de latencia, tasa de error, costo diario, llamadas por pedido. Una alerta
  que suena todos los días se ignora; empieza con pocas y con umbrales holgados.

---

<a name="12-herramientas"></a>
## 12. Herramientas del mercado

El trazador del laboratorio sirve para aprender y para proyectos pequeños. Cuando el sistema crece, conviene una
herramienta dedicada. Las más usadas:

- **Langfuse:** de código abierto, se puede instalar en tu propia infraestructura (importante con datos personales).
  Trazas, costos, datasets, evaluaciones y gestión de prompts.
- **LangSmith:** de los creadores de LangChain y LangGraph, muy integrado con ellos. Servicio en la nube.
- **Arize Phoenix:** de código abierto, fuerte en evaluación, basado en OpenTelemetry.
- **OpenTelemetry:** el estándar abierto de trazas. Tiene convenciones específicas para IA generativa (nombres de
  atributos como `gen_ai.request.model` o `gen_ai.usage.input_tokens`). Si instrumentas con él, puedes cambiar de
  herramienta sin reescribir el código.

Criterios para elegir: dónde quedan los datos (los CVs son datos personales), costo, si se integra con tu framework y
si soporta evaluaciones además de trazas. Los conceptos son los de este módulo; las herramientas cambian.

---

<a name="13-proyecto"></a>
## 13. Proyecto del módulo

Entregable: **el buscador de CVs instrumentado y con red de seguridad.**

1. **Trazas:** cada pedido (buscar → evaluar → responder) deja una traza con spans anidados, tokens y latencia, con
   los datos personales enmascarados.
2. **Informe operativo:** p50 y p95 de latencia por tipo de span, tasa de error, llamadas y tokens por pedido,
   proporción de tokens de razonamiento, y costo por pedido si configuraste los precios.
3. **Dataset de extracción** de al menos 15 CVs con valores esperados, y exactitud por campo.
4. **Juez de fidelidad** para las respuestas del RAG (Módulo 3), calibrado contra 15 casos etiquetados por ti, con el
   porcentaje de acuerdo y de falsos aprobados.
5. **Prueba de regresión** que se ejecute con un comando, compare dos versiones de prompt y diga si se acepta el
   cambio.

Criterios de la rúbrica:

- Puedes reconstruir lo que pasó en un pedido concreto solo con su traza.
- Sabes cuánto cuesta (en tokens, y en dinero si tienes los precios) un pedido típico y uno caro.
- El juez está calibrado y conoces su tasa de falsos aprobados.
- Un cambio de prompt que empeora el sistema **no pasa** la prueba de regresión.

En el **Módulo 8** cerramos el curso con **memoria y guardrails**: que el asistente recuerde lo relevante entre
conversaciones y que tenga defensas de entrada y salida medibles con todo lo que construiste aquí.

---

## Resumen del módulo (lo que no puedes olvidar)

- Los sistemas con LLM **fallan en silencio**: sin trazas ni evaluaciones, no te enteras.
- **Traza = árbol de spans** con atributos. Registra modelo, tokens, latencia, errores y versión del prompt; protege
  los datos personales.
- Los **tokens de razonamiento** se cobran como salida aunque no los veas.
- Mide la **latencia en percentiles** (p50, p95), no en promedio.
- **Datasets** pequeños, reales y con casos difíciles; cada error encontrado se convierte en un caso.
- **Primero métricas deterministas**; el **LLM juez** solo después, **calibrado** contra personas y con su varianza
  medida.
- Cada cambio de prompt o de modelo pasa una **prueba de regresión** con varias ejecuciones.

Sigue con [`ejercicios.md`](ejercicios.md).
