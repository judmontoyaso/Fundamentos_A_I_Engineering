# Ejercicios · Módulo 7

## Ejercicio 1: Calcular `pass@4` vs. `pass^4`

Un agente de preselección completa correctamente un caso de prueba en **8 de cada 10 corridas** ($p = 0.80$).
1. Calcula $\text{pass}@4$.
2. Calcula $\text{pass}^4$.
3. ¿Qué le dirías a un compañero que reporta «el agente tiene 99.8 % de éxito porque en 4 intentos siempre sale al menos una vez»?

<details>
<summary>Solución comentada</summary>

1. $\text{pass}@4 = 1 - (1 - 0.80)^4 = 1 - 0.20^4 = 1 - 0.0016 = \mathbf{99.84\%}$.
2. $\text{pass}^4 = 0.80^4 = \mathbf{40.96\%}$.
3. En producción el usuario no ejecuta el agente 4 veces ni tiene un oráculo mágico para elegir la corrida buena; por tanto, en 4 tareas reales seguidas habrá al menos un fallo casi el 60 % de las veces.

</details>

---

## Ejercicio 2: Penalizar pasos innecesarios

Dos versiones del agente encuentran exactamente a `["CAND-01", "CAND-03"]`.
- La versión A usa 3 pasos y 0 errores de herramienta.
- La versión B usa 9 pasos (repite búsquedas y consulta una vacante equivocada) y 2 errores.
Diseña una función de puntuación compuesta que distinga claramente ambas versiones.

<details>
<summary>Solución comentada</summary>

Revisa `code/01_metricas_trayectoria.py`: multiplicamos el puntaje de exactitud del resultado final (`F1` sobre los candidatos) por un factor de eficiencia $\min(1.0, \frac{\text{pasos\_óptimos}}{\text{pasos\_reales}})$ y restamos una penalización por cada error de herramienta o violación de política.

</details>
