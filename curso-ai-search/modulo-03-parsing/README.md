# Módulo 3 · El parsing le pone techo a todo el RAG

> **Objetivo:** medir cuánta información se pierde **antes** de buscar, cuando los CVs llegan como PDFs reales (a dos
> columnas o escaneados), y saber qué arreglo de la ingesta paga y cuál no.
>
> **Lo que te llevas:** 119 PDFs en tres formatos, tres formas de parsearlos, la medición de los hechos que sobreviven,
> de las fichas que salen y de la búsqueda que resulta, y la prueba de que el techo depende del extractor.

Índice:

1. [El techo](#1-techo)
2. [Documentos como llegan](#2-documentos)
3. [Tres formas de parsear](#3-formas)
4. [¿Sobreviven los hechos?](#4-hechos)
5. [El OCR](#5-ocr)
6. [Aguas abajo: fichas y búsqueda](#6-abajo)
7. [El techo depende de quién lee después](#7-extractor)
8. [Cómo saber si tu ingesta pierde información](#8-saber)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-techo"></a>
## 1. El techo

Todo lo que el sistema hace después (las fichas, el índice, el parser, el ranking) trabaja sobre el **texto que salió
de la ingesta**. Si un dato se perdió al leer el PDF, no hay reranker ni prompt que lo recupere. La calidad del parsing
es el **techo** de todo lo demás.

En los Módulos 1 y 2 el texto era perfecto: los CVs venían como texto plano y la extracción del índice coincidía con
los hechos en 119 de 119. En la práctica, los CVs llegan en PDF, y no todos los PDFs tienen texto.

---

<a name="2-documentos"></a>
## 2. Documentos como llegan

[`code/01_documentos_dificiles.py`](code/01_documentos_dificiles.py) maqueta cada CV desde sus hechos en un PDF de
página A4, en tres formatos (un tercio cada uno):

- **Texto:** una columna, con capa de texto. El caso fácil.
- **Dos columnas:** a la izquierda nombre, rol, ciudad y experiencia; a la derecha tecnologías, inglés y certificación.
  Escritas **línea a línea, alternando columnas**, como hacen muchas herramientas que generan CVs.
- **Escaneado:** la página rasterizada a 110 dpi, sin capa de texto: una imagen.

Lo que devuelve `get_text()` en un PDF a dos columnas:

```
Carlos Vélez
Tecnologías:
Científico de datos
python
Barranquilla
scikit-learn
Experiencia:
estadística
…
```

Y en uno escaneado: una cadena vacía.

Para cada documento se guarda el **texto de referencia** (la columna izquierda entera y después la derecha): lo que una
ingesta perfecta debería recuperar.

---

<a name="3-formas"></a>
## 3. Tres formas de parsear

[`code/02_tres_formas_de_parsear.py`](code/02_tres_formas_de_parsear.py):

| Ingesta | Qué hace |
|---|---|
| **Ingenua** | `page.get_text()` y nada más |
| **Con OCR** | Si la página no tiene texto, se le pasa la imagen a un modelo con visión para que la transcriba |
| **Columnas + OCR** | Además, agrupa las líneas por su posición horizontal y lee la columna izquierda entera antes que la derecha |

---

<a name="4-hechos"></a>
## 4. ¿Sobreviven los hechos?

La primera medida es la más barata: de las tecnologías, la ciudad, los años de cada trabajo y la certificación de cada
CV, ¿qué fracción aparece en el texto parseado?

| Formato | Ingenua | Con OCR | Columnas + OCR | Referencia |
|---|---|---|---|---|
| Texto | 100 % | 100 % | 100 % | 100 % |
| Dos columnas | 100 % | 100 % | 100 % | 100 % |
| Escaneado | **0 %** | 100 % | 100 % | 100 % |

El escaneado sin OCR lo pierde **todo**, y sin ningún error: el documento se indexa, solo que vacío. En dos columnas,
todos los hechos **están**, pero desordenados. Una medida de "¿aparece la palabra?" no ve el desorden: hay que medir
aguas abajo.

---

<a name="5-ocr"></a>
## 5. El OCR

El OCR con un modelo con visión transcribió los 39 escaneados con todos sus hechos (100 %). Tres cosas a tener en
cuenta en un sistema real:

- **Cuesta una llamada con imagen por página**, mucho más cara que una de texto. Solo se hace cuando la página no tiene
  texto: así lo hace este pipeline.
- **Se guarda** (`salida/ocr.json`): un documento no se vuelve a transcribir.
- **Los escaneados reales son peores** que estos (torcidos, con manchas, a 72 dpi, con sellos). Una página limpia a 110
  dpi es el mejor caso. Mide tu OCR con tus documentos.

---

<a name="6-abajo"></a>
## 6. Aguas abajo: fichas y búsqueda

[`code/03_el_techo_de_la_busqueda.py`](code/03_el_techo_de_la_busqueda.py) toma el texto de cada ingesta, extrae las
fichas con el mismo extractor del Módulo 2 (`gpt-6-luna`), construye el índice y repite la búsqueda con filtros suaves.
El parser de consultas es el mismo y está en caché: **lo único que cambia entre filas es la ingesta**.

Fichas correctas (de 39 CVs escaneados):

| Ingesta | Rol | Años | Ciudad | Remoto | Inglés | Skills |
|---|---|---|---|---|---|---|
| Ingenua | 0 | 5 | 0 | 27 | 8 | 0 |
| Con OCR | 39 | 39 | 39 | 39 | 39 | 39 |

Una trampa en esa tabla: con un documento vacío, la ficha "acierta" remoto en 27 casos y el inglés en 8, solo porque
el valor por defecto (no remoto, sin inglés) coincide con el hecho. **Un acierto por defecto no es un acierto**: cuenta
los campos vacíos aparte, o la exactitud de una ingesta rota parece aceptable.

En dos columnas, `gpt-6-luna` extrajo bien las 40 fichas con el texto intercalado: 40 de 40 en todos los campos.

La búsqueda:

| Ingesta | nDCG@10 |
|---|---|
| Referencia (ingesta perfecta) | 0.89 |
| **Ingenua** | **0.72** |
| Con OCR | 0.89 |
| Columnas + OCR | 0.89 |

Un tercio de los CVs escaneados sin OCR le quita 17 puntos a la búsqueda. Ninguna técnica de los módulos que siguen
recupera esos puntos: los CVs escaneados no tienen nada que encontrar.

---

<a name="7-extractor"></a>
## 7. El techo depende de quién lee después

Que la ingesta ingenua de dos columnas no le hiciera nada a `gpt-6-luna` no significa que el orden no importe. Se
repitió la extracción de las 40 fichas a dos columnas con `gpt-5.4-nano`, dos veces:

| Texto de entrada | Skills correctas | Remoto correcto |
|---|---|---|
| Referencia (bien ordenado) | 40 · 40 | 40 · 40 |
| **Ingenua (intercalado)** | **37 · 35** | 39 · 38 |
| Columnas | 39 · 38 | 40 · 40 |

Con el texto intercalado, el modelo barato pierde tecnologías: una línea "python" metida entre "Barranquilla" y
"Experiencia:" ya no parece parte de una lista. La lectura por columnas recupera casi todo. Es decir: **un buen
extractor tapa un mal parsing, y uno barato no**. Si vas a bajar el costo de la extracción (Módulo 9), arregla antes la
ingesta.

---

<a name="8-saber"></a>
## 8. Cómo saber si tu ingesta pierde información

- **Cuenta los documentos sin texto.** Es la señal más barata y la más importante: un `get_text()` vacío es un escaneo
  (o un PDF de imágenes) y va a OCR.
- **Mide los hechos que sobreviven** en una muestra donde los conozcas (como aquí) o donde los etiquetes a mano.
- **Mide aguas abajo**, porque el desorden no se ve contando palabras: fichas contra hechos y búsqueda contra
  referencia, **con el extractor que vas a usar**.
- **Cuenta los aciertos por defecto aparte**.
- **Mira los formatos de tus documentos reales**: tablas, columnas, encabezados repetidos, CVs de varias páginas. Cada
  formato es una dimensión del set (Módulo 3 de Evals).

---

## Resumen del módulo

- El parsing es el **techo**: lo que se pierde al leer no lo recupera nada después.
- Sin OCR, los escaneados se indexan **vacíos y sin error**: la búsqueda cayó de 0.89 a **0.72**. Con OCR, volvió a
  0.89.
- El desorden de dos columnas **no se ve contando palabras** (100 % de hechos presentes): hay que medir aguas abajo.
- Con `gpt-6-luna`, el texto intercalado no hizo daño; con `gpt-5.4-nano`, perdió tecnologías (35-37 de 40), y leer por
  columnas lo arregló. **El techo depende del extractor.**
- **Un acierto por defecto no es un acierto**: un documento vacío "acertó" remoto en 27 de 39.

Sigue con [`ejercicios.md`](ejercicios.md).
