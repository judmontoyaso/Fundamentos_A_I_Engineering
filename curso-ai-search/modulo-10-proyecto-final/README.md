# Proyecto final · Un sistema medido antes y después

> **Objetivo:** tomar un sistema de búsqueda que funciona "más o menos", medirlo, mejorarlo con las piezas del curso y
> **demostrar** la mejora: con un holdout, un intervalo, el costo que agrega y lo que todavía falla.
>
> **El sistema:** un **emparejador** que recibe una vacante entera (no una consulta de cuatro palabras) y devuelve los
> diez mejores candidatos de los 119.

Índice:

1. [El sistema](#1-sistema)
2. [Los datos](#2-datos)
3. [Las reglas del juego](#3-reglas)
4. [Las fases](#4-fases)
5. [Entregables y rúbrica](#5-entregables)

Código en [`code/`](code/). Rúbrica y solución de referencia en [`ejercicios.md`](ejercicios.md).

---

<a name="1-sistema"></a>
## 1. El sistema

El área de selección quiere pegar una vacante y recibir a los candidatos. La versión de hoy,
[`code/01_el_emparejador.py`](code/01_el_emparejador.py), hace lo más simple: usa **el texto completo de la vacante**
como consulta de la búsqueda híbrida del Módulo 1.

Las vacantes no se parecen a las consultas del curso:

- Son **largas**: un párrafo sobre la empresa, responsabilidades, beneficios y proceso de selección alrededor de tres
  líneas de requisitos.
- Mezclan **requeridas y deseables**: "Python y Spark obligatorios; Kafka es un plus".
- Piden **años** ("de 3 a 6 años"), una **ciudad** o trabajo remoto, a veces **inglés B2**.
- Vienen en cinco estilos, uno de ellos en inglés.

---

<a name="2-datos"></a>
## 2. Los datos

[`comun/as_vacantes.json`](../comun/as_vacantes.json): 30 vacantes generadas **desde los hechos**
([`comun/as_vacantes.py`](../comun/as_vacantes.py)), como los CVs. Cada una sale de un CV ancla, así que siempre hay al
menos un candidato que la cumple. La relevancia se calcula con código:

| Relevancia | Cuándo |
|---|---|
| 2 | mismo rol, **todas** las requeridas, años suficientes, ubicación compatible e inglés suficiente |
| 1 | mismo rol, pero falla alguno de esos requisitos |
| 0 | otro rol |

Las **deseables no cuentan** para la relevancia. Hay 1.5 candidatos de relevancia 2 por vacante en promedio: el trabajo
es ponerlos arriba.

La partición es fija: **DEV** (15 vacantes) para iterar y **HOLDOUT** (15) para la medición final. El arnés (`medir`,
`comparar` con bootstrap pareado, `resumen`) está en `01_el_emparejador.py`.

La línea base en DEV: **nDCG@10 0.678 · recall@10 0.917 · MRR 0.568**. El peor estilo es el más corto, "lista de
requisitos" (0.55, en 6 vacantes). Por qué, es tu primera pregunta de la fase 2.

---

<a name="3-reglas"></a>
## 3. Las reglas del juego

- **El holdout se mira una vez.** Itera en DEV todo lo que quieras; cuando decidas tu versión final, corre
  `HOLDOUT=1`. Si después de mirarlo cambias algo, ese cambio ya no tiene medición honesta.
- **Todo número con su tamaño y su repetición.** 15 vacantes son pocas: un intervalo bootstrap y al menos dos corridas
  sin caché.
- **Cada pieza que agregues, con sus tres números** (Módulo 9): cuánto mejora, cuánto tarda, cuántas llamadas.
- **No leas la solución de referencia** (al final de `ejercicios.md` y en `solucion/`) hasta tener tu informe.

---

<a name="4-fases"></a>
## 4. Las fases

Cada fase es un módulo del curso:

| Fase | Qué haces | Módulo |
|---|---|---|
| 1. Medir antes | Corre `01_el_emparejador.py`: la línea base, por estilo, y las tres peores | 0, 1 |
| 2. Leer los fallos | Lee las peores vacantes y lo que devolvió el sistema. ¿Qué tipo de fallo es cada una? Haz la tabla de tipos | 1 |
| 3. Entender la vacante | Extrae los requisitos con un LLM: rol, requeridas **separadas de las deseables**, años, ubicación, inglés. Mide la extracción contra los hechos antes de usarla | 2 |
| 4. ¿El parsing pone techo? | ¿Hay vacantes donde la extracción pierde datos? ¿Y CVs cuya ficha está mal? (el techo del Módulo 3) | 3 |
| 5. Ordenar | Con los requisitos: filtros suaves, deseables como desempate, quizá el reranker. Cada pieza con su ganancia **pareada** | 2, 4 |
| 6. Explicar | Opcional: que el sistema diga por qué propone a cada candidato y qué requisito no cumple, con el contexto justo | 5 |
| 7. Permisos | Cada vacante es de un cliente (`hechos["cliente"]`): solo puede ver los CVs autorizados para él. Pre-filtra y mide de nuevo | 8 |
| 8. Costo y fiabilidad | Llamadas, latencia y tokens por vacante. ¿Qué pasa si el LLM no responde? Ten una ruta de respaldo | 9 |
| 9. Holdout | Una sola vez, con tu versión final | 1 |

Escribe tu versión en [`code/02_tu_emparejador.py`](code/02_tu_emparejador.py). Ya trae la comparación con la línea
base, el intervalo y la lista de vacantes donde pierdes.

---

<a name="5-entregables"></a>
## 5. Entregables y rúbrica

Un **informe de una página** para quien decide si se usa el emparejador:

1. **Antes y después**, en DEV y en HOLDOUT, con el intervalo de la diferencia y cuántas vacantes gana y pierde.
2. **Qué hizo cada pieza**: la ganancia de cada cambio, en el orden en que los agregaste.
3. **Cuánto cuesta**: llamadas al LLM, latencia y qué pasa si el LLM falla.
4. **Lo que todavía falla**, con ejemplos, y **lo que tu eval no mide**.
5. **Con permisos**: cuántas vacantes se quedan sin un candidato autorizado que cumpla todo, y qué debería decir el
   sistema en ese caso.
6. **Tu recomendación.**

La rúbrica y la solución de referencia, en [`ejercicios.md`](ejercicios.md).

---

## Lo que se practica

Todo el curso en un sistema nuevo: **medir antes de tocar**, **leer los fallos**, **entender la entrada** en vez de
buscar con ella tal cual, **ordenar por requisitos**, **cada pieza con su ganancia pareada y su costo**, **permisos
antes de buscar**, **una ruta de respaldo** y **un holdout que se mira una vez**.
