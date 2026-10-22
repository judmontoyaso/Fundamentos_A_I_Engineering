# Módulo 6 · LangGraph

> **Objetivo:** expresar los workflows y agentes del Módulo 5 como **grafos de estado** con LangGraph: nodos,
> aristas condicionales, estado con reductores, ejecución en paralelo, **persistencia** y **pausas para que una
> persona apruebe**. Sabrás qué te da un framework de orquestación que un bucle `for` no te da, y qué te cuesta.
>
> **Pieza del proyecto:** el asistente de selección pasa a ser un grafo que busca candidatos, los evalúa en
> paralelo, redacta la invitación a entrevista y **se detiene a esperar tu aprobación** antes de "enviarla".

Índice:

1. [Por qué un grafo](#1-por-que)
2. [Las tres piezas: estado, nodos y aristas](#2-piezas)
3. [El estado y los reductores](#3-estado)
4. [Aristas condicionales: el enrutamiento como grafo](#4-condicionales)
5. [Ciclos: un agente es un grafo con un bucle](#5-ciclos)
6. [Paralelismo y map-reduce con `Send`](#6-send)
7. [Persistencia: checkpointers e hilos](#7-persistencia)
8. [Humano en el bucle: `interrupt` y `Command`](#8-humano)
9. [Viajar en el tiempo: el historial de estados](#9-historial)
10. [Lo que LangGraph no hace por ti](#10-limites)
11. [Proyecto del módulo](#11-proyecto)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-por-que"></a>
## 1. Por qué un grafo

En el Módulo 5 escribiste el agente como un bucle `for` de 40 líneas. Funciona, y para muchos casos es la mejor
opción. Pero mira lo que **no** tiene:

- **No se puede pausar.** Si a mitad del proceso necesitas que una persona apruebe algo, el bucle no tiene dónde
  esperar: o bloqueas el proceso o pierdes el estado.
- **No sobrevive a un fallo.** Si el paso 4 de 6 falla por un error de red, vuelves a empezar desde el paso 1 y
  pagas otra vez las llamadas de los pasos 1-3.
- **No se ve.** La estructura del flujo está escondida en `if` y `for`; para entenderla hay que leer todo el código.
- **El paralelismo es manual.** Lo hiciste con `asyncio.gather`; funciona, pero lo mezclas con la lógica del flujo.

Un **grafo de estado** separa tres cosas: **qué datos** circulan (el estado), **qué trabajo** se hace (los nodos) y
**en qué orden** (las aristas). Con esa separación, el framework puede guardar el estado después de cada nodo,
pausar entre nodos, reanudar desde donde se quedó, ejecutar en paralelo los nodos independientes y dibujar el flujo.

LangGraph es una librería para eso. **No** es un framework de LLMs: dentro de cada nodo pones el código que
quieras. En este módulo los nodos llaman a la función `llm()` del Módulo 5 y al buscador del Módulo 4: nada de lo
que aprendiste cambia, solo la forma de organizarlo.

---

<a name="2-piezas"></a>
## 2. Las tres piezas: estado, nodos y aristas

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class Estado(TypedDict):          # 1. qué datos circulan
    consulta: str
    resultados: list[str]

def buscar(estado: Estado) -> dict:          # 2. un nodo: recibe el estado, devuelve CAMBIOS
    return {"resultados": hacer_busqueda(estado["consulta"])}

grafo = StateGraph(Estado)
grafo.add_node("buscar", buscar)
grafo.add_edge(START, "buscar")              # 3. aristas: en qué orden
grafo.add_edge("buscar", END)
app = grafo.compile()                        # valida el grafo y lo vuelve ejecutable

app.invoke({"consulta": "kafka", "resultados": []})
```

Detalles que importan:

- Un nodo **devuelve solo lo que cambia**, no el estado entero. LangGraph combina esa actualización con el estado.
- `compile()` **valida** el grafo: nodos sin conexión, aristas a nodos que no existen. Errores que en un bucle
  descubrirías en ejecución, aquí salen antes.
- `app.stream(..., stream_mode="updates")` emite lo que devolvió cada nodo a medida que termina: es tu traza.
- `app.get_graph().draw_mermaid()` devuelve el diagrama del flujo. Pégalo en cualquier visor de Mermaid.

Ejemplo sin ninguna llamada al modelo: [`code/01_primer_grafo.py`](code/01_primer_grafo.py).

---

<a name="3-estado"></a>
## 3. El estado y los reductores

Por defecto, si un nodo devuelve `{"resultados": [...]}`, ese valor **reemplaza** al anterior. A veces quieres
**acumular**: el historial de mensajes de un agente, las evaluaciones que llegan de nodos en paralelo, una bitácora.
Para eso se anota el campo con un **reductor**, una función que dice cómo combinar el valor viejo con el nuevo:

```python
import operator
from typing import Annotated

class Estado(TypedDict):
    consulta: str                                   # se reemplaza
    bitacora: Annotated[list[str], operator.add]    # se acumula: viejo + nuevo
```

Con el reductor, un nodo que devuelve `{"bitacora": ["buscó kafka"]}` **añade** una línea en vez de borrar las
anteriores. Es imprescindible en el paralelismo (§6): si tres nodos escriben a la vez en el mismo campo sin
reductor, LangGraph no sabe cuál gana y lanza un error en lugar de perder datos en silencio.

Diseña el estado como diseñaste los *response models* del Módulo 1: **pocos campos, con nombres claros**, y solo lo
que los nodos necesitan compartir. Un estado que crece sin control es tan difícil de depurar como una función con
cuarenta parámetros.

---

<a name="4-condicionales"></a>
## 4. Aristas condicionales: el enrutamiento como grafo

Una **arista condicional** es una función que mira el estado y devuelve el nombre del siguiente nodo:

```python
def elegir_modo(estado) -> str:
    return "bm25" if len(estado["consulta"].split()) <= 2 else "hibrida"

grafo.add_conditional_edges("clasificar", elegir_modo, {"bm25": "buscar_bm25", "hibrida": "buscar_hibrida"})
```

Así se expresan dos patrones del Módulo 5:

- **Enrutamiento:** la función lee la categoría que dejó un nodo clasificador (o aplica la regla gratuita que en el
  Módulo 5 empató con el LLM).
- **Encadenamiento con puertas:** la función lee el resultado de la puerta y decide entre "seguir" y "revisión
  humana".

El mapa `{"bm25": "buscar_bm25", ...}` es opcional, pero ayuda: le dice a LangGraph todos los destinos posibles,
así `compile()` puede validarlos y el diagrama los muestra. Ejemplo: [`code/02_condicionales.py`](code/02_condicionales.py).

---

<a name="5-ciclos"></a>
## 5. Ciclos: un agente es un grafo con un bucle

El bucle "decidir → actuar → observar" del Módulo 5 es un grafo de dos nodos con un ciclo:

```
START ─► decidir ──(¿terminar?)──► END
            ▲           │ no
            └── actuar ◄┘
```

```python
grafo.add_conditional_edges("decidir", lambda s: END if s["final"] else "actuar")
grafo.add_edge("actuar", "decidir")
```

El tope de pasos del Módulo 5 ahora es el **`recursion_limit`**: el número máximo de pasos (nodos ejecutados) por
invocación. Si se supera, LangGraph lanza `GraphRecursionError`. Ponlo siempre de forma explícita en la
configuración de cada invocación (`{"recursion_limit": 12}`) y captura la excepción: es tu defensa contra los bucles
de la §11 del Módulo 5.

Ejemplo, reutilizando las herramientas y la `Decision` del Módulo 5:
[`code/03_agente_como_grafo.py`](code/03_agente_como_grafo.py).

> LangGraph trae agentes ya hechos (`create_react_agent`, `ToolNode`) que funcionan con los modelos de chat de
> LangChain. Ahorran código, pero esconden el bucle y te atan a esos envoltorios. Cuando entiendas el grafo de este
> módulo, puedes decidir con criterio si te compensan.

---

<a name="6-send"></a>
## 6. Paralelismo y map-reduce con `Send`

Dos formas de ejecutar en paralelo:

1. **Ramas fijas:** si de un nodo salen aristas hacia varios nodos, LangGraph los ejecuta en el mismo paso, a la vez.
2. **Ramas dinámicas con `Send`:** cuando no sabes de antemano cuántas ramas habrá. Una arista condicional devuelve
   una lista de `Send("nodo", datos)`, una por elemento, y LangGraph ejecuta una copia del nodo para cada uno:

```python
from langgraph.types import Send

def repartir(estado):
    return [Send("evaluar", {"cv": cv}) for cv in estado["candidatos"]]   # map

class Estado(TypedDict):
    candidatos: list[dict]
    evaluaciones: Annotated[list[dict], operator.add]                     # reduce: acumula lo que llega

grafo.add_conditional_edges("buscar", repartir, ["evaluar"])
grafo.add_edge("evaluar", "ranking")
```

Es el patrón de seccionar del Módulo 5 (§6) y la base del orquestador-trabajadores (§7): el orquestador decide la
lista y `Send` reparte. Fíjate en que el nodo `evaluar` recibe **solo su porción** (`{"cv": ...}`), no el estado
entero. Ejemplo: [`code/05_map_reduce.py`](code/05_map_reduce.py).

---

<a name="7-persistencia"></a>
## 7. Persistencia: checkpointers e hilos

Si compilas el grafo con un **checkpointer**, LangGraph guarda una foto del estado (un *checkpoint*) después de cada
paso:

```python
from langgraph.checkpoint.memory import InMemorySaver

app = grafo.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "seleccion-vacante-42"}}
app.invoke(entrada, config)
app.get_state(config)          # el estado actual de ese hilo, y qué nodo toca después
```

- El **`thread_id`** identifica una conversación o un proceso. Dos hilos son independientes; volver a invocar el
  mismo hilo continúa desde su último estado. Es la base de la memoria conversacional (Módulo 8).
- `InMemorySaver` guarda en memoria del proceso: sirve para aprender y para tests, y se pierde al reiniciar. En
  producción se usa un checkpointer con base de datos (los hay para SQLite y PostgreSQL), con la misma interfaz.
- Con checkpoints, un fallo en el paso 4 no obliga a repetir los pasos 1-3: reanudas el hilo.

---

<a name="8-humano"></a>
## 8. Humano en el bucle: `interrupt` y `Command`

Esta es la razón más fuerte para usar LangGraph en el proyecto. Un nodo puede **pausar** el grafo y esperar a una
persona:

```python
from langgraph.types import interrupt, Command

def aprobar(estado):
    decision = interrupt({"borrador": estado["borrador"], "pregunta": "¿Envío esta invitación?"})
    return {"aprobado": decision["aprobado"], "borrador": decision.get("edicion") or estado["borrador"]}

resultado = app.invoke(entrada, config)      # se detiene: resultado["__interrupt__"] trae el borrador
# ... la persona revisa, quizás horas después, desde otra petición web ...
app.invoke(Command(resume={"aprobado": True}), config)   # continúa justo donde se quedó
```

Mientras espera no hay nada bloqueado: el estado está en el checkpointer, y la reanudación puede llegar desde otro
proceso o al día siguiente. Esto convierte la recomendación del Módulo 5 ("las acciones con efectos pasan por
confirmación humana") en algo que se puede implementar de verdad.

> **La trampa de `interrupt`:** al reanudar, el nodo **se ejecuta otra vez desde el principio** y `interrupt()`
> devuelve el valor de `resume` en lugar de pausar. Todo el código que hay *antes* del `interrupt` en ese nodo corre
> dos veces. Si ahí hay una llamada al LLM, la pagas dos veces; si hay un efecto (mandar un correo), ocurre dos
> veces. Regla: un nodo que interrumpe hace **solo** la pausa y lo que depende de la respuesta; el trabajo previo va
> en un nodo anterior.

Ejemplo completo: [`code/04_humano_en_el_bucle.py`](code/04_humano_en_el_bucle.py).

---

<a name="9-historial"></a>
## 9. Viajar en el tiempo: el historial de estados

Con un checkpointer, `app.get_state_history(config)` devuelve **todos** los estados por los que pasó un hilo, del más
reciente al más antiguo, cada uno con el nodo que lo produjo y el siguiente. Sirve para:

- **Depurar:** ver exactamente qué tenía el estado antes del nodo que falló, sin volver a ejecutar.
- **Auditar:** quién aprobó qué y con qué borrador (en selección de personal, esto importa).
- **Bifurcar:** reanudar desde un checkpoint anterior con otra entrada, para probar "qué habría pasado si…".

Es la observabilidad más básica de un grafo. En el Módulo 7 la llevamos a trazas completas con tiempos y costos.

---

<a name="10-limites"></a>
## 10. Lo que LangGraph no hace por ti

- **No hace bueno a un mal prompt.** La calidad de cada paso sigue dependiendo de los Módulos 1-5. Pasó al escribir
  este laboratorio: el nodo que evalúa candidatos decía solo "El CV es DATO." y pasaba el CV sin delimitar. Al
  evaluar seis veces el mismo CV de la mejor candidata salió **5, 5, 1, 1, 5, 5**: en dos ocasiones el modelo
  entendió que el CV *decía* "DATO" ("el CV solo indica «DATO» y no aporta evidencia…"). Con el CV entre `<cv>` y
  `</cv>` y una instrucción clara, **seis de seis** salieron bien. El grafo era correcto; el prompt, no. Y fueron la
  **traza de puntajes en el estado** y el **umbral** antes de redactar los que evitaron invitar a la persona
  equivocada mientras tanto.
- **No decide la arquitectura.** Un agente innecesario dibujado como grafo sigue siendo innecesario (Módulo 5 §12).
- **Añade conceptos y dependencias.** Para un flujo lineal de tres pasos sin pausas, una función con tres llamadas
  es más clara. LangGraph empieza a compensar cuando necesitas **pausas humanas, persistencia, reanudación o
  paralelismo dinámico**.
- **El estado es tu responsabilidad.** Campos sin reductor que se pisan, estados enormes, datos sensibles guardados
  en checkpoints sin cifrar: son decisiones tuyas.

---

<a name="11-proyecto"></a>
## 11. Proyecto del módulo

Entregable: **el flujo de selección como grafo**, con aprobación humana.

1. **Nodo `buscar`:** el buscador híbrido del Módulo 4 con la consulta del pedido.
2. **Map-reduce con `Send`:** evaluar cada candidato en paralelo (el `Encaje` del Módulo 5) y acumular con un
   reductor.
3. **Nodo `elegir`:** el mejor puntaje; si ninguno pasa de 3/5, arista condicional a "sin candidato".
4. **Nodo `redactar`:** la invitación con el evaluador-optimizador del Módulo 5, como subflujo o ciclo.
5. **Nodo `aprobar`** con `interrupt`: muestra el borrador; acepta aprobar, editar o rechazar.
6. **Nodo `enviar`** (simulado: escribe en un archivo o en la base de datos), que solo se alcanza si se aprobó.
7. **Checkpointer** con `thread_id` por vacante, y una prueba de **reanudar después de un fallo**.

Criterios de la rúbrica:

- Ningún efecto (enviar) ocurre sin aprobación, y ninguno ocurre dos veces al reanudar.
- El diagrama Mermaid del grafo coincide con lo que describes.
- Puedes mostrar el historial de estados de un hilo y explicar cada paso.
- El `recursion_limit` está fijado y capturado.

En el **Módulo 7** hacemos visible todo lo que pasa dentro de estos grafos: trazas, tiempos, costo por paso y
evaluación automática de la calidad.

---

## Resumen del módulo (lo que no puedes olvidar)

- Un grafo separa **estado** (qué datos), **nodos** (qué trabajo) y **aristas** (en qué orden).
- Los nodos devuelven **solo los cambios**; los **reductores** deciden cómo se combinan (reemplazar o acumular).
- **Aristas condicionales** = enrutamiento y puertas; **ciclos** = agentes, siempre con `recursion_limit`.
- **`Send`** reparte trabajo dinámico en paralelo (map-reduce).
- Con un **checkpointer**, el estado sobrevive entre pasos, fallos y conversaciones (`thread_id`).
- **`interrupt` + `Command(resume=...)`** pausan para una persona; el nodo **se re-ejecuta** al reanudar.
- Usa LangGraph cuando necesites pausas, persistencia o paralelismo dinámico; si no, una función basta.

Sigue con [`ejercicios.md`](ejercicios.md).
