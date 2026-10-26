# Módulo 4 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). El 1 es el más importante del módulo.

---

### Ejercicio 1 — Tu acuerdo con el autor
Etiqueta los 30 perfiles en **Anotar (tu turno)**, sin mirar `m4_etiquetas_autor.py`. Corre `01`. ¿Cuál es tu kappa
con el autor? ¿En qué perfiles difieren? Para cada desacuerdo, lee tu nota y la del autor: ¿es una frontera de la guía,
un descuido de alguno de los dos o una diferencia de criterio legítima?

### Ejercicio 2 — ¿Quién se parece más a quién?
Con tus etiquetas, compara también tu acuerdo con el anotador LLM con guía v3 (adapta `comparar()` para que use tus
etiquetas como referencia). ¿Estás más cerca del autor o del LLM? ¿Qué dice eso de la frontera "frases de orientación"?

### Ejercicio 3 — Escribe la guía v5
A partir de tus desacuerdos con el autor (o, si no anotaste, de los del LLM con v3), escribe una aclaración más para la
guía. Pruébala con el anotador LLM dos veces. ¿Sube el kappa? ¿Cambia el número de "no pasa"?

### Ejercicio 4 — Kappa a mano
Dos anotadores etiquetan 20 perfiles. A dice "no pasa" en 4, B en 6, y coinciden en 3 de esos "no pasa". Calcula sin
código el acuerdo observado, el acuerdo esperado por azar y el kappa.

### Ejercicio 5 — Una escala del 1 al 5
Cambia el anotador LLM para que puntúe cada perfil del 1 al 5 en vez de sí o no, y córrelo dos veces. ¿Cuántos perfiles
reciben la misma puntuación en las dos corridas? ¿Y si conviertes la escala en sí o no (4-5 = pasa)?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** No hay una respuesta única: el entregable es tu kappa y la lectura de cada desacuerdo. Lo esperable es que
coincidas con el autor en los fallos claros (contacto, certificación inventada) y que los desacuerdos caigan en los
casos que el autor marcó como dudosos (#5, #9, #20, #25). Si tu kappa supera ~0.6, la guía v2 + la aclaración funcionan
entre personas; si queda por debajo, hay otra frontera sin decidir, y ese es el ejercicio 3.

**2.** Si coincides más con el autor, el LLM aplica un estándar más estricto que el de las personas, y en el Módulo 5
eso será un juez con demasiados falsos "no pasa". Si coincides más con el LLM, quizá el autor es demasiado permisivo con
el relleno, y lo que habría que cambiar son las etiquetas del autor. En los dos casos, decide la frontera y escríbela.

**3.** Una aclaración posible: "Las frases sobre a qué se orienta el candidato o qué tipo de trabajo hace, si se deducen
del cargo y las tecnologías del CV, pasan". Lo que importa es medir: dos corridas, el kappa y el número de "no pasa".
Si la frase no mueve nada, quítala: una guía larga también cansa a las personas.

**4.** Coinciden en 3 "no pasa". A dice "pasa" en 16 y B en 14; los dos dicen "pasa" en 20 − 4 − 6 + 3 = 13. Acuerdo
observado = (3 + 13) / 20 = 0.80. Por azar: P(A no pasa) = 0.20, P(B no pasa) = 0.30, así que pe = 0.20 × 0.30 + 0.80 ×
0.70 = 0.06 + 0.56 = 0.62. Kappa = (0.80 − 0.62) / (1 − 0.62) = 0.18 / 0.38 ≈ **0.47**: moderado, aunque el acuerdo sea
del 80 %.

**5.** Lo habitual es que muchos perfiles cambien de puntuación entre corridas (un 3 que pasa a 4), mientras que la
versión binaria es bastante más estable. Las escalas reparten la incertidumbre en más categorías y hacen más difícil el
acuerdo, también el de un modelo consigo mismo. Si necesitas matices, usa varias preguntas binarias (¿inventa? ¿tiene
contacto?), no una escala.

</details>
