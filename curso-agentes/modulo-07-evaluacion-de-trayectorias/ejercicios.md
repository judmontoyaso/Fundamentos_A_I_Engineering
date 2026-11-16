# Módulo 7 · Ejercicios

---

### Ejercicio 1. Por qué promediar `pass^k` por tarea no es igual a elevar el promedio global
En `code/02_pass_k_vs_pass_hat_k.py` calculamos `estimar_pass_hat_k(n, c, k)` **dentro de cada vacante** y luego promediamos entre `VAC-101` y `VAC-102`. Imagina que tienes 2 tareas: en la Tarea A tu agente acierta `8/8` veces (`100 %`) y en la Tarea B acierta `0/8` veces (`0 %`). La tasa global promedio es `p = 0.50`. ¿Cuánto vale $(0.50)^3$ frente al promedio real de `pass^3` por tarea?

<details>
<summary>Ver solución</summary>

- Si elevaras erróneamente la media global al cubo: $(0.50)^3 = 0.125$ (`12.5 %`).
- Calculando correctamente por tarea como en $\tau$-bench:
  - Tarea A (`8/8`): $\text{pass}\hat{\mkern6mu}3 = 1.0$.
  - Tarea B (`0/8`): $\text{pass}\hat{\mkern6mu}3 = 0.0$.
  - Promedio real de $\text{pass}\hat{\mkern6mu}3 = (1.0 + 0.0) / 2 = 0.500$ (`50.0 %`).

La desigualdad de Jensen ($\mathbb{E}[p_i^k] \ge (\mathbb{E}[p_i])^k$) explica por qué siempre debes medir las $n$ corridas por cada caso del benchmark y promediar al final.
</details>

---

### Ejercicio 2. Penalizar la eficiencia cuando se violan invariantes
Modifica `evaluar_corrida` en `code/01_metricas_trayectoria.py` para que `eficiencia_trayectoria` valga `0.0` cuando la terna no es exacta o hay candidatos sin verificar. Así una trayectoria incorrecta no puede sacar una buena nota de eficiencia, aunque haya usado pocos pasos.

<details>
<summary>Ver solución</summary>

```python
eficiencia = (
    round(min(1.0, pasos_optimos / max(len(pasos), 1)), 3)
    if (obtenida == esperada and not sin_verificar)
    else 0.0
)
```
</details>

---

### Ejercicio 3. Intervalo para pass^k
Con 8 corridas y 3 éxitos, `pass^1 = 0,375`. Calcula un intervalo de confianza del 95 % para la tasa de éxito con el
método de Wilson. ¿Cuántas corridas necesitarías para que el intervalo mida menos de ±10 puntos?

<details>
<summary>Ver solución</summary>

El intervalo de Wilson con 3/8 va aproximadamente de 0,14 a 0,69: enorme. El ancho se reduce con la raíz de $n$; para
una tasa cerca de 0,4 hacen falta del orden de 90 corridas para bajar a ±10 puntos. En la práctica se reparte entre
más tareas y menos corridas por tarea (por ejemplo, 30 tareas × 5 corridas), y se reporta el intervalo junto al
promedio.
</details>

---

### Ejercicio 4. Acciones no autorizadas como métrica
Añade a `evaluar_corrida` la métrica `acciones_no_autorizadas`: llamadas a herramientas de nivel 2 sin aprobación.
Usa una corrida del escenario sin defensas del módulo 6. ¿Qué dice la evaluación si solo miras exactitud?

<details>
<summary>Ver solución</summary>

La terna de ese escenario es exacta (`CAND-01`, `CAND-03`), así que exactitud y F1 dan 1,0. La métrica nueva cuenta 1
(`enviar_oferta` a `CAND-04`). Cualquier valor mayor que 0 debe hacer fallar la evaluación, sin importar la exactitud:
es la diferencia entre un agente correcto y uno seguro.
</details>
