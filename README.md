# IA en Producción · Ruta completa de ingeniería de IA (4 cursos · 42 módulos)

Formación práctica en español para construir, evaluar, escalar y operar sistemas con modelos de lenguaje en producción. Todo el material se articula alrededor de un mismo caso de ingeniería real (un sistema de reclutamiento, búsqueda híbrida de talento y preselección autónoma sobre un ATS), con manuales profundos, ejercicios resueltos, autoevaluaciones y laboratorios de código en Python.

## Los cuatro cursos

| # | Curso | Carpeta | Módulos | Qué construyes y dominas |
|---|---|---|---|---|
| 1 | **Fundamentos de AI Engineering** | [`curso-ai-engineering/`](./curso-ai-engineering/README.md) | 9 | Salidas estructuradas, embeddings desde cero, Qdrant, búsqueda híbrida BM25 + RRF, workflows, LangGraph, observabilidad, guardrails y proyecto integrador |
| 2 | **Evaluación y Observabilidad de Sistemas de IA (Evals)** | [`curso-evals/`](./curso-evals/README.md) | 13 | Error analysis, anotación y $\kappa$ de Cohen, jueces LLM calibrados con TPR/TNR, RAG Triad, regresión en CI/CD, monitoreo en producción y optimización de costo/latencia |
| 3 | **Búsqueda con IA y RAG en Producción** | [`curso-ai-search/`](./curso-ai-search/README.md) | 11 | nDCG@k y MRR, chunking y estructura, enriquecimiento en ingesta, BM25 + vectores, reranking con cross-encoders, ruteo de consultas, permisos ACL/GDPR y caché semántica |
| 4 | **Agentes de IA en Producción: Herramientas, Estado y Control** | [`curso-agentes/`](./curso-agentes/README.md) | 9 | Presupuestos de ejecución, herramientas Poka-Yoke, máquinas de estado con checkpoints e idempotencia, poda de contexto, servidores MCP sobre JSON-RPC (`stdio`), subagentes Map-Reduce, HITL, defensa contra *prompt injection* y evaluación $\text{pass}\hat{\mkern6mu}k$ |

## Ejecución local de los laboratorios

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r curso-ai-engineering/requirements.txt
```

Define `OPENAI_API_KEY` como variable de entorno (o guárdala en un `.env` y ejecuta los scripts desde esa carpeta). En [`curso-agentes/`](./curso-agentes/README.md), además, todos los laboratorios pueden correrse sin costo de API usando el modo determinista integrado (`ModeloSimulado`) o conectarse a OpenAI al definir `OPENAI_API_KEY`.
