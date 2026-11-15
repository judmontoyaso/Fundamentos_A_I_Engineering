# Módulo 0 · Cuándo usar (y cuándo no usar) un agente

Un error frecuente en ingeniería de IA es convertir un problema que se resuelve con tres funciones deterministas y una llamada a un LLM en un **agente autónomo con bucle abierto**. Cada vez que le entregas al modelo la decisión de *qué hacer a continuación* y *cuándo detenerse*, introduces tres riesgos:

1. **Propagación multiplicativa del error**: si cada paso tiene una probabilidad de acierto de `p = 0.92`, tras 8 pasos la probabilidad de completar la trayectoria sin errores cae a `0.92⁸ ≈ 0.51` (51 %).
2. **Varianza en costo y latencia**: un flujo fijo tarda siempre ~1.2 segundos; un agente en bucle puede tardar 1.5 segundos o 28 segundos si entra en una espiral de reintentos.
3. **Superficie de efectos secundarios**: un agente con herramientas de escritura puede modificar registros equivocados si malinterpreta una observación intermedia.

![Módulo 0 · La escalera de autonomía y el riesgo compuesto por paso](/infografias/agentes-m0-escalera-autonomia.png)

---

## La escalera de autonomía

Antes de escribir un bucle `while not terminado`, ubica tu problema en esta tabla:

| Nivel | Arquitectura | Quién decide el flujo | Cuándo usarlo |
|---|---|---|---|
| **1. Llamada estructurada** | `prompt -> JSON validado` | Código (1 paso) | Clasificar, extraer campos de un CV, normalizar una consulta |
| **2. Workflow / DAG** | Cadena, ruteo o paralelo fijo | Código (N pasos fijos) | El orden de las etapas se conoce de antemano (parsear → buscar → rerankear → resumir) |
| **3. Agente acotado** | Bucle con herramientas de solo lectura + presupuesto duro | El modelo dentro de límites estrictos | No sabes de antemano cuántas consultas o cruces de datos harán falta para responder |
| **4. Agente con estado y efectos** | Máquina de estados + checkpoints + aprobación humana | Híbrido (modelo explora, grafo gobierna transiciones críticas) | El sistema debe investigar, proponer una acción sobre sistemas externos y ejecutarla con garantías |

---

## El impuesto de la autonomía y los frenos obligatorios

Ningún agente debe salir a producción sin un **presupuesto de ejecución** (`PresupuestoAgente`) verificado fuera del modelo, en código Python:

- `max_pasos`: número máximo de iteraciones del bucle (p. ej. 8).
- `max_tokens`: techo acumulado de tokens de entrada y salida.
- `max_costo_usd`: límite monetario por tarea.
- **Detección de bucles repetidos**: si el modelo invoca la misma herramienta con los mismos argumentos dos veces seguidas, el controlador corta o inyecta una advertencia sin volver a ejecutar la herramienta.

En los scripts de este módulo comparamos un workflow determinista frente a un agente exploratorio sobre las vacantes y candidatos de nuestro ATS, midiendo pasos, latencia y costo.
