# Módulo 3 · Presupuesto de contexto, poda y memoria

> **Objetivo:** controlar el crecimiento cuadrático de tokens de entrada mediante poda selectiva de observaciones antiguas (*observation masking*) e implementar memoria episódica persistente entre ejecuciones.

En una aplicación de chat tradicional, el usuario escribe mensajes breves. En un agente con herramientas, **cada paso inyecta al historial JSONs de fichas, resultados de búsquedas y trazas de auditoría**. Como en cada turno el LLM vuelve a leer toda la conversación desde el paso 1, una observación verbosa de $T$ tokens añadida en el paso 2 se vuelve a pagar en los pasos 3, 4, 5… hasta el paso $N$:

$$\text{Tokens facturados} = \sum_{k=1}^{N} \left(\text{Prompt base} + \sum_{i=1}^{k} \text{Observación}_i\right) = \mathcal{O}(N^2)$$

Además del costo económico, acumular docenas de fichas crudas en la misma ventana degrada la atención del modelo y provoca que mezcle atributos de un candidato descartado en el paso 3 con el candidato evaluado en el paso 10.

![Módulo 3 · Presupuesto de contexto, poda de observaciones (observation masking) y memoria episódica](/infografias/agentes-m3-poda-contexto-memoria.png)

---

## 1. Poda de observaciones antiguas (`01_podar_observaciones.py`)

La técnica más efectiva y segura para domar el contexto de un agente no es pedirle a otro LLM que «resuma la conversación en prosa» (lo cual es lento, caro y suele borrar códigos exactos como `CAND-03`), sino **enmascarar o podar determinísticamente las salidas de herramientas antiguas (`role == "tool"`)**:

1. **En el estado/checkpoint** se conserva el historial íntegro para auditoría.
2. **En la vista que se envía al modelo en cada turno (`podar_observaciones_antiguas`)** se mantienen intactas únicamente las últimas $K = 2$ observaciones de herramientas; las anteriores se reemplazan por su versión compacta sin campos redundantes ni volcados largos.

En `code/01_podar_observaciones.py` medimos el impacto real sobre los 11 pasos de `VAC-101` cuando `consultar_ficha_candidato` incluye metadatos verbosos de auditoría empresarial:

| Modo de contexto | Pasos | Tokens de entrada acumulados | Tokens de salida | Costo USD | Terna entregada | Ahorro en entrada |
|---|---|---|---|---|---|---|
| **Sin poda (`podar=False`)** | 11 | `30.525` | `224` | `$0.0126` | `["CAND-01", "CAND-03"]` | — |
| **Con poda (`podar=True`, `K=2`)** | 11 | `15.729` | `224` | `$0.0066` | `["CAND-01", "CAND-03"]` | **-48.5 %** |

El agente toma **exactamente las mismas decisiones** y llega a la misma terna (`exacta: true`), pero reduce casi a la mitad los tokens de entrada facturados.

---

## 2. Memoria episódica entre ejecuciones (`02_memoria_episodica.py`)

La ventana de contexto (con o sin poda) muere cuando termina la ejecución. Si tras revisar la primera terna de `VAC-101` (`["CAND-01", "CAND-03"]`) el gerente de ingeniería corrige al equipo:

> *"Para `VAC-101` es indispensable que quien entre tenga experiencia práctica en `FastAPI`, aunque no hubiera quedado escrito en la ficha original de la vacante."*

No queremos reentrenar el modelo ni editar el código fuente por cada preferencia operativa de una vacante. En `code/02_memoria_episodica.py` implementamos `MemoriaEpisodica` sobre `salida/m3_memoria_episodica.json`:

1. **Sesión 1 (sin recuerdos previos)**: el agente busca las 4 habilidades base de `VAC-101` (`["Python", "SQL", "RAG", "Evaluación de LLMs"]`) y entrega `["CAND-01", "CAND-03"]`.
2. **Registro del aprendizaje humano**: se persiste `mem.registrar_aprendizaje("VAC-101", "REQUISITO_EXTRA: FastAPI", origen="revisión_humana_sesion_1")`.
3. **Sesión 2 (con recuerdo recuperado por `vacante_id`)**: al iniciar la corrida para `VAC-101`, el controlador inyecta las reglas asociadas a esa vacante en el mensaje de sistema. El agente incluye `"FastAPI"` en `buscar_candidatos` y estrecha la terna a `["CAND-01"]` (*Valeria Ríos*, la única candidata elegible que domina `FastAPI`).
