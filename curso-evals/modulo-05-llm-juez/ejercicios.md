# Módulo 5 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Corre `03` antes que `04`: `04` lee la calibración que
guarda `03`.

---

### Ejercicio 1 — Veredicto primero
Crea un `v3b` igual a `v3` pero con el campo `inventa` **antes** de `afirmaciones` en el schema. Córrelo tres veces en
desarrollo. ¿Cambian el TPR y el TNR? ¿Las afirmaciones que lista justifican el veredicto o lo contradicen?

### Ejercicio 2 — Otro modelo como juez
Calibra el juez v3 con `gpt-4.1-mini` (pasa `modelo=` en `juzgar()`) en desarrollo y en prueba. ¿Es más o menos
paranoico? Con su TPR y su TNR, ¿cambia la tasa corregida de los perfiles v1?

### Ejercicio 3 — ¿Qué invenciones se escapan?
Cuenta los aciertos del juez por `origen` (real, insertada obvia, sutil, numérica) en las tres corridas de prueba.
¿Detecta igual las numéricas ("12 años" en vez de 9) que las obvias? ¿Qué harías para detectar mejor las que se le
escapan?

### Ejercicio 4 — Rogan-Gladen a mano
Un juez con TPR 90 % y TNR 80 % marca el 30 % de 200 perfiles. Calcula la tasa corregida. ¿Qué pasaría con la
estimación si el TNR fuera 55 %?

### Ejercicio 5 — Tus etiquetas como verdad
Si anotaste en el Módulo 4, usa tus etiquetas en lugar de las del autor para los 30 perfiles reales (los "no pasa" por
invención). ¿Cambian el TPR y el TNR del juez en los ítems reales?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Con el veredicto primero, el modelo decide antes de enumerar y la lista se convierte en una justificación. Lo
habitual es que el TNR baje y que aparezcan listas donde todas las afirmaciones están "respaldadas" y aun así el
veredicto es "inventa". Si lo ves, tienes la prueba de por qué el orden del schema importa.

**2.** Un modelo pequeño como juez suele ser más barato y peor calibrado, a veces en la dirección contraria (deja pasar
invenciones sutiles). Lo importante es que la corrección de Rogan-Gladen usa **sus** TPR y TNR: con un juez distinto,
la tasa observada cambia y la corregida debería quedar en un rango compatible. Si no, alguno de los dos juicios está
mal calibrado.

**3.** Es frecuente que las numéricas sean las más difíciles: "12 años" parece una afirmación normal y el juez tiene que
contrastarla con el CV. Para eso, mejor que un juez es **código**: extraer el número de años del perfil y compararlo
con la ficha (Módulo 1). Regla general: lo que se puede comprobar con código, se saca del juez.

**4.** (0.30 + 0.80 − 1) / (0.90 + 0.80 − 1) = 0.10 / 0.70 ≈ **14 %**. Con TNR 55 %: (0.30 + 0.55 − 1) / (0.90 + 0.55 − 1)
= −0.15 / 0.45 < 0, que se recorta a 0 %. Un juez que da tantas falsas alarmas no permite distinguir "nadie inventa"
de "algunos inventan": el 30 % observado se explica entero por sus errores.

**5.** Si tus etiquetas coinciden con las del autor en los 4 perfiles que inventan, el TPR no cambia. Lo que suele
cambiar es el TNR: si marcaste como "no pasa por invención" algún perfil que el autor dejó pasar (por ejemplo, el #9
"experto en Jenkins"), el juez "acertaba" en ese caso según tú. Es la conexión entre los dos módulos: **el juez se
calibra contra personas**, y si las personas no se ponen de acuerdo, la calibración hereda ese ruido.

</details>
