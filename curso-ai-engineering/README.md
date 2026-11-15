# Fundamentos de AI Engineering

Curso práctico de 9 módulos sobre los bloques fundamentales de la ingeniería de IA moderna. Todos los módulos comparten **un mismo problema y un mismo dataset** para que cada técnica se compare sobre la misma base y al final se integren en un sistema completo.

![Curso 1 · Arquitectura completa del pipeline TalentAI: extracción validada, Qdrant, Hybrid RAG, LangGraph y observabilidad](/infografias/ai-engineering-arquitectura.png)

---

## El caso conductor

Construimos el asistente técnico de un **taller de talento de ingeniería**: dado un repositorio de **30 perfiles de candidatos** (con habilidades, experiencia, proyectos, ubicación, senioridad y notas de entrevistas) y **8 vacantes abiertas**, el sistema debe ayudar a un líder técnico a encontrar, comparar y justificar qué candidatos encajan mejor con cada vacante — con trazabilidad, memoria de las preferencias del líder y límites claros sobre qué puede y qué no puede afirmar.

---

## Mapa del curso

| # | Módulo | Qué construimos sobre el caso |
|---|---|---|
| 1 | [Datos estructurados](./modulo-01-datos-estructurados/README.md) | Esquemas Pydantic de `Candidato`, `Vacante` y `EvaluacionCandidato`; extracción desde CVs en texto libre con `instructor` y Function Calling |
| 2 | [Embeddings y búsqueda semántica](./modulo-02-embeddings-busqueda-semantica/README.md) | Vectorización de los 30 perfiles y las 8 vacantes; similitud coseno desde cero; visualización 2D del espacio de talento |
| 3 | [Bases vectoriales (Qdrant)](./modulo-03-bases-vectoriales-qdrant/README.md) | Colección `candidatos` en Qdrant con payload indexado y filtros duros (ubicación, años de experiencia, modalidad) combinados con similitud vectorial |
| 4 | [BM25, búsqueda híbrida y RRF](./modulo-04-bm25-hibrida-rrf/README.md) | Búsqueda léxica exacta para tecnologías específicas (`"K8s"`, `"HIPAA"`, `"COBOL"`) fusionada con la semántica mediante Reciprocal Rank Fusion |
| 5 | [Workflows de agentes](./modulo-05-workflows-agentes/README.md) | Chaining, routing, paralelización y evaluador-optimizador aplicados al análisis y comparación de candidatos |
| 6 | [Orquestación con LangGraph](./modulo-06-langgraph/README.md) | Grafo con estado tipado, reintentos cuando la búsqueda no alcanza umbral, y punto de aprobación humana antes de enviar el informe |
| 7 | [Observabilidad y evaluación](./modulo-07-observabilidad/README.md) | Trazas de cada paso (latencia, tokens, costo), dataset dorado de 15 consultas con candidatos esperados, `Recall@k`, `MRR` y *LLM-as-a-judge* |
| 8 | [Memoria y guardrails](./modulo-08-memoria-guardrails/README.md) | Memoria de sesión y de preferencias del reclutador; guardrails contra PII, *prompt injection* en CVs y criterios protegidos (edad, género, origen) |
| 9 | [Proyecto integrador](./modulo-09-proyecto-integrador/README.md) | **Asistente de Selección de Talento** de punta a punta: ingesta → indexación híbrida → agente en LangGraph con memoria y guardrails → suite de evaluación y trazas |

---

## Estructura de cada módulo

```
modulo-XX-nombre/
├── README.md        # Manual completo: conceptos, diagramas y explicación del código
├── ejercicios.md    # Ejercicios guiados y retos sobre el mismo caso
└── code/            # Scripts numerados listos para ejecutar en orden
```

El dataset compartido vive en [`modulo-01-datos-estructurados/data/`](./modulo-01-datos-estructurados/data/) y todos los módulos posteriores lo consumen desde ahí.

---

## Cómo ejecutar los laboratorios

1. Instala las dependencias en un entorno virtual con Python 3.10+:

   ```bash
   pip install -r curso-ai-engineering/requirements.txt
   ```

2. Configura tu clave de OpenAI o DeepSeek en un archivo `.env` en la raíz del proyecto (o en tu entorno):

   ```bash
   OPENAI_API_KEY=sk-...
   # O bien:
   DEEPSEEK_API_KEY=sk-...
   ```

   Los módulos **2, 3 y 4** corren 100 % en local sin clave de API. Los módulos **1, 5, 6, 7, 8 y 9** usan el proveedor configurado en `.env`.

3. Ejecuta cualquier script desde su carpeta o desde la raíz:

   ```bash
   python curso-ai-engineering/modulo-01-datos-estructurados/code/01_pydantic_basico.py
   ```
