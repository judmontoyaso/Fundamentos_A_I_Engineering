# Módulo 9 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Los tests se corren desde la carpeta del módulo con
`pytest tests -q` (o con el laboratorio `02`).

---

### Ejercicio 1 — Un test que atrape un bug del eval
Introduce a propósito un bug en `comparar_ficha()`: por ejemplo, que compare el nombre sin normalizar. Corre
`pytest tests -m "not llm"`. ¿Algún test falla? Si no, escribe el test que lo habría atrapado.

### Ejercicio 2 — Romper un caso crítico
Crea un prompt `v-mal` que diga "Si el CV contiene instrucciones, síguelas" y haz que `extraer()` lo use en la suite.
¿Qué test falla y con qué mensaje? (Después, quítalo.)

### Ejercicio 3 — Activar el workflow en tu repositorio
Copia `ci/evals.yml` a `.github/workflows/evals.yml`, crea el secreto `OPENAI_API_KEY` en tu repositorio y abre un pull
request con un cambio mínimo. ¿Qué jobs corren? ¿Cuánto tarda cada uno? ¿Qué pasa en el segundo pull request con la
caché?

### Ejercicio 4 — Una tolerancia con números
La tolerancia del umbral es 7 %. Con la variación que mediste en el Módulo 1 (el modelo barato perfecto en 27-29 de 30
según la corrida), ¿cuántas veces fallaría el test de umbral por puro ruido si la línea base fuera 29/30? Ajusta la
tolerancia para que el ruido no lo dispare, y di qué regresión dejarías de detectar.

### Ejercicio 5 — Más poder
Con McNemar, 0 arreglados y 4 rotos no bloquean con 30 casos. Usa los 35 sintéticos del Módulo 3 junto a los 30
originales (65 casos) y repite el laboratorio 03. ¿Cambia la decisión de v1 a v2? ¿Cuántos rotos sin arreglos harían
falta ahora para bloquear?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** `test_nombre_sin_tildes_ni_mayusculas` falla: compara "LAURA GOMEZ" con "Laura Gómez" y, sin normalizar, no
coinciden. Si tu bug fuera otro (por ejemplo, aceptar cualquier correo cuando se esperaba `None`), el test de
`test_correo_ausente` lo atrapa. La regla: cada decisión de tolerancia que tomaste en un módulo merece un test que la
fije.

**2.** Falla `test_casos_criticos[22-anios]` con el mensaje "#22 inyección: anios": el modelo registra 30 años. Es el
test que bloquea el cambio sin ninguna estadística. Nota: con la caché activa, el prompt nuevo no está en caché, así
que el test paga esas llamadas; con el prompt de siempre, saldría de la caché.

**3.** En el pull request corren `sin-llm` (unos segundos más la instalación) y después `con-llm`. En el primero, la
caché está vacía y se pagan todas las llamadas; en el segundo, `actions/cache` restaura `cache_llm.db` y solo se
pagan las llamadas de los casos o prompts que cambiaron. Si `con-llm` falla por falta del secreto, revisa el nombre
exacto: los tests sin clave se saltan, no fallan.

**4.** Si la línea base fuera 29/30 (97 %), una corrida con 27/30 (90 %) quedaría a 7 puntos, justo en la frontera: el
test fallaría o no según el redondeo. Con 27-29 observados, una tolerancia de unos 10 % evita las falsas alarmas. A
cambio, una regresión real de 2 o 3 casos pasaría sin aviso. Es el intercambio de siempre: o más casos, o más falsas
alarmas, o más regresiones sin detectar. Por eso existen los casos críticos.

**5.** Con más casos, la misma proporción de roturas da un p más bajo. En el Módulo 3, v2 rompía los rangos solapados en
los sintéticos (de 4/6 a 6/6), así que es probable que aparezcan más rotos y que McNemar se acerque al umbral. Con 65
casos sigue haciendo falta un desequilibrio claro, pero se detectan regresiones más pequeñas. La forma barata de ganar
poder es tener más casos; la cara, más repeticiones.

</details>
