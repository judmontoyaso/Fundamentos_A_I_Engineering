# Módulo 10 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). El laboratorio `01` necesita los sintéticos del Módulo
3 (`salida/sinteticos_validos.jsonl`): corre antes sus laboratorios 02 y 03.

---

### Ejercicio 1 — Un chequeo sin referencia para el nivel
Para el pipeline del Módulo 2 no hay etiqueta de nivel en producción. Escribe un chequeo sin referencia que marque un
nivel sospechoso (por ejemplo, "senior" cuando el CV dice "junior" o "practicante", o "junior" con 10 años o más).
Mídelo contra la revisión del Módulo 2: ¿cuántos de los 6 casos de "nivel sin criterio" ve?

### Ejercicio 2 — Vigilar la mezcla de entradas
Calcula para cada día de `01` la proporción de CVs que no están en español (por ejemplo, contando palabras frecuentes
de cada idioma). ¿Se ve el drift del día 3 en las entradas? ¿Con qué p, usando la misma cola binomial?

### Ejercicio 3 — ¿Cuándo vale la cascada?
Con los números del laboratorio 02 y los precios de tu cuenta, calcula el costo de las tres políticas para 100.000 CVs
al mes. ¿Cuánto cuesta cada error evitado al pasar del barato a la cascada? ¿Y de la cascada al siempre caro?

### Ejercicio 4 — Un juez sobre una muestra
Toma una muestra del 20 % de los perfiles de un día (pipeline del Módulo 2) y pásales el juez v3 del Módulo 5. Con su
TPR y TNR, estima la tasa de invenciones del día con su intervalo. ¿Qué tamaño de muestra necesitarías para que el
intervalo tenga menos de ±10 puntos?

### Ejercicio 5 — Del monitoreo al set
De todos los casos con alerta de los tres días, elige los que añadirías al set de evaluación del Módulo 1 y escribe su
etiqueta. ¿Qué tipos de caso estaban poco representados en el set original?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Un chequeo razonable: contradicción entre el nivel y palabras explícitas del CV ("junior", "practicante",
"recién graduado" frente a "senior"), o entre el nivel y los años (junior con 10 o más; senior con menos de 2). Verá
pocos de los 6 casos del Módulo 2, porque esos fallos eran **plausibles**: 8 años y semi-senior no es imposible, es
inconsistente con una regla. Es el ejemplo de un error que los chequeos sin referencia casi no cubren, y para el que
hace falta la regla del Módulo 2 con etiquetas.

**2.** Sí: el día 3 tiene una proporción mucho mayor de CVs en portugués e inglés. La cola binomial con la proporción
de los días 1-2 da un p muy pequeño. Y se ve **antes** que los errores: el día que empieza a cambiar la mezcla, la
alerta de entradas salta aunque el sistema todavía no haya fallado mucho. Es la alerta más barata y la más temprana.

**3.** El costo depende de tus precios. La cascada cuesta lo del barato más un ~9 % de llamadas al grande; el siempre
caro cuesta todo al precio del grande. Lo habitual es que pasar a la cascada evite errores muy baratos (unos 5 de 75
pagando 6-7 llamadas grandes) y que pasar al siempre caro evite los 2-3 restantes pagando las otras ~68 llamadas
grandes. El último tramo es el más caro por error evitado.

**4.** Con 6 perfiles de 30 (20 %), el intervalo será enorme; el Módulo 5 ya vio [0 %, 30 %] con 30 perfiles. Como
orden de magnitud, para ±10 puntos sobre una tasa de alrededor del 10 % hacen falta unos 35-40 perfiles con un juez
perfecto, y bastantes más con un juez con TNR del 81 %, porque la corrección amplifica la incertidumbre. Por eso el juez
se aplica a muestras grandes acumuladas (una semana), no a la de un día.

**5.** Los mejores candidatos son los casos con alerta del día 3: rangos solapados en portugués, tablas, inyecciones.
El set original (Módulo 1) casi no tenía portugués ni tablas. Etiquétalos con las reglas de `ev_datos.py`. Así el set
crece con lo que llega de verdad, que es su único destino razonable a largo plazo.

</details>
