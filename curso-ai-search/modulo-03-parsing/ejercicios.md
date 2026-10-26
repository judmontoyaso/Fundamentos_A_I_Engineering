# Módulo 3 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Corre los laboratorios en orden: `01` crea los PDFs,
`02` los parsea (y guarda el OCR), `03` mide aguas abajo.

---

### Ejercicio 1 — Un escaneo peor
Cambia en `01` la resolución del escaneo de 110 a 60 dpi y añade una rotación pequeña (por ejemplo, rasteriza con una
matriz `pymupdf.Matrix(1, 1).prerotate(2)`). Borra `salida/ocr.json` y repite `02` y `03`. ¿Cuántos hechos sobreviven al
OCR? ¿Cuánto baja la búsqueda?

### Ejercicio 2 — Una tabla
Añade un cuarto formato: la experiencia en una tabla de tres columnas (cargo | empresa | años) dibujada con líneas.
¿Qué devuelve `get_text()`? ¿Y `page.find_tables()`? ¿Qué ingesta recupera mejor los años?

### Ejercicio 3 — Detectar los documentos vacíos
Escribe un chequeo de ingesta que, sin conocer los hechos, marque los documentos con riesgo: sin texto, con muy poco
texto para un CV, o con líneas cortas que alternan temas (señal de columnas). ¿Cuántos de los 119 marca? ¿Coinciden con
los formatos difíciles?

### Ejercicio 4 — Los aciertos por defecto
Rehace la tabla de fichas del escaneado ingenuo contando solo los campos donde la ficha **no** está vacía (o no es el
valor por defecto). ¿Qué queda de los 27 aciertos de remoto?

### Ejercicio 5 — ¿Cuánto cuesta el OCR?
Con las trazas del laboratorio 02, suma los tokens de las 39 llamadas de OCR y compáralos con los de las 119 extracciones
de fichas. ¿Qué parte del costo de la ingesta es OCR? ¿Cómo lo bajarías si la mitad de tus CVs fueran escaneados?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** A 60 dpi y torcido, el OCR empieza a confundir caracteres en lo pequeño: años ("2018" por "2016"), siglas y
correos. Los hechos que sobreviven bajan de 100 %, sobre todo los años, y con ellos el nivel calculado. La búsqueda baja
menos que con la ingesta ingenua, porque el rol y la mayoría de tecnologías se leen igual. Lección: mide el OCR con
documentos como los tuyos, no con el mejor caso.

**2.** `get_text()` suele devolver las celdas en orden de lectura de la página, a veces con los años separados de su
cargo. `find_tables()` reconoce la estructura y permite leer celda a celda (Módulo 1 de AI Engineering, laboratorio de
PDFs). La ingesta que lee la tabla como tabla recupera mejor qué años van con qué cargo, que es lo que el cálculo de
años necesita.

**3.** Un chequeo razonable: menos de 100 caracteres → sin texto; muchas líneas de una o dos palabras que alternan
entre tecnologías y datos personales → posibles columnas. Marca los 39 escaneados con certeza y buena parte de los de
dos columnas. Es un chequeo sin referencia (Módulo 10 de Evals) aplicado a la ingesta: barato, y con él sabes qué
documentos revisar o mandar a OCR.

**4.** Desaparecen casi todos: la ficha de un documento vacío dice "no remoto" porque no sabe nada, y coincide con los
CVs que no aceptan remoto. Contando solo los campos con información, la ingesta ingenua del escaneado acierta cero en
todo. Es la forma honesta de reportar.

**5.** Una llamada con imagen suele costar varias veces más tokens de entrada que una de texto. Con un tercio de
escaneados, el OCR puede ser una parte grande del costo de la ingesta, aunque se haga una sola vez por documento. Para
bajarlo: OCR clásico (Tesseract, el OCR de un proveedor de la nube) para el texto y un LLM solo para los documentos
donde el OCR clásico sale con poca confianza, y siempre guardando el resultado.

</details>
