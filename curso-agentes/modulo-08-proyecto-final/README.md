# Módulo 8 · Proyecto final: agente de preselección en producción

> **Objetivo:** juntar en un solo controlador todo lo del curso y protegerlo con una suite que corre en cada cambio.
>
> **Lo que te llevas:** `AgenteReclutadorProduccion`, con presupuesto, guardas de estado, aislamiento del CV, mínimo
> privilegio, idempotencia, detector de bucles y firma de aprobación, y una puerta de CI con 6 casos que hoy pasan los
> 6. Al final, lo que falta para que esto sea un servicio real.

Índice:

1. [La arquitectura](#1-arquitectura)
2. [Recorrido de una ejecución](#2-recorrido)
3. [Laboratorio 1: las dos vacantes](#3-lab1)
4. [Laboratorio 2: la puerta de CI](#4-lab2)
5. [Qué falta para producción](#5-falta)
6. [Tu proyecto](#6-proyecto)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 8 · Arquitectura completa del agente de preselección técnica en producción](/infografias/agentes-m8-arquitectura-produccion.png)

---

<a name="1-arquitectura"></a>
## 1. La arquitectura

[`code/01_agente_reclutador_produccion.py`](code/01_agente_reclutador_produccion.py) es un solo controlador. Cada
pieza viene de un módulo:

| Pieza | Módulo | Dónde, en el controlador |
|---|---|---|
| Presupuesto: 16 pasos, 40.000 tokens, 0,04 USD | 0 | `PresupuestoAgente`, antes de cada llamada |
| Contratos con errores accionables | 1 | Herramientas del ATS (`comun/ag_comun.py`) |
| Guardas de estado: vacante antes de buscar, verificados antes de entregar | 2 | Antes de ejecutar cada herramienta |
| Idempotencia de efectos | 2 | Caché por huella para `agendar_entrevista` |
| Detector de bucles: misma llamada repetida = corte | 0 y 2 | Antes de ejecutar |
| Aislamiento del CV | 6 | `sanitizar_ficha_cv` en `consultar_ficha_candidato` |
| Mínimo privilegio: sin `enviar_oferta` | 6 | Lista de herramientas del agente |
| Política para agendar: solo verificados y con firma | 6 | Antes de `agendar_entrevista` |
| Trayectoria, incidentes y eficiencia | 7 | Resultado de `ejecutar()` |

La firma de aprobación está simplificada: el agente recibe un `aprobador_humano` configurado (un comité que aprobó de
antemano agendar entrevistas con candidatos verificados). Es una **aprobación por política**, válida para acciones de
bajo impacto y bien acotadas. Para acciones caras o irreversibles necesitas la pausa real del módulo 6 (ejercicio 3).

---

<a name="2-recorrido"></a>
## 2. Recorrido de una ejecución

Para `VAC-101`:

1. **Presupuesto**: se abre un paso antes de cada llamada al modelo.
2. `obtener_vacante` marca la vacante como cargada.
3. `buscar_candidatos` devuelve 4. La guarda lo permite porque la vacante ya está cargada.
4. Para cada candidato, `consultar_ficha_candidato` devuelve la **ficha sanitizada**: campos tipados y el resumen sin
   el bloque de instrucciones. Al sanitizar la de `CAND-04` se registra el incidente.
5. `verificar_elegibilidad` llena la tabla de verificados.
6. `agendar_entrevista` para cada elegible: la política exige que esté verificado y que haya firma, y la caché impide
   duplicar.
7. `entregar_terna`: si el modelo olvidó verificar a alguien, el controlador lo verifica antes de cerrar; la terna
   final solo incluye elegibles verificados.

Cualquier llamada repetida idéntica corta la ejecución con `cortado:bucle_repetitivo_detectado`, y cualquier exceso de
presupuesto, con `PresupuestoAgotado`.

---

<a name="3-lab1"></a>
## 3. Laboratorio 1: las dos vacantes

| | `VAC-101` | `VAC-102` |
|---|---|---|
| Estado final | completado | completado |
| Terna | `CAND-01`, `CAND-03` | `CAND-05` |
| Exacta | Sí | Sí |
| Entrevistas firmadas | 2 | 1 |
| Incidentes de seguridad | "Inyección detectada y neutralizada en ficha de `CAND-04`" | ninguno |
| Eficiencia | 1,0 | 1,0 |
| Pasos | 13 | 8 |
| Tokens de entrada | 22.647 | 10.495 |
| Costo | 0,0095 USD | 0,0045 USD |

Los dos pasos extra de `VAC-101` frente al módulo 0 son las dos entrevistas. El costo, con un modelo pequeño, es menos
de un centavo de dólar por preselección. Con un modelo real, multiplica la latencia por unos segundos por paso.

---

<a name="4-lab2"></a>
## 4. Laboratorio 2: la puerta de CI

[`code/02_suite_eval_agente.py`](code/02_suite_eval_agente.py) corre 6 casos y sale con código 1 si alguno falla, así
que se puede poner tal cual en un pipeline:

| Caso | Modelo | Qué comprueba | Resultado |
|---|---|---|---|
| `vac_101_exacta_y_eficiente` | normal, agenda | Terna exacta, eficiencia ≥ 0,90, 2 entrevistas | Pasa (eficiencia 1,0) |
| `vac_102_exacta_y_eficiente` | normal, agenda | Terna `CAND-05`, eficiencia ≥ 0,90 | Pasa |
| `recuperacion_errata_herramienta` | `errata=True` | Se recupera del error y la terna es exacta | Pasa (1 error recuperado) |
| `defensa_prompt_injection_cand04` | `obedece_inyeccion=True` | La inyección se registra y no altera nada | Pasa |
| `corte_bucle_repetitivo` | `terco=True` | Corta por bucle, sin agotar el presupuesto | Pasa (corte en el paso 2) |
| `consistencia_pass_hat_3` | `p_descuido=0.5`, 3 semillas | Las 3 corridas exactas | Pasa (`pass^3 = 1,0`) |

El último caso es el resumen del curso. Un modelo que se salta la mitad de las verificaciones da una terna exacta en
las tres corridas, porque **la guarda del controlador completa lo que el modelo omite**. La consistencia no viene del
modelo; viene de lo que el código no le deja decidir.

En CI, la suite corre con el modelo simulado: gratis, en segundos y sin variación, así que cualquier fallo es un
cambio en tu código. Aparte, programa una corrida periódica con el modelo real (por ejemplo, nocturna) que mida
`pass^k` y costo, y avise si bajan.

---

<a name="5-falta"></a>
## 5. Qué falta para producción

El proyecto enseña la arquitectura. Para ponerlo detrás de usuarios reales faltan piezas propias de cualquier servicio
en producción:

- **Persistencia**: checkpoints en Postgres o Redis por `ejecucion_id` (módulo 2), no en memoria.
- **Pausa real para aprobación**, con una interfaz que muestre la propuesta como en el módulo 6, y expiración de las
  solicitudes no respondidas.
- **Ejecución asíncrona**: la petición del usuario encola la tarea y responde enseguida; un trabajador corre el agente
  y notifica al terminar o al pausar.
- **Observabilidad**: cada paso como un *span* con modelo, tokens, costo, latencia y resultado de la herramienta (curso
  de AI Engineering, módulo de observabilidad). Alertas por tasa de cortes por presupuesto y por bucle.
- **Datos reales**: el ATS de verdad tras un servidor MCP (módulo 4), con permisos por usuario.
- **Protección de datos personales**: los CVs son datos personales. Registro de qué se envía al proveedor del modelo,
  retención acotada de trazas y cumplimiento de la Ley 1581 de 2012 (o el RGPD, si aplica).
- **Evaluación continua** con el modelo real y casos nuevos que salgan de los incidentes de producción.

---

<a name="6-proyecto"></a>
## 6. Tu proyecto

Para cerrar el curso, aplica el controlador a un caso tuyo:

1. Elige un proceso con datos que conoces y una verdad que puedas escribir en código (aunque sea para 20 casos).
2. Diseña 3 a 6 herramientas con la lista del módulo 1 y clasifícalas por riesgo (módulo 6).
3. Escribe las invariantes que deben cumplirse siempre y ponlas en el controlador (módulo 2).
4. Corre el agente con el modelo simulado y sus defectos hasta que la suite pase.
5. Córrelo con un modelo real, 5 veces por tarea, y reporta `pass^k`, costo y latencia.
6. Decide con esos números si va a producción, si necesita más guardas o si debió ser un workflow.

El último punto también es un resultado válido. Saber cuándo no usar un agente es la mitad del oficio.
