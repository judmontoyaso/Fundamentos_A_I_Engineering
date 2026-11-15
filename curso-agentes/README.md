# Agentes en producción: herramientas, estado y control

> Contenido, arquitecturas y código **originales**, diseñados para construir agentes que operan sobre sistemas reales
> sin salirse de presupuesto, sin corromper datos y con trazabilidad completa.

En el curso de **AI Engineering** construimos el buscador y un primer bucle de herramientas; en **Evals** aprendimos a medir con rigor; en **AI Search** llevamos la recuperación al límite. Pero cuando un sistema deja de solo responder preguntas y empieza a **ejecutar acciones de varios pasos** —consultar varias fuentes, cruzar restricciones, invocar servidores externos por protocolo, pedir confirmación humana y recuperarse de fallos— aparece una clase nueva de problemas de ingeniería.

Este curso responde una pregunta central: **¿cómo construyes un controlador de agente que sea confiable en producción cuando cada paso adicional multiplica el riesgo de error, el costo y la latencia?**

![Arquitectura de un agente en producción: presupuesto, máquina de estados, herramientas poka-yoke, aprobación humana y evaluación pass^k](/infografias/agentes-arquitectura.png)

---

## El proyecto: de buscador pasivo a agente de preselección técnica

Nuestro sistema de reclutamiento opera un flujo completo de preselección sobre el ATS (`comun/ag_comun.py`):

1. **Inspeccionar la vacante (`obtener_vacante`)** y cargar requisitos obligatorios, modalidad, inglés mínimo y tope salarial (`VAC-101` y `VAC-102`).
2. **Explorar el catálogo de candidatos (`buscar_candidatos`)** validando habilidades contra un vocabulario controlado y manejando errores con sugerencias accionables.
3. **Inspeccionar fichas y verificar elegibilidad (`consultar_ficha_candidato`, `verificar_elegibilidad`)** comprobando reglas duras de negocio: 90 días de enfriamiento desde el último contacto, nivel CEFR de inglés, modalidad híbrida/remota y años de experiencia.
4. **Neutralizar inyecciones indirectas (`CAND-04`)** aislando el procesamiento de textos no confiables de las herramientas con privilegios.
5. **Pausar la ejecución (checkpoint + HITL)** antes de acciones con efectos externos (`agendar_entrevista`) hasta contar con firma humana, sin duplicar eventos ante reintentos.

---

## Mapa del curso

| # | Módulo | La pregunta que responde |
|---|---|---|
| 0 | [Cuándo usar (y cuándo no usar) un agente](modulo-00-anatomia-de-un-agente/README.md) | ¿Necesitas un bucle autónomo o un flujo determinista, y cómo cortas el gasto fuera del modelo? |
| 1 | [Diseño de herramientas y contratos poka-yoke](modulo-01-herramientas-contratos/README.md) | ¿Cómo diseñar herramientas y errores accionables para que el modelo se autocorrija en un turno? |
| 2 | [Máquinas de estados, checkpoints e idempotencia](modulo-02-estado-y-checkpoints/README.md) | ¿Cómo impedir que el agente se salte verificaciones y cómo reanudar tras una caída sin duplicar efectos? |
| 3 | [Presupuesto de contexto, poda y memoria](modulo-03-contexto-y-memoria/README.md) | ¿Cómo reducir casi a la mitad los tokens de entrada podando observaciones antiguas y guardando memoria episódica? |
| 4 | [Protocolo MCP y servidores de herramientas](modulo-04-mcp-e-integraciones/README.md) | ¿Cómo aislar credenciales y herramientas en un subproceso real usando Model Context Protocol sobre JSON-RPC 2.0 (`stdio`)? |
| 5 | [Subagentes, delegación y ejecución paralela](modulo-05-subagentes-y-paralelismo/README.md) | ¿Cómo usar el patrón Orquestador-Trabajadores y Map-Reduce para acelerar 3.9x y ahorrar 95 % del contexto principal? |
| 6 | [Aprobación humana y defensa contra inyección indirecta](modulo-06-human-in-the-loop-seguridad/README.md) | ¿Cómo pausar ante herramientas irreversibles y defender el agente del CV hostil de `CAND-04`? |
| 7 | [Evaluar agentes: trayectorias, pass@k y pass^k](modulo-07-evaluacion-de-trayectorias/README.md) | ¿Por qué un agente con `pass@5 = 93.8 %` puede tener `pass^5 = 0.0 %` en producción y cómo medir ambos? |
| 8 | [Proyecto final: agente de preselección en producción](modulo-08-proyecto-final/README.md) | El `AgenteReclutadorProduccion` completo certificado por una suite CI/CD de 6 puertas de calidad |

---

## Cómo correr los laboratorios (con o sin API key)

Todos los scripts usan la interfaz `crear_modelo()` de `comun/ag_modelo.py`:

- **Sin API key (o con `AGENTE_SIMULADO=1`)**: corren con `ModeloSimulado`, una política determinista sin red cuyos defectos (`errata`, `terco`, `obedece_inyeccion`, `p_descuido`) se encienden en cada laboratorio para probar que **tu controlador** los contiene.
- **Con `OPENAI_API_KEY` en tu entorno (o en un archivo `.env`)**: `crear_modelo()` instancia automáticamente `ModeloOpenAI` (por defecto `gpt-4.1-mini`, o el modelo que definas en `MODELO`) usando *tool calling* real.

Empieza por el [Módulo 0](modulo-00-anatomia-de-un-agente/README.md).
