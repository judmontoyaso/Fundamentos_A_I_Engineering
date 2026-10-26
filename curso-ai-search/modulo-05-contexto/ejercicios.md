# Módulo 5 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Los laboratorios usan el contexto largo: cada
corrida completa son decenas de miles de tokens. Reduce las preguntas mientras pruebas.

---

### Ejercicio 1 — El tamaño justo
Añade "top 10", "top 25" y "top 40" a `01`. Dibuja (o imprime) aciertos y tokens contra k. ¿Dónde está el punto en que
añadir más CVs deja de ayudar?

### Ejercicio 2 — Pedirle que sea exhaustivo
Cambia el prompt del contexto largo para pedir exhaustividad de forma explícita ("revisa cada CV uno por uno; antes de
responder, lista los que cumplen con su número de CV"). ¿Mejoran las listas? ¿Cuántos tokens de salida cuesta?

### Ejercicio 3 — Un modelo barato con todo el corpus
Repite `01` con `gpt-5.4-nano` como generador. ¿Cuánto cae el contexto largo? ¿Y el top 15?

### Ejercicio 4 — Las cuentas con código
Responde las tres preguntas de cuenta con código sobre `as_fichas` (por ejemplo, `sum(f["lidera"] for f in fichas.values())`).
¿Aciertan? ¿Cuánto tarda y cuánto cuesta frente al contexto largo?

### Ejercicio 5 — Una pregunta que sí necesite contexto largo
Escribe una pregunta que obligue a leer muchos CVs con atención y no se pueda responder con filtros (por ejemplo,
"¿qué combinación de tecnologías es la más frecuente entre los ingenieros de datos?"). ¿Qué contexto gana ahí?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Lo habitual es que los aciertos suban rápido hasta k ≈ 10-15 y se aplanen (o bajen) después, mientras los tokens
crecen lineales. El punto justo depende del tamaño de las respuestas: si una lista puede tener 16 candidatos, un k de 15
no alcanza. Por eso k se elige midiendo con tus preguntas, y para listas largas la respuesta correcta no es subir k sino
cambiar de herramienta (fichas + código).

**2.** Pedir que liste los CVs que cumplen antes de responder suele mejorar algo las listas (es un razonamiento
explícito, como el juez del Módulo 5 de Evals con su lista de afirmaciones), a cambio de muchos más tokens de salida.
Rara vez las hace exactas siempre con 119 CVs: sigue siendo un recorrido largo hecho por un modelo.

**3.** El contexto largo suele caer bastante más con el modelo pequeño (le cuesta más mantener la atención sobre 119
CVs); el top 15 cae menos. Es otra cara del Módulo 3: **el contexto largo exige un modelo capaz**, y un buen recuperador
permite usar uno barato.

**4.** Con las fichas, las cuentas salen exactas (18 líderes, 10 analistas de seguridad, 20 juniors) en milisegundos y sin
costo, porque las fichas coinciden con los hechos. Es el argumento del Módulo 6: para contar, consulta datos; no los
leas.

**5.** En una pregunta de "patrones" sobre un grupo (la combinación más frecuente, qué tienen en común los seniors de
datos), el contexto largo filtrado (todos los ingenieros de datos, no solo el top 15) suele ganar: hay que ver el grupo
completo para responder. La mejor opción es una mezcla: filtrar con las fichas para quedarse con el grupo y darle al
modelo el grupo entero.

</details>
