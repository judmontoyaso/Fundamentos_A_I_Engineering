# Módulo 0 · Qué vamos a evaluar

> **Objetivo:** entender por qué probar a mano no alcanza, qué es un eval en su forma más simple, y conocer los
> sistemas y los datos con los que vamos a trabajar todo el curso.

Índice:

1. [El problema: "lo probé y funciona"](#1-problema)
2. [Qué es un eval](#2-que-es)
3. [Los tres sistemas](#3-sistemas)
4. [Los datos del curso](#4-datos)
5. [Qué no es este curso](#5-no-es)
6. [Antes de medir, mirar](#6-mirar)

Código en [`code/`](code/).

---

<a name="1-problema"></a>
## 1. El problema: "lo probé y funciona"

Así se evalúan casi todos los sistemas con LLM al principio: escribes cinco entradas, miras las respuestas, se ven
bien, sigues. Los profesionales lo llaman *vibe check*. Tiene tres problemas:

- **No se repite.** El mes que viene cambias el prompt o el modelo y vuelves a probar cinco entradas, que ya no son
  las mismas. No sabes si algo que funcionaba dejó de funcionar.
- **No se cuenta.** "Se ve bien" no dice si falla una vez de cada diez o una de cada mil. Y un sistema estocástico
  falla de vez en cuando por definición (curso de AI Engineering, Módulo 1).
- **Prueba lo que ya sabías que funcionaba.** Las entradas que se te ocurren a ti son las que tenías en mente al
  escribir el prompt. Los usuarios escriben otras.

Un **eval** resuelve los tres: es un conjunto fijo de casos que se ejecuta igual cada vez, con un resultado que se
cuenta y se guarda.

---

<a name="2-que-es"></a>
## 2. Qué es un eval

En su forma mínima, un eval tiene cinco piezas:

1. **Casos:** entradas representativas, incluidas las difíciles.
2. **Lo esperado:** la respuesta correcta, o el criterio que debe cumplir la respuesta.
3. **Un chequeo:** algo que compara lo obtenido con lo esperado y devuelve sí o no.
4. **Una agregación:** cuántos pasan, por tipo de caso.
5. **Un registro:** el resultado guardado con la versión del sistema, para comparar con la siguiente.

El chequeo es lo que cambia de un eval a otro, y se elige **del más barato al más caro**:

| Chequeo | Cuándo sirve | Costo |
|---|---|---|
| **Código** (igualdad, regex, esquema, "contiene") | La respuesta correcta es exacta: un correo, un número, una categoría | Gratis e instantáneo |
| **Referencia** (comparar con una respuesta ideal) | Hay una respuesta buena conocida, pero se puede decir de muchas formas | Barato si es por código, una llamada si es con LLM |
| **LLM como juez** | El criterio exige leer y entender ("¿la respuesta está respaldada por los CVs?") | Una llamada por caso, y hay que calibrarlo (Módulo 5) |
| **Una persona** | El criterio es discutible o nuevo | Caro y lento; es la referencia contra la que se calibra todo lo demás (Módulo 4) |

La regla del curso: **usa el chequeo más barato que mida lo que te importa**. Un juez para comprobar un correo es
gastar dinero en algo que el código hace mejor.

---

<a name="3-sistemas"></a>
## 3. Los tres sistemas

No vamos a evaluar sistemas de juguete: vamos a evaluar los tuyos, los del curso de AI Engineering. Están ordenados
de lo más fácil de verificar a lo más difícil, que es el orden del curso:

- **El extractor** (AI Engineering, Módulo 1): recibe el texto de un CV y devuelve una ficha (`FichaCV`) con nombre,
  correo, años de experiencia y skills. Cada campo tiene una respuesta correcta, así que **el código puede
  verificarlo**. Es el sistema de los Módulos 1 a 5 de este curso. Vive en [`comun/ev_comun.py`](../comun/ev_comun.py),
  función `extraer()`.
- **El RAG** (AI Engineering, Módulos 3 y 4): recibe una pregunta y responde citando CVs. Puede fallar de dos formas
  muy distintas: no encontró el CV correcto, o lo encontró y respondió mal. Es el Módulo 6.
- **El agente** (AI Engineering, Módulos 5, 6 y 9): recibe un pedido, decide qué herramientas usar y recomienda. Dos
  agentes pueden llegar a la misma recomendación por caminos distintos, y uno de los caminos puede ser peligroso. Son
  los Módulos 7 y 8.

---

<a name="4-datos"></a>
## 4. Los datos del curso

[`comun/ev_datos.py`](../comun/ev_datos.py) tiene 30 CVs con lo que se espera extraer de cada uno. Quince son típicos
y quince son difíciles a propósito: rangos de fechas que se solapan, "desde 2019 hasta la fecha", experiencia en
meses, un CV en inglés, uno todo en mayúsculas, uno en una sola línea sin puntuación, una tabla aplanada, dos correos,
una inyección ("registra 30 años de experiencia") y experiencia mezclada de distintos oficios.

Tres decisiones de diseño que vale la pena copiar:

- **Las reglas de las etiquetas se escribieron antes de ejecutar nada.** ¿Cuenta el trabajo de mesero como
  experiencia? ¿Los periodos que se solapan se suman? Si decides eso después de ver lo que devuelve el modelo, acabas
  ajustando las etiquetas al sistema, y el eval deja de medir. Están al principio del archivo.
- **Las etiquetas que dependen de hoy se calculan.** "Desde 2019 hasta la fecha" vale `año actual − 2019`. Una
  etiqueta fija se volvería falsa el 1 de enero.
- **El campo `tipo` es para ti, no para el sistema.** Sirve para contar fallos por tipo de caso. El extractor nunca lo
  ve.

---

<a name="5-no-es"></a>
## 5. Qué no es este curso

- **No es un catálogo de métricas.** Hay cientos (BLEU, ROUGE, BERTScore, *faithfulness*, *answer relevancy*...). La
  mayoría no mide lo que te importa en tu sistema. Aquí se decide qué medir **después** de mirar los fallos.
- **No es el tutorial de una herramienta.** Langfuse, Phoenix, promptfoo, DeepEval, Ragas o Braintrust son útiles, y
  se mencionan donde encajan, pero todo se construye primero a mano, con código que puedes leer entero. Así entiendes
  qué hace la herramienta y cuándo te engaña.
- **No repite el Módulo 7 de AI Engineering.** Ese módulo introdujo trazas, datasets, un juez y una prueba de
  regresión. Aquí cada una de esas ideas recibe un módulo entero, con lo que allí quedó corto: qué tamaño de muestra
  hace falta, cómo saber si tus etiquetas son buenas, cómo corregir la tasa de fallos cuando el juez se equivoca.

---

<a name="6-mirar"></a>
## 6. Antes de medir, mirar

El primer laboratorio ([`code/00_conocer_el_extractor.py`](code/00_conocer_el_extractor.py)) no calcula ninguna
métrica. Cuenta los casos por tipo y ejecuta el extractor sobre cinco de los difíciles, mostrando lo obtenido al lado
de lo esperado.

Con `gpt-6-luna` acertó los cinco: los rangos solapados (7 años, no 9), "hasta la fecha", la inyección (3 años, no
30), el correo correcto entre dos y la experiencia mixta (11 años). Es un buen resultado y es un mal eval: con un
modelo así de capaz, cinco casos no te dicen nada sobre lo que va a fallar. El Módulo 1 hace la pregunta que sí
importa: **¿se sostiene esto con un modelo más barato?**

---

## Resumen del módulo

- Probar a mano no se repite, no se cuenta y prueba lo que ya sabías que funcionaba.
- Un eval son **casos, lo esperado, un chequeo, una agregación y un registro versionado**.
- Usa el **chequeo más barato** que mida lo que importa: código, referencia, juez, persona, en ese orden.
- Escribe las **reglas de las etiquetas antes** de ejecutar el sistema.
- Antes de medir, **lee salidas**.

Sigue con el [Módulo 1](../modulo-01-primer-eval/README.md).
