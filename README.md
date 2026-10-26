# AI Engineering — Curso Profundo (edición personal)

> Material de estudio **original** construido para ir más a fondo que un curso en video.
> Uso personal. No es una copia de ningún curso: es tu propio manual, para leer, editar, correr y ampliar.

Este repositorio es un curso-manual de **AI Engineering**: cómo pasar de un demo de LLM a software de verdad —
determinista en su contrato, validado, observable y barato de operar. El hilo conductor es un proyecto real
que crece módulo a módulo: **un buscador de hojas de vida** (resume search) que extrae datos estructurados de
CVs y PDFs, los indexa, y responde búsquedas con RAG híbrido.

La diferencia con un curso en video no es el temario sino la **profundidad**: aquí cada idea viene con el *por qué*
a nivel de tokens, los *trade-offs* reales, el código que ejecutas, y ejercicios con solución.

---

## Cómo usar este curso

1. **Lee el `README.md` de cada módulo** como el texto principal. Es un manual, no notas sueltas.
2. **Corre el código** de la carpeta `code/` de cada módulo. Todo está pensado para ejecutarse de verdad.
3. **Haz los ejercicios** (`ejercicios.md`). Las soluciones están al final, tápalas hasta intentarlo.
4. **Avanza el proyecto**: cada módulo deja una pieza del buscador de CVs.
5. **Comprueba lo aprendido** con la autoevaluación de cada módulo (`autoevaluacion.json`, se corrige y explica cada
   respuesta).

### La app del curso

`app/` es una aplicación local para estudiar todo lo anterior de forma interactiva: backend FastAPI en `app/backend`
(puerto 8000) y frontend React en `app/frontend` (puerto 5173). Incluye, por módulo, el manual, los ejercicios, el
**laboratorio** (los scripts de `code/` como celdas ejecutables, estilo notebook) y la **autoevaluación**. En el
Módulo 9 está el **asistente de selección en vivo**: el sistema completo, con su traza y su memoria por reclutador,
usable desde el navegador.

```bash
cd app/backend
python run.py
```

```bash
cd app/frontend
npm run dev
```

### Requisitos

- **Python 3.11+**
- Una API key de al menos un proveedor (OpenAI, Anthropic, Google AI Studio u OpenRouter), o un modelo local con **Ollama**.
- Entorno recomendado:

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -U "instructor" "pydantic>=2" "openai" "anthropic" "jinja2" "pymupdf" "qdrant-client" "rank-bm25"
```

Crea un archivo `.env` en la raíz (no lo subas a ningún lado):

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=...
```

> **Sobre los nombres de modelo:** en el código uso identificadores reales y actuales como variables de entorno
> o constantes al inicio de cada archivo, para que cambies de proveedor/modelo sin tocar la lógica. La ingeniería
> que enseñamos es independiente del modelo de moda.

---

## Mapa del curso

| # | Módulo | Qué dominas al terminar | Pieza del proyecto |
|---|--------|-------------------------|--------------------|
| 1 | [**Datos estructurados con LLMs**](modulo-01-datos-estructurados/README.md) | Sacar datos validados de texto y PDFs con Instructor + Pydantic; retry, costos, paralelización | Esquema de extracción del CV |
| 2 | [**Embeddings y búsqueda semántica**](modulo-02-embeddings-busqueda-semantica/README.md) | Qué es un embedding, cómo se compara y almacena; Qdrant | Indexar CVs por significado |
| 3 | [**Chunking, metadata y RAG**](modulo-03-chunking-metadata-rag/README.md) | Las 4 familias de chunking; metadata filtering; primer RAG | Partir CVs y recuperar pasajes |
| 4 | [**BM25, Hybrid Search y RRF**](modulo-04-bm25-hibrida-rrf/README.md) | Búsqueda léxica, cuándo gana, y fusión con Reciprocal Rank Fusion | Búsqueda híbrida sobre CVs |
| 5 | [**Workflows y agentes**](modulo-05-workflows-agentes/README.md) | Diferencia entre workflow y agente; cuándo cada uno | Orquestar la búsqueda |
| 6 | [**LangGraph**](modulo-06-langgraph/README.md) | Grafos de estado, nodos, aristas condicionales, checkpoints | Flujo del buscador como grafo |
| 7 | [**Observabilidad**](modulo-07-observabilidad/README.md) | Tracing, evals, métricas de un sistema no determinista | Medir calidad de respuestas |
| 8 | [**Memoria y guardrails**](modulo-08-memoria-guardrails/README.md) | Memoria conversacional y defensas de entrada/salida | Endurecer el buscador |
| 9 | [**Proyecto integrador**](modulo-09-proyecto-integrador/README.md) | Todo junto, de punta a punta | El buscador completo |

### Cursos que siguen a este

| Curso | Qué responde | Estado |
|---|---|---|
| [**Evals para AI Engineers**](curso-evals/README.md) | ¿Cómo sé, con evidencia, si un cambio mejoró o empeoró el sistema? | Completo: 12 módulos y proyecto final |
| **AI search: medir y mejorar** | ¿Qué está fallando en el RAG, y qué cambio lo arregla? | Pendiente (después de Evals) |

En la app, el selector **Curso** (arriba a la izquierda) cambia entre ellos.

---

## Filosofía (lee esto antes del Módulo 1)

El error número uno en AI Engineering es tratar al LLM como una **función pura** que siempre devuelve lo que pides.
No lo es: es un **proceso estocástico** que devuelve *texto plausible*. Toda la disciplina consiste en construir
un **contrato** alrededor de ese proceso —un esquema que valida, reintenta y falla ruidosamente cuando algo no cuadra—
para que el resto de tu sistema pueda confiar en la salida como confía en cualquier otra función.

Ese es el salto que saca a un producto del **"PoC Purgatory"**: el demo funcionó una vez en la presentación, pero en
producción falla de vez en cuando, y de formas silenciosas. El Módulo 1 es, literalmente, cómo convertir "texto plausible"
en "dato en el que puedo confiar".

Empieza por [`modulo-01-datos-estructurados/README.md`](modulo-01-datos-estructurados/README.md).
