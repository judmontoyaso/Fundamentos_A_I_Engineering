# Fundamentos de AI Engineering

Curso práctico de 9 módulos sobre las técnicas básicas de la ingeniería de IA. Todos los módulos trabajan sobre el
mismo proyecto, de modo que cada técnica se compara con las anteriores sobre la misma base y al final todas se integran
en un solo sistema.

![Curso 1 · Arquitectura completa del pipeline TalentAI: extracción validada, Qdrant, Hybrid RAG, LangGraph y observabilidad](/infografias/ai-engineering-arquitectura.png)

---

## El caso conductor

Construimos un **asistente de selección de personal**. Recibe CVs en texto libre o en PDF, los convierte en datos
validados, los indexa para buscarlos por palabras y por significado, y responde los pedidos de un reclutador ("busco a
alguien senior para liderar datos en tiempo real") con una recomendación que cita lo que dice cada CV. Los datos son
CVs escritos como llegan en la práctica: con formatos distintos, alguno en inglés, alguno sin correo y uno con una
instrucción escondida para engañar al sistema.

---

## Mapa del curso

| # | Módulo | Qué construimos sobre el caso |
|---|---|---|
| 1 | [Datos estructurados](./modulo-01-datos-estructurados/README.md) | El esquema de extracción del CV con Pydantic e Instructor, validación con reintentos, lectura de PDFs con texto, tablas o escaneados, y una primera defensa contra *prompt injection* |
| 2 | [Embeddings y búsqueda semántica](./modulo-02-embeddings-busqueda-semantica/README.md) | Búsqueda por significado sobre los CVs en Qdrant, elección del modelo de embeddings con mediciones y `recall@k` |
| 3 | [Chunking, metadata e introducción a RAG](./modulo-03-chunking-metadata-rag/README.md) | CVs partidos por secciones con metadata filtrable, chunking jerárquico y un primer RAG cuyas citas se verifican contra el texto |
| 4 | [BM25, búsqueda híbrida y RRF](./modulo-04-bm25-hibrida-rrf/README.md) | BM25 implementado desde cero, tokenización en español, búsqueda híbrida con RRF en Qdrant, re-ranking y comparación medida de los tres modos |
| 5 | [Workflows y agentes](./modulo-05-workflows-agentes/README.md) | Encadenamiento, enrutamiento, paralelización, orquestador-trabajadores y evaluador-optimizador; un agente con herramientas y un servidor MCP |
| 6 | [LangGraph](./modulo-06-langgraph/README.md) | El flujo de selección como grafo: evaluación en paralelo, persistencia, reanudación tras un fallo y aprobación humana antes de enviar la invitación |
| 7 | [Observabilidad](./modulo-07-observabilidad/README.md) | Trazas con tokens, costo y latencia, un dataset de extracción, un LLM juez calibrado contra etiquetas humanas y pruebas de regresión de prompts |
| 8 | [Memoria y guardrails](./modulo-08-memoria-guardrails/README.md) | Memoria de la conversación y de las preferencias de cada reclutador; guardrails medidos contra datos personales, *prompt injection* y pedidos discriminatorios |
| 9 | [Proyecto integrador](./modulo-09-proyecto-integrador/README.md) | El asistente completo, con una evaluación de punta a punta y el análisis de los fallos que solo aparecieron al integrar las piezas |

---

## Estructura de cada módulo

```
modulo-XX-nombre/
├── README.md        # Manual completo: conceptos, diagramas y explicación del código
├── ejercicios.md    # Ejercicios guiados y retos sobre el mismo caso
└── code/            # Scripts numerados listos para ejecutar en orden
```

Cada módulo trae en `code/` los scripts y los datos que necesita. Los 10 CVs del proyecto integrador están en
[`modulo-09-proyecto-integrador/code/00_datos_cvs.py`](./modulo-09-proyecto-integrador/code/00_datos_cvs.py).

---

## Cómo ejecutar los laboratorios

1. Instala las dependencias en un entorno virtual con Python 3.10+:

   ```bash
   pip install -r curso-ai-engineering/requirements.txt
   ```

2. Define tu clave de OpenAI como variable de entorno. Los scripts la leen del entorno; **no cargan el archivo `.env` por sí solos**. En la terminal donde vas a ejecutarlos:

   ```bash
   # macOS / Linux
   export OPENAI_API_KEY=sk-...
   # Windows (PowerShell)
   $env:OPENAI_API_KEY = "sk-..."
   ```

   Si prefieres guardarla en un archivo `.env` en la raíz del proyecto (`OPENAI_API_KEY=sk-...`), ejecuta los scripts
   **desde esa carpeta** con `dotenv run -- python ...` (viene con `python-dotenv`, que ya está en las dependencias).

   El modelo se elige con la variable `MODELO`. Con otro proveedor compatible con la API de OpenAI, define además
   `OPENAI_BASE_URL`; el código pide salida estructurada con JSON Schema, así que el proveedor tiene que soportarla.

   Las búsquedas de los módulos **2, 3 y 4** corren en local sin clave de API; los scripts que generan respuestas
   (el RAG del Módulo 3, el re-ranking del Módulo 4) o comparan modelos de embeddings por API sí la necesitan. Los
   módulos **1, 5, 6, 7, 8 y 9** llaman al modelo.

3. Ejecuta cualquier script desde su carpeta o desde la raíz:

   ```bash
   python curso-ai-engineering/modulo-01-datos-estructurados/code/03_inspeccionar_schema.py
   ```
