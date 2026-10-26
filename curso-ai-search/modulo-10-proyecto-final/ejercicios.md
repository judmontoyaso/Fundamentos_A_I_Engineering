# Proyecto final · Rúbrica y solución de referencia

Primero la rúbrica, para que sepas contra qué se juzga tu informe. La solución de referencia está al final, colapsada:
no la abras hasta tener el tuyo.

---

## Rúbrica

| Criterio | Insuficiente | Bien | Muy bien |
|---|---|---|---|
| **Antes y después** | Un número de DEV | DEV y HOLDOUT | DEV y HOLDOUT con intervalo pareado, ganadas y perdidas, y dos corridas sin caché |
| **Lectura de fallos** | "Mejoró" | Una tabla de tipos de fallo antes de arreglar | La tabla, y cada cambio justificado por un tipo de fallo |
| **Cada pieza** | Todo junto | La ganancia total | La ganancia **de cada pieza** contra la anterior, incluidas las que no ganaron nada |
| **Entender la entrada** | Se usa la extracción sin mirarla | Se mide la extracción contra los hechos | Y se encuentran sus fallos (nombres canónicos, ciudades, deseables mezcladas) |
| **Costo y fiabilidad** | No se menciona | Llamadas y latencia por vacante | Y una ruta de respaldo probada (¿qué devuelve si el LLM falla?) |
| **Permisos** | No se aplican | Pre-filtro y medición con permisos | Y qué hace el sistema cuando ningún candidato autorizado cumple todo |
| **Honestidad** | Solo lo que salió bien | Lo que falla, con ejemplos | Lo que el eval **no mide**, y el holdout mirado una sola vez |

---

## Preguntas para el informe

1. ¿Qué pieza compró casi toda la mejora? ¿Alguna no compró nada?
2. ¿Tu métrica premia algo que el reclutador no pidió, o ignora algo que sí pidió?
3. Con permisos, ¿cuántas vacantes no tienen un candidato autorizado que cumpla todo? ¿Qué debería mostrar el sistema?
4. Si mañana el LLM no responde, ¿qué ve el reclutador?
5. ¿Qué encontraste mirando el holdout que ya no puedes arreglar con una medición honesta?

---

<details>
<summary><b>Solución de referencia</b></summary>

El código está en [`solucion/emparejador_de_referencia.py`](solucion/emparejador_de_referencia.py).

### Lo que hace

1. **Entiende la vacante** con el modelo barato: rol del catálogo, requeridas, deseables **aparte**, años mínimos (si
   hay rango, el mínimo), remoto o ciudad, inglés. Una llamada por vacante.
2. **Busca corto**: la consulta es el rol y las requeridas, no las 300 palabras de la vacante.
3. **Ordena por requisitos** sobre las fichas del índice (los filtros suaves del Módulo 2): primero cuántos cumple, a
   igualdad cuántas deseables tiene, a igualdad el orden de la híbrida.
4. **Respaldo**: si la extracción falla, devuelve la búsqueda de hoy.
5. **Permisos**: pre-filtra los CVs autorizados para el cliente de la vacante.

### Antes y después

| | Corrida 1 (DEV) | Corrida 2 sin caché (DEV) | Corrida 1 (HOLDOUT) | Corrida 2 sin caché (HOLDOUT) |
|---|---|---|---|---|
| Línea base nDCG@10 | 0.678 | 0.678 | 0.750 | 0.750 |
| Referencia nDCG@10 | **0.932** | **0.963** | **0.933** | **0.954** |
| Diferencia [IC 95%] | +0.25 [+0.13, +0.40] | +0.29 [+0.17, +0.43] | +0.18 [+0.07, +0.31] | +0.20 [+0.09, +0.33] |
| Gana · pierde | 14 · 1 | 15 · 0 | 11 · 4 | 12 · 3 |
| MRR | 0.57 → 0.96 | 0.57 → 1.00 | 0.61 → 0.95 | 0.61 → 1.00 |

La mejora se sostiene en el holdout, y es algo menor que en DEV, como debe ser.

### Cada pieza (DEV, corrida 1)

| Pieza | nDCG@10 | Contra la fila anterior |
|---|---|---|
| Línea base (la vacante entera) | 0.678 | |
| + consulta corta (rol y requeridas) | 0.735 | +0.06 [−0.08, +0.18], gana 10 y pierde 5 |
| + orden por requisitos | 0.939 | **+0.20 [+0.09, +0.35]** |
| + deseables como desempate | 0.932 | −0.01 [−0.03, +0.01] |

- **Casi toda la mejora la compra el orden por requisitos.** Acortar la consulta, por sí solo, no se distingue de cero:
  la búsqueda sigue sin saber qué es obligatorio.
- **Las deseables no compran nada… según la métrica.** La relevancia del proyecto no cuenta las deseables, así que
  ordenar por ellas no puede ganar. Para el reclutador probablemente sí importan. Es la respuesta a la pregunta 2: **el
  eval no mide las deseables**; si importan, hay que etiquetarlas (por ejemplo, relevancia 3 para quien cumple todo y
  tiene deseables). Mantenerlas sin evidencia es una decisión de producto, y el informe tiene que decirlo así.

### Costo y fiabilidad

Una llamada al modelo barato por vacante; unos 2 s por vacante en vivo (casi todo es el LLM). Si la llamada falla, el
respaldo devuelve la búsqueda de hoy: peor (0.68), pero una respuesta.

### Lo que todavía falla

- **Nombres canónicos.** En la corrida 1 el parser escribió `amazon web services (aws)` donde la vacante decía AWS, y
  el requisito dejó de coincidir con las fichas. La instrucción del Módulo 2, "con su nombre completo (k8s ->
  kubernetes)", **provocó** la expansión. En la corrida 2 no pasó: es intermitente, que es peor. El arreglo es
  normalizar contra el vocabulario de skills del índice, no pedírselo al modelo.
- **Ciudades.** "Bogotá, Colombia" no coincide con "Bogotá": el requisito de ciudad falla para todos.
- **El rol pesa como un requisito más.** Un CV de otro rol que cumple las tecnologías, la ciudad y los años puede
  ganarle a uno del rol correcto que cumple menos. En las vacantes #1 (analista de datos) y #2 (desarrollador Python)
  del holdout, los puestos 8 a 10 los ocupan CVs de otros roles (un ingeniero de datos, un científico de datos) que
  desplazan a candidatos del rol correcto.
- **El emparejamiento de skills es por subcadena** (heredado de `en.requisitos`): "sql" se encuentra dentro de
  "postgresql" y de "sql server".

Los dos últimos los encontré **mirando el holdout**, en las vacantes donde la referencia pierde. Ya no puedo arreglarlos
y medir el arreglo con ese holdout: la siguiente iteración necesita vacantes nuevas (el generador las produce desde los
hechos con otra semilla). Es la pregunta 5.

### Con permisos

Con el pre-filtro por cliente (Módulo 8), en las 30 vacantes: base 0.785, referencia **0.976**. **6 de 30 vacantes se
quedan sin ningún candidato autorizado que cumpla todo.** El sistema no debería esconderlo detrás de un top 10 de
"casi": debería decir "ningún candidato autorizado cumple todos los requisitos; estos son los más cercanos y esto es lo
que les falta", que es la fase 6 (explicar) y una alerta para el equipo comercial (hay que conseguir candidatos para
ese cliente).

### Recomendación

Se usa, con la extracción normalizada contra el vocabulario del índice, el rol como requisito duro (o con más peso) y
un aviso explícito cuando ningún candidato cumple todo. Antes de ampliar: 30 vacantes nuevas para un holdout limpio, y
etiquetas que cuenten las deseables si el negocio las quiere en el orden.

</details>
