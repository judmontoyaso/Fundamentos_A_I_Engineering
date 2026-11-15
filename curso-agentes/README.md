# Agentes en producción: herramientas, estado y control

> Contenido, arquitecturas y código **originales**, diseñados para construir agentes que operan sobre sistemas reales
> sin salirse de presupuesto, sin corromper datos y con trazabilidad completa.

En el curso de **AI Engineering** construimos el buscador y un primer bucle de herramientas; en **Evals** aprendimos a medir con rigor; en **AI Search** llevamos la recuperación al límite. Pero cuando un sistema deja de solo responder preguntas y empieza a **ejecutar acciones de varios pasos** —consultar varias fuentes, cruzar restricciones, escribir en una base de datos, pedir confirmación humana y recuperarse de fallos— aparece una clase nueva de problemas de ingeniería.

Este curso responde una pregunta central: **¿cómo construyes un agente que sea confiable en producción cuando cada paso adicional multiplica el riesgo de error, el costo y la latencia?**

---

## El proyecto: de buscador pasivo a agente de preselección técnica

Nuestro sistema de reclutamiento ya sabe buscar hojas de vida. Ahora debe operar un flujo completo de preselección para una vacante:

1. **Inspeccionar la vacante** y extraer requisitos obligatorios, deseables y bandas salariales.
2. **Explorar el repositorio de candidatos** combinando filtros SQL y búsqueda semántica.
3. **Verificar disponibilidad e historial** en el sistema ATS (entrevistas previas, periodo de enfriamiento, expectativas salariales).
4. **Detectar contradicciones o huecos** y preparar un informe técnico con evidencia citada.
5. **Pausar la ejecución (checkpoint)** antes de cualquier acción irreversible (como enviar un correo o agendar entrevista) hasta recibir aprobación humana.

---

## Mapa del curso

| # | Módulo | La pregunta que responde |
|---|---|---|
| 0 | [Cuándo usar (y cuándo no usar) un agente](modulo-00-anatomia-de-un-agente/README.md) | ¿Necesitas un bucle autónomo o un flujo determinista con un LLM adentro? |
| 1 | [Diseño de herramientas y contratos poka-yoke](modulo-01-herramientas-contratos/README.md) | ¿Por qué una buena API para humanos suele ser una pésima herramienta para un modelo? |
| 2 | [Máquinas de estados, checkpoints e idempotencia](modulo-02-estado-y-checkpoints/README.md) | ¿Cómo reanudar un agente que falló en el paso 6 sin repetir los efectos secundarios de los pasos 1 a 5? |
| 3 | [Presupuesto de contexto, poda y memoria](modulo-03-contexto-y-memoria/README.md) | ¿Cómo evitar que 12 respuestas de herramientas llenen y degraden la ventana de contexto? |
| 4 | [Protocolo MCP y servidores de herramientas](modulo-04-mcp-e-integraciones/README.md) | ¿Cómo desacoplar las herramientas del agente usando Model Context Protocol con permisos aislados? |
| 5 | [Subagentes, delegación y ejecución paralela](modulo-05-subagentes-y-paralelismo/README.md) | ¿Cuándo conviene dividir un agente en subagentes con ventanas de contexto limpias? |
| 6 | [Aprobación humana y defensa contra inyección indirecta](modulo-06-human-in-the-loop-seguridad/README.md) | ¿Cómo impedir que un texto malicioso dentro de un CV secuestre las herramientas del agente? |
| 7 | [Evaluar agentes: trayectorias, pass@k y pass^k](modulo-07-evaluacion-de-trayectorias/README.md) | ¿Cómo medir confiabilidad real cuando el agente debe acertar el 100 % de las veces y no una de cada cinco? |
| 8 | [Proyecto final: agente de preselección en producción](modulo-08-proyecto-final/README.md) | Un agente completo con presupuesto, checkpoints, aprobación humana y suite de regresión |

---

## Cómo usarlo

Cada módulo incluye manual (`README.md`), ejercicios con solución (`ejercicios.md`), autoevaluación interactiva y scripts completos en `code/`. Puedes leer y completar las autoevaluaciones en la web, y descargar el `.zip` del curso para correr todos los scripts en tu máquina (`pip install -r requirements.txt`). Todos los laboratorios funcionan tanto en modo determinista local (con nuestro entorno simulado de ATS en `comun/ag_comun.py`) como conectados a tu clave `OPENAI_API_KEY`.

Empieza por el [Módulo 0](modulo-00-anatomia-de-un-agente/README.md).
