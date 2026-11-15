# Ejercicios · Módulo 0

## Ejercicio 1: Probabilidad compuesta de éxito en una trayectoria

Tu equipo diseña un agente que en promedio necesita **7 pasos** para completar una preselección. Hoy cada paso elige la herramienta y argumentos correctos el **90 %** de las veces.

1. Calcula la probabilidad de que una ejecución de 7 pasos termine sin ningún fallo intermedio.
2. Si logras reemplazar los primeros 4 pasos por un workflow determinista en código (con confiabilidad del 99.5 % en bloque) y dejas al agente solo los últimos 3 pasos exploratorios (al 90 % cada uno), ¿cuál es la nueva tasa de éxito de punta a punta?

<details>
<summary>Solución comentada</summary>

1. Con 7 pasos autónomos independientes al 90 %:
   - `P(éxito) = 0.90⁷ ≈ 0.4783` (**47.8 %**)
   - Más de la mitad de las corridas fallan o requieren recuperación.
2. Con los primeros 4 pasos fijados en código (`0.995`) y solo 3 pasos autónomos (`0.90³`):
   - `P(éxito) = 0.995 × 0.90³ = 0.995 × 0.729 ≈ 0.7254` (**72.5 %**)
   - Reducir el número de decisiones abiertas del modelo sube la confiabilidad casi 25 puntos porcentuales sin cambiar de modelo.

</details>

---

## Ejercicio 2: Detector de bucle repetitivo

Modifica `PresupuestoAgente` para que rechace una llamada si el agente intenta ejecutar exactamente la misma herramienta con los mismos argumentos más de una vez en la misma trayectoria.

<details>
<summary>Solución comentada</summary>

Basta con guardar un `set` de hashes `(herramienta, argumentos_json_ordenados)` usando `clave_idempotencia(herramienta, argumentos)` de `comun/ag_comun.py`. Si la clave ya está en `vistos`, devolvemos al modelo un mensaje explícito: `"Ya ejecutaste esta consulta con los mismos argumentos. Usa el resultado anterior o cambia los filtros."` sin gastar otra llamada al servicio externo.

</details>
