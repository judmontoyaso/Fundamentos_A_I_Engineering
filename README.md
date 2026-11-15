# Fundamentos de AI Engineering — Cursos prácticos

Repositorio con tres cursos prácticos de ingeniería de IA que comparten el mismo caso conductor (**Asistente de Selección de Talento** sobre 30 perfiles y 8 vacantes) y pueden recorrerse desde la web (`web/`) o ejecutando los scripts localmente en Python.

---

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| [`curso-ai-engineering/`](./curso-ai-engineering/README.md) | **Curso 1 — Fundamentos de AI Engineering** (9 módulos): Pydantic + `instructor`, embeddings, Qdrant, BM25 + RRF, workflows de agentes, LangGraph, observabilidad, memoria y guardrails, y proyecto integrador. |
| [`curso-evals/`](./curso-evals/README.md) | **Curso 2 — Evals para Sistemas de IA** (9 módulos): primer eval, análisis de errores, datos sintéticos, anotación y κ de Cohen, jueces con código y con LLM, calibración, RAG + tool calling, multi-turn y CI/CD en producción. |
| [`curso-ai-search/`](./curso-ai-search/README.md) | **Curso 3 — AI Search y RAG en Producción** (10 módulos): métricas de recuperación, anatomía de un índice híbrido, chunking y representación, expansión de consultas, reranking, compresión de contexto, atribuciones verificables, seguridad/ACL, costo/latencia y sistema en producción. |
| [`web/`](./web/README.md) | Aplicación web en Next.js para leer los tres cursos, responder cuestionarios, hacer las tareas de anotación y descargar los laboratorios en `.zip`. |

---

## Ejecución rápida de los laboratorios en Python

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS / Linux: source .venv/bin/activate
pip install -r curso-ai-engineering/requirements.txt
```

Configura `OPENAI_API_KEY` o `DEEPSEEK_API_KEY` en un archivo `.env` en la raíz del proyecto y ejecuta cualquier script de `code/` dentro de [`curso-ai-engineering/`](./curso-ai-engineering/README.md), [`curso-evals/`](./curso-evals/README.md) o [`curso-ai-search/`](./curso-ai-search/README.md).
