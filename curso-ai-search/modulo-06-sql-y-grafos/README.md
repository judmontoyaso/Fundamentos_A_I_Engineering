# Módulo 6 · Cuándo un grafo o SQL le ganan a los vectores

> **Objetivo:** reconocer las preguntas que no son de similitud (cuentas, listas exactas, máximos, relaciones) y
> responderlas consultando datos estructurados, con un LLM que escribe la consulta y nunca ve los datos.
>
> **Lo que te llevas:** una base relacional construida desde el índice, texto → SQL en modo solo lectura comparado con
> el RAG en 13 preguntas, una relación de grafo resuelta con un JOIN, y un enrutador entre buscar y consultar.

Índice:

1. [Preguntas que no son de similitud](#1-preguntas)
2. [Una base desde el índice](#2-base)
3. [El grafo que ya tenías](#3-grafo)
4. [Texto a SQL, con seguridad](#4-sql)
5. [Lo que pasó](#5-resultados)
6. [Los fallos eran definiciones](#6-definiciones)
7. [Buscar o consultar](#7-enrutar)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-preguntas"></a>
## 1. Preguntas que no son de similitud

El Módulo 5 terminó con una conclusión incómoda: con todo el corpus en el contexto, el LLM perdía candidatos de las
listas y se desviaba al contar. Y una búsqueda tampoco sirve para "¿cuántos juniors hay?": no hay un documento que se
parezca a esa pregunta. Hay preguntas que **no son de similitud**:

| Tipo | Ejemplo | Qué exige |
|---|---|---|
| Cuenta | "¿Cuántos candidatos son junior?" | Recorrer todos y contar |
| Lista exacta | "¿Quiénes trabajan con Kafka?" | Todos, ni uno de más ni de menos |
| Máximo | "¿Quién es el analista de datos con más años?" | Comparar todos |
| Relación | "¿Quiénes coincidieron con Tomás Duarte en la misma empresa y años?" | Seguir un vínculo entre registros |

Para eso existen las bases de datos.

---

<a name="2-base"></a>
## 2. Una base desde el índice

[`code/01_construir_la_base.py`](code/01_construir_la_base.py) carga las fichas del Módulo 2 en SQLite:
`candidatos` (rol, años, nivel, ciudad, remoto, inglés, liderazgo), `skills`, `certificaciones` y `trabajos`.

Hubo que extraer dos datos que el índice **no guardaba**: el nombre y la **empresa** de cada trabajo. Para buscar no
hacían falta; para relaciones, sí. Es la tercera vez en el curso que aparece la misma lección (certificaciones en el
Módulo 8 de Evals, duraciones en el Módulo 11 de Evals): **lo que no se extrae no existe para el sistema**, y lo que
hay que extraer depende de las preguntas que vas a responder. Se extrajo con el mismo modelo y coincidió con los hechos
en 119 de 119 CVs.

---

<a name="3-grafo"></a>
## 3. El grafo que ya tenías

Candidatos y empresas, unidos por "trabajó en, de tal año a tal año", forman un **grafo**. No hace falta una base de
grafos para recorrerlo: la tabla `trabajos` es la lista de aristas, y "¿quién coincidió con quién?" es esa tabla unida
consigo misma por empresa, con los periodos solapados:

```sql
SELECT DISTINCT c.nombre
FROM candidatos AS c
JOIN trabajos AS otro  ON otro.cv_id = c.id
JOIN trabajos AS tomas ON tomas.empresa = otro.empresa
JOIN candidatos AS ct  ON ct.id = tomas.cv_id
WHERE ct.nombre = 'Tomás Duarte' AND c.id <> ct.id
  AND otro.inicio < COALESCE(tomas.fin, 2026)
  AND tomas.inicio < COALESCE(otro.fin, 2026);
```

Una base de grafos (Neo4j, o grafos en Postgres) paga cuando los recorridos son largos y variables ("colegas de
colegas de colegas") o cuando el grafo es enorme. Con un salto o dos, SQL alcanza. Y un buscador por vectores no puede
responderlo: no hay ningún texto que diga "Tomás coincidió con estas 31 personas".

---

<a name="4-sql"></a>
## 4. Texto a SQL, con seguridad

[`code/02_sql_contra_rag.py`](code/02_sql_contra_rag.py): un LLM recibe el esquema y la pregunta, y devuelve **una**
consulta SELECT y el tipo de respuesta (nombres o cuenta). Tres reglas de seguridad que no dependen del modelo:

- **El LLM nunca ve los datos**, solo el esquema. Un CV con una inyección no puede influir en la consulta.
- **La conexión es de solo lectura** (`mode=ro`): aunque el modelo escribiera un `DELETE`, la base no se puede modificar.
- **Solo SELECT**, y con un límite de filas. El código formatea el resultado: el LLM no "resume" lo que salió.

---

<a name="5-resultados"></a>
## 5. Lo que pasó

13 preguntas (las 10 del Módulo 5 y 3 de relaciones), con la respuesta calculada desde los hechos:

| Pregunta | SQL v1 | SQL v2 | RAG (top 15) |
|---|---|---|---|
| Listas (6), máximo (1), certificación, analistas de seguridad | ✓ | ✓ | ✓ |
| ¿Cuántos son junior? | ✓ | ✓ | ✗ |
| ¿Cuántos trabajaron en Northwind? | ✓ | ✓ | ✗ |
| ¿Quiénes trabajaron en Banco Andino? | ✓ | ✓ | ✓ |
| ¿Quiénes coincidieron con Tomás Duarte? | ✗ | **✓** | ✗ |
| ¿Cuántos han liderado equipos? | ✗ | ✗ | ✗ |
| **Aciertos** | **11 / 13** | **12 / 13** | 9 / 13 |

El SQL gana donde había que esperar: cuentas sobre todo el conjunto y relaciones. El RAG acierta las listas cuando el
top 15 las contiene enteras, y falla cuando la respuesta exige ver más de 15 CVs.

---

<a name="6-definiciones"></a>
## 6. Los fallos eran definiciones

Los dos fallos de la primera versión no fueron errores de SQL:

- **"¿Cuántos han liderado equipos?"**: el modelo contó los cargos que contienen "líder" en el texto (15). Los cargos en
  inglés dicen "Lead". La tabla tenía la columna `lidera`, calculada justo para eso, y no la usó.
- **"¿Quiénes coincidieron con Tomás Duarte?"**: usó `<=`, así que dos periodos que solo comparten el año de frontera
  (2018-2020 y 2020-2022) contaron como coincidencia. Mis etiquetas exigían un solape estricto. Las dos lecturas son
  defendibles: **la definición no estaba escrita**.

La versión 2 **documenta el esquema** (qué significa `lidera`, qué es "coincidir") y acierta la relación. La cuenta de
liderazgo sigue fallando, ahora por otra razón: la consulta es la correcta (`WHERE lidera = 1`) y devuelve 17, pero los
hechos dicen 18. Una ficha del índice se equivocó en el liderazgo (el 118 de 119 del Módulo 2). **SQL es exacto sobre
los datos, y los errores de los datos pasan intactos.** Es el techo del Módulo 3 otra vez, en otra parte del sistema.

Dos lecciones para texto a SQL:

- **Un esquema sin documentar es una guía de anotación ambigua** (Módulo 4 de Evals): el modelo elige una lectura
  razonable que no es la tuya. Documenta el significado de cada columna y las definiciones del negocio.
- **Evalúa la consulta Y los datos**: una cuenta mal puede venir de la consulta o del índice. Mirar el SQL generado
  separa las dos causas.

---

<a name="7-enrutar"></a>
## 7. Buscar o consultar

Con dos rutas, alguien tiene que elegir. [`code/03_buscar_o_consultar.py`](code/03_buscar_o_consultar.py) usa un
clasificador barato sobre las 41 búsquedas del curso y las 13 preguntas de este módulo:

| | Corrida 1 | Corrida 2 |
|---|---|---|
| Búsquedas bien enrutadas | 37 / 41 | 36 / 41 |
| Consultas bien enrutadas | 13 / 13 | 13 / 13 |

Todas las confusiones van en el mismo sentido: búsquedas de una sola tecnología ("PyTorch", "dbt", "experiencia con
Airflow") y una numérica ("más de 8 años en backend") enviadas a consultar. **Son errores casi inofensivos**: para
"dbt", la consulta devuelve la lista exacta de quienes saben dbt, que es exactamente el conjunto relevante para esa
búsqueda. La frontera entre buscar y consultar es borrosa, y por eso un enrutador se evalúa por **lo que cambia en la
respuesta**, no solo por la etiqueta. El error caro sería el contrario (mandar una cuenta a la búsqueda), y no ocurrió.

---

## Resumen del módulo

- **Cuentas, listas exactas, máximos y relaciones no son de similitud**: se consultan, no se buscan.
- Para preguntas nuevas hace falta **extraer datos nuevos** (aquí, la empresa de cada trabajo).
- Las relaciones son un **grafo**, y con uno o dos saltos un JOIN alcanza.
- **Texto a SQL seguro**: el LLM ve solo el esquema, la conexión es de solo lectura y el código formatea la respuesta.
- SQL **12 de 13** contra RAG 9 de 13; los fallos de SQL fueron **definiciones sin escribir**, y el último, un error de
  los **datos** que la consulta reprodujo con exactitud.
- Un enrutador se evalúa por **lo que cambia en la respuesta**: sus errores (búsquedas de una tecnología enviadas a
  consultar) eran inofensivos.

Sigue con [`ejercicios.md`](ejercicios.md).
