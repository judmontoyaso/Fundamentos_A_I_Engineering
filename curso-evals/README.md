# Evals para AI Engineers

> El contenido, los datos y el código de este curso se escribieron para el curso, a partir de la práctica con
> sistemas reales.

El curso de AI Engineering terminó con un sistema que funciona: extrae CVs, busca con RAG híbrido, recomienda con un
agente y tiene guardrails. Este curso responde la pregunta que viene después: **¿cómo sé, con evidencia, si un cambio
lo mejoró o lo empeoró?**

El orden del curso es el contrario al que se suele seguir: **en lugar de empezar escribiendo métricas, se empieza
leyendo salidas** para entender dónde falla el sistema, con qué frecuencia y qué fallos importan. Solo después se decide qué medir, y solo al final se
escribe un juez. Cada técnica entra cuando el sistema la necesita, del caso más fácil de verificar al más difícil.

![Curso 2 · Ciclo de evaluación continua: Error Analysis, Dataset Dorado, Juez Calibrado y Puerta de Calidad en CI/CD](/infografias/evals-arquitectura.svg)

---

## Los sistemas que vamos a evaluar

Son los tuyos, del curso de AI Engineering ([`../curso-ai-engineering/`](../curso-ai-engineering/README.md)):

| Sistema | Qué hace | Por qué es difícil evaluarlo |
|---|---|---|
| **Extractor** (Módulo 1 de AI Engineering) | Texto de un CV → ficha con nombre, correo, años y skills | Casi nada: cada campo tiene una respuesta correcta. Por eso va primero |
| **RAG** (Módulos 3 y 4) | Pregunta → respuesta citando CVs | Hay que separar si falló la búsqueda o la respuesta |
| **Agente** (Módulos 5, 6 y 9) | Pedido → búsquedas con herramientas → recomendación | El resultado depende del camino, y hay muchas formas de llegar |

Y un set de datos escrito para este curso: [`comun/ev_datos.py`](comun/ev_datos.py), 30 CVs con lo que se espera
extraer de cada uno, la mitad difíciles a propósito.

---

## Mapa del curso

| # | Módulo | La pregunta que responde |
|---|---|---|
| 0 | [Qué vamos a evaluar](modulo-00-que-vamos-a-evaluar/README.md) | ¿Qué sistemas, con qué datos, y por qué no basta con probarlos a mano? |
| 1 | [El primer eval en una tarde](modulo-01-primer-eval/README.md) | ¿Puedo pasar el extractor a un modelo barato sin perder calidad? |
| 2 | [Error analysis](modulo-02-error-analysis/README.md) | ¿Dónde falla el sistema, y qué fallo arreglo primero? |
| 3 | [Datos sintéticos](modulo-03-datos-sinteticos/README.md) | ¿Cómo consigo casos difíciles sin tener usuarios, y sin engañarme? |
| 4 | [Las personas que etiquetan](modulo-04-anotacion/README.md) | ¿Mis etiquetas son correctas? ¿Dos personas etiquetarían igual? |
| 5 | [LLM como juez](modulo-05-llm-juez/README.md) | ¿Puedo confiar en un juez, y cuál es la tasa real de fallos si el juez se equivoca? |
| 6 | [¿Falló el retrieval o la respuesta?](modulo-06-evals-rag/README.md) | ¿Cómo evalúo un RAG por partes? |
| 7 | [Evaluar agentes con herramientas](modulo-07-evals-agentes/README.md) | ¿Importa el resultado o el camino? |
| 8 | [Conversaciones de varios turnos](modulo-08-multi-turn/README.md) | ¿Cómo evalúo algo que depende de lo que se dijo antes? |
| 9 | [Del notebook al CI](modulo-09-evals-en-ci/README.md) | ¿Cómo hago que cada cambio pase por los evals sin que nadie se acuerde? |
| 10 | [Evals y guardrails en producción](modulo-10-produccion/README.md) | ¿Qué mido cuando ya no tengo la respuesta correcta? |
| 11 | [Mejorar el sistema con los evals](modulo-11-mejorar/README.md) | ¿Cómo uso los evals para mejorar sin sobreajustarme a ellos? |
| 12 | [Proyecto final](modulo-12-proyecto-final/README.md) | Evaluar desde cero un sistema que no construiste |


---

## Cómo usarlo

Cada módulo incluye manual (`README.md`), ejercicios con solución (`ejercicios.md`), autoevaluación y los scripts completos en `code/`. Puedes leer y hacer las autoevaluaciones y tareas de anotación en la web del curso, y descargar el `.zip` del curso para correr los scripts de `code/` en tu máquina con tu propia API key.

Instala las dependencias con `pip install -r requirements.txt` y define tu clave (`OPENAI_API_KEY`) como variable de entorno, igual que en el curso de AI Engineering. Variable opcional:

```env
# El modelo "barato" candidato que evalúa el Módulo 1. Usa uno que exista en tu cuenta.
MODELO_BARATO=gpt-5.4-nano
```

Los resultados de cada laboratorio se guardan en `curso-evals/salida/` (no se sube al repositorio): son tu histórico.

Empieza por el [Módulo 0](modulo-00-que-vamos-a-evaluar/README.md).
