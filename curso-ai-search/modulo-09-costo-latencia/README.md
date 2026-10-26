# Módulo 9 · Que no se caiga y que no salga carísimo

> **Objetivo:** poner a cada pieza del buscador tres números (calidad, latencia y costo) y decidir con ellos qué
> pagar; y medir qué pasa cuando el LLM falla, en vez de descubrirlo en una caída.
>
> **Lo que te llevas:** la tabla calidad-latencia-tokens de cinco configuraciones, una política que paga el reranker
> solo donde compra, las fallas reales de tus trazas, y cinco estrategias contra una caída simulada (tiempo límite,
> reintentos, respaldo, presupuesto, cortacircuitos).

Índice:

1. [Tres números por pieza](#1-numeros)
2. [Lo que cuesta cada configuración](#2-tabla)
3. [Qué compra cada pieza](#3-compra)
4. [Pagar solo donde compra](#4-politica)
5. [Cachés](#5-caches)
6. [Cómo falla de verdad](#6-fallas)
7. [Una caída simulada](#7-caida)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-numeros"></a>
## 1. Tres números por pieza

Cada módulo añadió una pieza y midió su calidad. En producción cada pieza tiene además **latencia** (lo que espera el
reclutador) y **costo** (tokens que se pagan). Sin los tres, "el reranker mejora 2 puntos" es media frase: ¿a cambio de
cuántos segundos y cuántos tokens?

[`code/01_costo_y_latencia.py`](code/01_costo_y_latencia.py) mide cinco configuraciones:

| Configuración | Qué hace |
|---|---|
| base | híbrida del Módulo 1, sin LLM |
| parser nano | consulta entendida con el modelo barato + filtros suaves (Módulo 2) |
| parser principal | lo mismo con el modelo principal |
| nano + reranker | parser nano + reranker LLM sobre el top 20 (Módulo 4, modelo barato, 20 llamadas en paralelo) |
| principal + rerank | parser principal + el mismo reranker |

La calidad, en las 41 consultas con la caché. La latencia y los tokens, **en vivo y sin caché** sobre 8 consultas,
leídos de las trazas (curso de AI Engineering, Módulo 7): la observabilidad que montaste para depurar es la que mide el
costo. La medición en vivo tarda unos 3.5 minutos y se guarda; si la app corta el laboratorio a los 300 s, córrelo una
vez desde la terminal.

El costo en dinero depende de los precios de tu cuenta, que cambian. El laboratorio reporta **tokens**, que no
cambian, y los convierte a dólares si defines `PRECIO_<MODELO>="entrada,salida"` en `.env` (USD por millón de tokens).

---

<a name="2-tabla"></a>
## 2. Lo que cuesta cada configuración

| Configuración | nDCG@10 | Llamadas | p50 | p95 | Tokens entrada | Tokens salida (razonamiento) |
|---|---|---|---|---|---|---|
| base | 0.685 | 0 | 0.04 s | 0.13 s | 0 | 0 |
| **parser nano** | **0.891** | 1 | **1.3 s** | 2.0 s | 728 | 92 (0) |
| parser principal | 0.893 | 1 | 3.7 s | 6.4 s | 728 | 161 (71) |
| nano + reranker | 0.910 | 21 | 4.8 s | 5.9 s | 5.766 | 2.094 (0) |
| principal + rerank | 0.913 | 21 | 6.8 s | 8.3 s | 5.742 | 2.093 (55) |

Con 8 consultas, el p95 es casi el máximo. Las trazas tienen más datos del parser: en 352 llamadas, el modelo
principal tarda p50 3.6 s y p95 5.6 s; el barato, en 139, p50 1.2 s y p95 1.7 s. Coinciden con la tabla.

---

<a name="3-compra"></a>
## 3. Qué compra cada pieza

Leída como "cuánto pago por cada punto":

- **El parser es la mejor compra del curso**: +0.21 de nDCG por una llamada de ~800 tokens. Es lo primero que se paga.
- **El modelo principal no compra nada en el parser**: 0.893 contra 0.891, con el triple de latencia y casi el doble de
  tokens de salida (el modelo principal razona: 71 tokens de razonamiento que se pagan y no se ven). Para una tarea
  acotada, con salida estructurada y bien medida (Módulo 2), el modelo barato basta. **Se cambia el modelo cuando el
  eval dice que se puede**, no antes.
- **El reranker compra poco y cuesta mucho**: +0.02 por 20 llamadas, 8 veces los tokens y 3.5 s más de espera. Es el
  mismo resultado del Módulo 4 (sobre la búsqueda entendida el reranker casi no suma), ahora con su factura.

La latencia del reranker no es 20 veces la del parser porque las 20 llamadas van **en paralelo**: la latencia de un
pedido es la de su camino más lento, no la suma. El costo, en cambio, sí es la suma.

---

<a name="4-politica"></a>
## 4. Pagar solo donde compra

El reranker no ayuda igual a todas las consultas. Por tipo (nano + reranker contra parser nano):

| Tipo | Consultas | Ganancia del reranker |
|---|---|---|
| exclusión | 2 | **+0.26** |
| numérica | 3 | **+0.10** |
| rol + idioma, liderazgo, paráfrasis | 10 | +0.01 a +0.03 |
| tecnología, rol, nivel, certificación, abreviatura, en inglés | 23 | 0.00 |
| rol + ciudad | 3 | **−0.06** |

Gana donde los filtros suaves son débiles (exclusiones, rangos de años) y no hace nada, o estorba, en el resto. El tipo
es una etiqueta del conjunto de evaluación, que en producción no existe, pero **el parser ya dice lo mismo**: si la
consulta entendida trae `skills_excluidas` o un mínimo o máximo de años, se llama al reranker; si no, no.

| Política | nDCG@10 | Consultas con reranker | Llamadas al reranker por consulta |
|---|---|---|---|
| nunca | 0.891 | 0 / 41 | 0 |
| siempre | 0.910 | 41 / 41 | 20 |
| **si el parser ve exclusión o años** | **0.910** | 9 / 41 | **4.4** |

La misma calidad con el 22% de las llamadas. Es el patrón general: **una pieza cara detrás de una condición barata**,
y la condición sale de una pieza que ya pagaste.

---

<a name="5-caches"></a>
## 5. Cachés

Tres cachés distintas, que no hay que confundir:

- **La caché de llamadas del curso** (`llm_cache`): misma entrada, misma salida guardada. Sirve para que los
  laboratorios no vuelvan a pagar, y esconde la variación entre corridas (por eso las mediciones de latencia se hacen
  sin ella).
- **Una caché de parseos en producción**: la consulta normalizada (minúsculas, espacios) como clave y la consulta
  entendida como valor. Su valor depende de **cuánto se repiten las consultas**, y eso se mide en tus logs, no se
  supone (ejercicio 1). Caduca cuando cambias el prompt o el modelo del parser: la clave incluye su versión.
- **La caché de prompts del proveedor**: el proveedor cobra menos por el prefijo de entrada que ya vio hace poco. El
  trazador la registra (`tokens_cache`). Se aprovecha poniendo lo fijo (instrucciones, esquema) al principio y lo
  variable (la consulta, los CVs) al final.

Y una advertencia del Módulo 8: las tres guardan datos. Una caché de respuestas es una copia más en el inventario.

---

<a name="6-fallas"></a>
## 6. Cómo falla de verdad

[`code/02_que_no_se_caiga.py`](code/02_que_no_se_caiga.py) empieza por las trazas de este proyecto: **14.077 llamadas al
LLM, 84 con error (0.6%)**.

| Veces | Error | Qué fue |
|---|---|---|
| 51 | `Missing credentials` | correr sin la clave cargada en el entorno |
| 30 | `404 · The model gpt-4.1-nano…` | un modelo retirado por el proveedor |
| 2 | validación | el modelo no pudo cumplir el esquema (una prueba a propósito) |
| 1 | `Request timed out` | el único fallo del proveedor |

Casi ningún fallo fue "el proveedor se cayó": fueron **configuración** y **un modelo retirado**. Las dos cosas se
detectan antes de servir un pedido: una prueba de arranque que haga una llamada mínima con el modelo configurado, y
el eval en CI del curso de Evals (Módulo 9), que habría fallado el día que retiraron el modelo.

---

<a name="7-caida"></a>
## 7. Una caída simulada

Sin llamadas al LLM: 1.000 pedidos, uno por segundo. El parser tarda lo que tardó en tus trazas, falla el 2% de las
veces y, entre los pedidos 400 y 600, el proveedor está caído (cada intento se cuelga hasta el tiempo límite). Cinco
estrategias con el modelo principal, y dos con el barato:

| Estrategia | Disponible | nDCG@10 | p50 | p95 | Peor | Llamadas |
|---|---|---|---|---|---|---|
| Ingenua (defaults del SDK: 600 s, 2 reintentos) · principal | 80.0% | 0.717 | 3.9 s | **1.802 s** | 1.802 s | 1.419 |
| Límite 5 s + 2 reintentos · principal | 80.0% | 0.719 | 3.9 s | 16.6 s | 17 s | 1.504 |
| **Límite 5 s + respaldo** · principal | **100%** | 0.832 | 3.9 s | 5.0 s | 5 s | 1.000 |
| Presupuesto 3 s + respaldo · principal | 100% | 0.728 | 3.0 s | 3.0 s | 3 s | 1.000 |
| Presupuesto 3 s + cortacircuitos · principal | 100% | 0.690 | 0.1 s | 3.0 s | 3 s | 169 |
| **Límite 5 s + respaldo · nano** | **100%** | **0.852** | 1.3 s | 5.0 s | 5 s | 1.000 |
| **Presupuesto 3 s + cortacircuitos · nano** | **100%** | 0.846 | 1.2 s | **2.3 s** | 3 s | 797 |

Sin fallos, el techo es 0.893 (siempre con parser) y el piso 0.685 (nunca).

Lo que enseña:

- **Los valores por defecto no son una decisión.** El SDK espera hasta 600 s por intento y reintenta dos veces: en la
  caída, cada pedido queda colgado media hora. Nadie elige eso; se hereda.
- **Reintentar no arregla una caída.** Recupera los fallos sueltos (el 2%), pero contra un proveedor caído solo
  multiplica la espera y las llamadas.
- **El respaldo es lo que da disponibilidad.** Si el parser no responde, se busca con la híbrida sin entender la
  consulta: peor (0.685 contra 0.893), pero **una respuesta peor es mejor que un error**. Es posible porque el sistema
  tiene una ruta sin LLM; diseñar esa ruta es parte del sistema, no un parche.
- **Un presupuesto por debajo de la mediana destruye la calidad.** Con el modelo principal (p50 3.6 s), 3 s cortan más
  de la mitad de los parseos: nDCG 0.728. El presupuesto se fija desde la distribución de latencias, y el
  **cortacircuitos** lo empeora: interpreta la lentitud como fallo y apaga el parser casi todo el tiempo (169 llamadas
  de 1.000, nDCG 0.690).
- **Con el modelo barato todo encaja**: su p95 (1.7 s) cabe en el presupuesto, el cortacircuitos solo se abre en la
  caída real y evita esperarla (p95 2.3 s, 797 llamadas) a cambio de 0.006 de nDCG. **Elegir el modelo también es una
  decisión de fiabilidad**, y el §3 ya había dicho que en calidad daba igual.

---

## Resumen del módulo

- Cada pieza lleva **tres números**: calidad, latencia y tokens. Las trazas los dan.
- El **parser** es la mejor compra (+0.21 por una llamada); el **modelo principal** no compra nada ahí; el **reranker**
  compra +0.02 por 20 llamadas.
- **Pagar solo donde compra**: el reranker detrás de una condición del parser da la misma calidad con el 22% de las
  llamadas.
- Las cachés ahorran según **cuánto se repite el tráfico**, que se mide; y guardan datos.
- Las fallas reales de este proyecto fueron **configuración y un modelo retirado**: se detectan antes de servir.
- Contra una caída: **tiempo límite explícito y una ruta de respaldo sin LLM**. Reintentar no basta, y un presupuesto o
  un cortacircuitos mal calibrados contra la latencia real empeoran la calidad.
- El modelo barato, medido igual de bueno, también fue **el más fiable**.

Sigue con [`ejercicios.md`](ejercicios.md).
