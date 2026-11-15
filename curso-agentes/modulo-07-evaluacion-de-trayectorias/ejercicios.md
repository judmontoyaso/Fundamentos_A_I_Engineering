# Módulo 7 · Ejercicios

---

### Ejercicio 1 — Por qué promediar `pass^k` por tarea no es igual a elevar el promedio global
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

### Ejercicio 2 — Penalizar la eficiencia cuando se violan invariantes
Modifica `evaluar_corrida` en `code/01_metricas_trayectoria.py` para que si `violaciones_politica_sin_verificar` no está vacía o `exact_match` es `False`, `eficiencia_trayectoria` sea automáticamente `0.0` (evitando que un agente que se salta pasos obligatorios parezca «más eficiente que el óptimo»).

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
