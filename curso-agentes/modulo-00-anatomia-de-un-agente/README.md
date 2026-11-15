# Módulo 0 · Cuándo usar (y cuándo no usar) un agente

> **Objetivo:** distinguir con criterio de ingeniería cuándo un problema exige un bucle autónomo de herramientas y cuándo basta un flujo determinista, e implementar un controlador con presupuesto estricto de pasos, tokens y dinero fuera del modelo.

Un error frecuente al pasar de prototipos a producción es convertir un problema que se resuelve con tres funciones deterministas y una llamada estructurada a un LLM en un **agente autónomo de bucle abierto**. Cada vez que le entregas al modelo la decisión de *qué herramienta invocar a continuación* y *cuándo detenerse*, pagas tres costos operativos:

1. **Propagación multiplicativa del error**: si en cada paso el modelo elige la acción correcta con probabilidad $p = 0.92$, tras 11 pasos la probabilidad de completar la trayectoria sin tropiezos cae a $0.92^{11} \approx 0.40$ (40 %).
2. **Varianza en latencia y facturación**: un workflow fijo en código tarda milisegundos o un número fijo de llamadas; un bucle abierto sin freno puede entrar en una espiral de reintentos y multiplicar por 10 el consumo de tokens de entrada.
3. **Superficie de efectos secundarios**: un agente con herramientas de escritura (`agendar_entrevista`, `enviar_oferta`) puede disparar acciones irreversibles si malinterpreta una observación intermedia.

![Módulo 0 · La escalera de autonomía y el riesgo compuesto por paso](/infografias/agentes-m0-escalera-autonomia.png)

---

## 1. La escalera de autonomía

Antes de escribir `while True:`, ubica tu caso de uso en el nivel más bajo de la escalera que resuelva el problema:

| Nivel | Arquitectura | Quién gobierna el flujo | Llamadas al LLM | Caso de uso ideal en nuestro ATS |
|---|---|---|---|---|
| **1. Extracción estructurada** | `prompt → JSON Schema` | Código (1 paso fijo) | 1 | Extraer años de experiencia, inglés y tecnologías desde el texto de un CV |
| **2. Workflow / DAG fijo** | Secuencia, ruteo o paralelo en Python | Código ($N$ pasos fijos) | $1\text{–}3$ | Leer vacante → filtrar candidatos con SQL/reglas → redactar resumen comparativo |
| **3. Agente acotado de lectura** | Bucle ReAct con herramientas `GET` y presupuesto duro | El modelo propone; el controlador limita | Variable ($4\text{–}12$) | Explorar un ATS cuando no sabes de antemano qué filtros arrojarán candidatos suficientes |
| **4. Agente con estado y efectos** | Máquina de estados + checkpoints + aprobación humana (HITL) | Híbrido: el modelo explora, la máquina de estados valida transiciones | Variable + pausa | Preseleccionar candidatos, verificar elegibilidad normativa y agendar entrevistas reales |

---

## 2. El entorno del curso: el ATS y la interfaz dual `Modelo`

Para que puedas medir y depurar **el controlador del agente** sin gastar saldo en cada prueba (y luego contrastarlo con un LLM real en vivo), todos los laboratorios del curso se apoyan en dos módulos compartidos en `comun/`:

- **`comun/ag_comun.py`**: contiene las 2 vacantes (`VAC-101` híbrida en Bogotá para *Senior AI Engineer* y `VAC-102` remota para *Platform / MLOps Engineer*), los 8 candidatos (`CAND-01` a `CAND-08`), las reglas de negocio deterministas en `motivos_bloqueo(vacante, candidato)` y la verdad esperada `terna_correcta(vacante_id)`:

| Vacante | Candidatos que cumplen habilidades + sueldo | Quiénes quedan bloqueados al verificar elegibilidad | Terna correcta (`terna_correcta`) |
|---|---|---|---|
| `VAC-101` | `CAND-01`, `CAND-03`, `CAND-04`, `CAND-07` | `CAND-04` (1 año exp., inglés A2 y CV con inyección), `CAND-07` (inglés B1 < B2 y vive en Medellín siendo híbrida en Bogotá) | `["CAND-01", "CAND-03"]` |
| `VAC-102` | `CAND-05`, `CAND-08` | `CAND-08` (último contacto hace 45 días < 90 días de enfriamiento obligatorio) | `["CAND-05"]` |

- **`comun/ag_modelo.py`**: define el protocolo `responder(mensajes, herramientas) -> Respuesta` con dos implementaciones intercambiables:
  - `ModeloOpenAI`: llama a la API real de OpenAI (`gpt-4.1-mini` por defecto, o el que definas en `MODELO`) cuando `OPENAI_API_KEY` está en el entorno.
  - `ModeloSimulado`: una política determinista reproducible sin red cuyos defectos se encienden por parámetro (`errata=True`, `terco=True`, `obedece_inyeccion=True`, `p_descuido=0.25`) para poner a prueba las defensas de tu controlador.

---

## 3. Workflow determinista frente a bucle de agente (`01_workflow_vs_agente.py`)

En `code/01_workflow_vs_agente.py` resolvemos la misma preselección de `VAC-101` por ambos caminos:

1. **`workflow_fijo("VAC-101")`**: aplica `motivos_bloqueo` directamente en Python sobre el catálogo estructurado. Tarda **< 0.1 ms**, hace **0 llamadas al modelo**, cuesta **$0.00 USD** y entrega `["CAND-01", "CAND-03"]`.
2. **`bucle_agente(modelo, "VAC-101")`**: el agente arranca solo con el identificador `"VAC-101"` y explora paso a paso mediante llamadas a herramientas (`obtener_vacante` → `buscar_candidatos` → 4 llamadas a `consultar_ficha_candidato` y 4 a `verificar_elegibilidad` → `entregar_terna`):

| Métrica | `workflow_fijo` (`VAC-101`) | `bucle_agente` (`VAC-101`) | `bucle_agente` (`VAC-102`) |
|---|---|---|---|
| **Pasos de ejecución** | 1 | 11 | 7 |
| **Tokens de entrada acumulados** | 0 | 16.446 | 7.862 |
| **Tokens de salida** | 0 | 224 | 153 |
| **Costo estimado (`$0.40 / $1.60` por 1M)** | `$0.0000` | `$0.0069` | `$0.0034` |
| **Terna entregada** | `["CAND-01", "CAND-03"]` | `["CAND-01", "CAND-03"]` | `["CAND-05"]` |

**Lección de diseño:** si los datos ya están normalizados y la secuencia de pasos es fija, escribe un workflow. Reserva el agente para cuando el sistema deba decidir dinámicamente qué herramienta invocar según lo que descubra en tiempo de ejecución.

---

## 4. El freno presupuestario fuera del modelo (`02_presupuesto_y_frenos.py`)

Un prompt que dice *"No hagas más de 5 pasos"* es una sugerencia; no un límite de ingeniería. Cuando un modelo entra en bucle (por ejemplo, repitiendo una búsqueda que devuelve 0 resultados), ignorará las instrucciones del prompt y consumirá saldo hasta agotar el *timeout* del servidor.

Por eso `PresupuestoAgente` vive **en el bucle de Python**, fuera del alcance del LLM, y verifica dos compuertas en cada iteración:

```python
while True:
    presupuesto.abrir_paso()  # Corta ANTES de pagar la llamada si pasos >= max_pasos
    r = modelo.responder(mensajes, esquemas)
    presupuesto.registrar(r.tokens_entrada, r.tokens_salida)  # Corta si supera max_tokens o max_costo_usd
```

Al ejecutar `code/02_presupuesto_y_frenos.py` sobre tres escenarios obtenemos:

1. **Ejecución sana (`max_pasos=16, max_tokens=30000`)**: completa en 11 pasos (`15.915` tokens de entrada) y entrega `["CAND-01", "CAND-03"]`.
2. **Modelo atascado (`crear_modelo(terco=True)` con `max_pasos=5`)**: el modelo repite `buscar_candidatos(habilidades=["Python"], max_aspiracion_usd=1000)` sin avanzar. `abrir_paso()` lanza `PresupuestoAgotado("max_pasos=5")` antes del sexto turno, conteniendo el gasto en `$0.0017 USD`.
3. **Tope de contexto (`max_tokens=1500`)**: tras el paso 3 (`2.383` tokens acumulados), `registrar()` aborta la corrida con `PresupuestoAgotado("max_tokens=1500")`.
