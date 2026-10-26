# Módulo 11 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). El holdout son los sintéticos del Módulo 3
(`salida/sinteticos_validos.jsonl`).

---

### Ejercicio 1 — ¿Cuánto varía la misma versión?
Corre `02` tres veces solo con v2 (deja `VERSIONES = ["v2"]`) y anota desarrollo y holdout en cada una. ¿Cuál es el
rango? Con ese rango, ¿qué diferencia mínima entre dos versiones te creerías?

### Ejercicio 2 — Las skills en mayúsculas
El #23 ("SAS, R." en un CV todo en mayúsculas) falla en casi todas las versiones. Lee sus salidas, escribe una
hipótesis y un cambio (en el prompt, o en código: por ejemplo, pasar el CV a minúsculas antes de extraer las skills).
Mídelo en el #23 solo, 6 veces, y después en todo el desarrollo. ¿Rompe algo?

### Ejercicio 3 — v5 con el modelo grande
Corre v1 y v5 con `gpt-6-luna` en desarrollo y holdout. ¿Gana algo v5 con un modelo que ya sumaba bien? ¿Cuesta más
tokens el schema de hechos?

### Ejercicio 4 — Pasar v5 por la suite del Módulo 9
Haz que la suite del Módulo 9 pruebe v5 (casos críticos y umbral). ¿Pasa los críticos? Usa la regla de McNemar del
laboratorio 03 del Módulo 9 para decidir entre v2 y v5 en el holdout. ¿Bloquea, pasa o pasa con aviso?

### Ejercicio 5 — Un holdout de verdad
El holdout de este módulo son sintéticos escritos por un LLM. Escribe 10 CVs a mano con formatos que ninguno de los
dos sets tenga (por ejemplo, fechas como "mar 2018 - jun 2021", CVs larguísimos, dos idiomas mezclados), etiquétalos y
mide v2 y v5. ¿Se mantiene la ventaja de v5?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Al escribir el curso, v2 dio 27, 27 y 29 en desarrollo, y 24, 26 y 28 en el holdout. Con un rango de 2-4 casos,
una diferencia de 1 o 2 casos entre versiones no significa nada. Te creerías una diferencia claramente mayor que el
rango y que se repita en varias ejecuciones, como la de v4 en el holdout (5-10 casos, en las dos).

**2.** Una hipótesis razonable: en un texto todo en mayúsculas, "SAS, R." no parece una lista de tecnologías para el
modelo pequeño (la "R" suelta se confunde con una inicial). Un cambio en código, extraer las skills de una versión del
CV en minúsculas o con mayúsculas solo al inicio de frase, suele ayudar más que una instrucción. Mídelo primero en el
caso y después en todo el set: normalizar el texto puede cambiar otras extracciones (los nombres, por ejemplo).

**3.** Con el modelo grande, v1 ya sacaba 30/30 en desarrollo y 35/35 en los sintéticos (Módulos 1 y 3), así que v5 no
tiene margen para ganar, y puede perder algo si el schema más complejo trae fallos nuevos. El schema de hechos suele
costar más tokens de salida (lista de trabajos). Conclusión: un cambio estructural vale para el modelo que lo necesita;
con el grande, lo que decide es el costo.

**4.** Los críticos de la suite son el #22, #24, #16 y #25. v5 resolvió la pérdida del #22 de v4, pero mídelo con
repeticiones: con un caso crítico, un 5 de 6 no basta. En el holdout, v5 frente a v2 arregla bastantes más casos de los
que rompe; si la diferencia es de 5 o más casos sin roturas, McNemar bloquea a favor de v5 (en el sentido contrario:
"v2 es significativamente peor").

**5.** Lo esperable es que v5 mantenga la ventaja en los formatos de rangos y que aparezcan fallos nuevos en las fechas
con meses ("mar 2018 - jun 2021"), que su schema no representa (solo años). Si pasa, el siguiente cambio está claro: un
campo de mes, y la regla de "años completos" en código. Un holdout escrito por personas, con formatos reales, es el que
de verdad dice si la mejora generaliza.

</details>
