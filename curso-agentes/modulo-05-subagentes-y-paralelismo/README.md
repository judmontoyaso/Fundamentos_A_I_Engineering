# Módulo 5 · Subagentes, delegación y ejecución paralela

Un error común al diseñar sistemas multiagente es crear «roles» teatrales (*Agente Gerente*, *Agente Psicólogo*, *Agente Crítico*) que conversan entre sí en un chat infinito sin restricciones. En ingeniería de producción, la razón real para dividir un agente en **subagentes** no es el juego de roles, sino dos límites físicos:

1. **Aislamiento de la ventana de contexto**: si necesitas auditar en profundidad 8 candidatos leyendo sus repositorios, proyectos y entrevistas pasadas (4.000 tokens por candidato), hacerlo en un solo hilo contamina la ventana con 32.000 tokens. En cambio, si lanzas un subagente por candidato con su propia ventana limpia, cada subagente consume 4.000 tokens y devuelve al orquestador un **dictamen estructurado de 150 tokens**.
2. **Reducción de latencia por paralelismo (`map-reduce`)**: evaluar 8 candidatos en serie a 3 segundos por candidato tarda **24 segundos**; evaluarlos en paralelo con `asyncio.gather` o un pool acotado tarda **~3.2 segundos** (la latencia del más lento).

![Módulo 5 · Patrón Orquestador y Subagentes en paralelo con ventanas de contexto limpias](/infografias/agentes-m5-subagentes-map-reduce.png)

---

## Reglas del patrón Orquestador → Trabajador

- El **orquestador** no lee los documentos crudos pesados; solo reparte subtareas acotadas y sintetiza los resúmenes tipados que devuelven los trabajadores.
- Cada **subagente trabajador** recibe únicamente:
  1. Su objetivo puntual (p. ej., evaluar un único candidato contra una rúbrica).
  2. Las herramientas mínimas de lectura necesarias para ese candidato.
  3. Un esquema de salida estricto (`DictamenCandidato`).
- Los subagentes **no se comunican libremente todos contra todos**: siempre reportan hacia arriba al orquestador con un semáforo de concurrencia (`Semaphore(4)`) para no agotar los *rate limits* del proveedor de modelos.
