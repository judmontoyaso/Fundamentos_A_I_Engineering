# Ejercicios · Módulo 3

## Ejercicio 1: Costo cuadrático de un historial sin podar

Un agente ejecuta 10 pasos. En cada paso la herramienta devuelve **1.500 tokens** de observación y el system prompt base mide **1.000 tokens**.

1. ¿Cuántos tokens de entrada totales se envían al modelo a lo largo de los 10 pasos si nunca podas las observaciones antiguas?
2. ¿Cuántos tokens de entrada totales se envían si solo mantienes completas las últimas 2 observaciones y reemplazas cada observación anterior por un resumen de 60 tokens?

<details>
<summary>Solución comentada</summary>

1. **Sin podar**:
   En el paso $k$ (de 1 a 10) entran $1000 + 1500 \times (k-1)$ tokens.
   Total $= 10 \times 1000 + 1500 \times \frac{9 \times 10}{2} = 10.000 + 67.500 = \mathbf{77.500\text{ tokens}}$.
2. **Con poda de observaciones ($K=2$ completas, resto a 60 tokens)**:
   A partir del paso 4 nunca hay más de $2 \times 1500 = 3000$ tokens de observaciones recientes más unos pocos cientos de tokens de resúmenes. El total cae a **~34.200 tokens** (más de un **55 % de ahorro** y menor distracción para el modelo).

</details>

---

## Ejercicio 2: Qué nunca debe resumirse con prosa libre

¿Qué campos del ATS jamás deberían comprimirse mediante un resumen libre de LLM?

<details>
<summary>Solución comentada</summary>

Identificadores exactos (`CAND-01`, `VAC-101`), montos numéricos (`aspiracion_usd`), fechas y banderas booleanas de elegibilidad. Esos datos deben copiarse de forma determinista al estado tipado del agente antes de enmascarar la observación cruda.

</details>
