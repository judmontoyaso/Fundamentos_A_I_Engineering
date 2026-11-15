# Módulo 7 · Evaluar agentes: trayectorias, pass@k y pass^k

> **Objetivo:** evaluar agentes simultáneamente por su resultado final (*Outcome*) y por la calidad de su trayectoria (*Trajectory*), y calcular empíricamente la brecha entre `pass@k` y `pass^k` (metodología $\tau$-bench) sobre múltiples corridas.

En una llamada única a un LLM basta con comparar la salida final contra la referencia. En un agente autónomo, **dos ejecuciones pueden devolver exactamente la misma terna final `["CAND-01", "CAND-03"]`, pero una lo logró en 11 pasos limpios y la otra dio 17 vueltas con errores de esquema o incluyó candidatos por azar sin haber verificado su elegibilidad**.

Por eso la evaluación de agentes en producción mide siempre dos planos ortogonales:
1. **Evaluación de resultado (*Outcome*)**: Precisión, Recall, $F_1$ y coincidencia exacta (*Exact Match*) frente a `terna_correcta(vacante_id)`.
2. **Evaluación de trayectoria (*Trajectory*)**: eficiencia de pasos ($\text{pasos\_óptimos} / \text{pasos\_reales}$), tasa de recuperación ante errores de herramientas y cumplimiento estricto de invariantes (cero candidatos entregados sin haber llamado antes a `verificar_elegibilidad`).

![Módulo 7 · Evaluación de trayectorias de agentes y comparación entre pass@k y pass^k](/infografias/agentes-m7-evaluacion-pass-hat-k.png)

---

## 1. Métricas de resultado y salud de trayectoria (`01_metricas_trayectoria.py`)

Para `VAC-101`, donde `buscar_candidatos` devuelve 4 candidatos, la trayectoria óptima tiene **11 pasos** (`1` vacante + `1` búsqueda + `4 × 2` fichas y verificaciones + `1` entrega). En `code/01_metricas_trayectoria.py` comparamos tres corridas reales sobre `VAC-101`:

| Corrida evaluada | `exact_match` | `f1_terna` | Pasos reales | Eficiencia (`11 / pasos`) | Errores de herramienta | ¿Se recuperó? | Violaciones de política (sin verificar) |
|---|---|---|---|---|---|---|---|
| **1. Modelo limpio** | `true` | `1.000` | `11` | **`1.000`** | `0` | — | `[]` |
| **2. Modelo con errata (`errata=True`)** | `true` | `1.000` | `12` | **`0.917`** | `1` | `true` | `[]` |
| **3. Modelo descuidado (`p_descuido=0.6`)** | `false` | `0.667` | `8` | `1.375` *(engañoso: saltó pasos)* | `0` | — | `["CAND-01", "CAND-03", "CAND-07"]` |

Observa por qué **nunca debes mirar una sola métrica aislada**: la corrida 3 dio menos pasos (`8` en vez de `11`), pero lo hizo porque se saltó `verificar_elegibilidad` en tres candidatos y coló a `CAND-07` en la terna.

---

## 2. Consistencia en producción: `pass@k` frente a `pass^k` (`02_pass_k_vs_pass_hat_k.py`)

En competencias de generación de código se popularizó la métrica $\text{pass}@k$ (Chen et al.): la probabilidad de que **al menos 1 de $k$ intentos** resuelva el problema. Con $n$ corridas totales de una tarea y $c$ corridas exitosas, su estimador insesgado es:

$$\text{pass}@k = 1 - \frac{\binom{n - c}{k}}{\binom{n}{k}}$$

Pero cuando un reclutador usa tu agente en producción, **no lanza 5 veces la tarea para quedarse con la corrida que salió bien**: necesita que el agente acierte **la primera vez, la segunda y la quinta**. Por eso el benchmark **$\tau$-bench** (Yao et al.) introdujo $\text{pass}\hat{\mkern6mu}k$ (*pass-hat-k*): la probabilidad de que **las $k$ corridas salgan todas bien**:

$$\text{pass}\hat{\mkern6mu}k = \frac{\binom{c}{k}}{\binom{n}{k}}$$

En `code/02_pass_k_vs_pass_hat_k.py` ejecutamos $N = 8$ corridas reales por vacante (`VAC-101` y `VAC-102`) comparando un agente estocástico sin guarda de estado (`p_descuido=0.25`) frente a nuestro agente con invariantes (`p_descuido=0.0`):

| Métrica (promedio en `VAC-101` y `VAC-102`) | $k = 1$ | $k = 2$ | $k = 3$ | $k = 5$ | Qué significa en producción |
|---|---|---|---|---|---|
| **Agente sin guarda (`p_descuido=0.25`) · `pass@k`** | `0.312` | `0.553` | `0.732` | **`0.938`** | Engañoso: en 5 intentos casi siempre sale bien *alguna vez* (`93.8 %`) |
| **Agente sin guarda (`p_descuido=0.25`) · `pass^k`** | `0.312` | `0.071` | `0.009` | **`0.000`** | Realidad: probabilidad del **`0.0 %`** de encadenar 5 corridas limpias seguidas |
| **Agente con invariantes (`p_descuido=0.0`) · `pass^k`** | **`1.000`** | **`1.000`** | **`1.000`** | **`1.000`** | Confiabilidad empresarial: `8/8` corridas exactas en ambas vacantes |
