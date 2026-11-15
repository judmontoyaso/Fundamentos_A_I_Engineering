# Módulo 7 · Evaluar agentes: trayectorias, pass@k y pass^k

En una llamada simple a un LLM basta con evaluar la respuesta final. En un agente, **dos corridas pueden llegar a la misma respuesta final, pero una lo hizo en 3 pasos limpios y la otra dio 9 vueltas erráticas y borró un registro por el camino**. Por eso un agente se evalúa en dos niveles simultáneos:

1. **Resultado final (*Outcome*)**: ¿la terna de candidatos devuelta coincide con el conjunto verdad (`ground truth`) y respeta todas las restricciones de la vacante?
2. **Calidad de la trayectoria (*Trajectory*)**:
   - **Eficiencia de pasos**: $\text{Eficiencia} = \frac{\text{pasos\_óptimos}}{\text{pasos\_reales}}$.
   - **Tasa de llamadas inválidas**: proporción de invocaciones a herramientas que devolvieron error de esquema o de negocio.
   - **Cumplimiento de invariantes**: cero violaciones de enfriamiento, presupuesto o seguridad.

![Módulo 7 · Evaluación de trayectorias de agentes y comparación entre pass@k y pass^k](/infografias/agentes-m7-evaluacion-pass-hat-k.png)

---

## La diferencia crítica entre `pass@k` y `pass^k`

En generación de código competitiva se suele usar $\text{pass}@k$: la probabilidad de que **al menos 1 de $k$ intentos** funcione ($1 - (1 - p)^k$).

Pero en un agente en producción que atiende a un usuario real, **no tienes $k$ intentos para ver si uno sale bien**: necesitas que el agente sea consistente **todas las veces** que un cliente lo ejecuta. Para eso usamos $\text{pass}^k$ (*pass-hat-k*, introducida en el benchmark $\tau$-bench):

$$\text{pass}^k = p^k$$

Si tu agente acierta el $75\%$ de las veces en una sola corrida ($p = 0.75$):
- $\text{pass}@5 = 1 - 0.25^5 = 99.9\%$ (parece casi perfecto si solo miras si «alguna vez» lo logra).
- $\text{pass}^5 = 0.75^5 = \mathbf{23.7\%}$ (la probabilidad de que 5 ejecuciones seguidas en producción salgan bien sin fallar ninguna).

En producción empresarial, la métrica que importa es $\text{pass}^k$.
