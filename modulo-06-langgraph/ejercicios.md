# Módulo 6 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Se hacen en el **Laboratorio** de la app; la
**celda libre** comparte variables con las anteriores, así que puedes usar `app`, `CONFIG`, etc. sin recrearlos.

---

### Ejercicio 1 — Un nodo más
En [`code/01_primer_grafo.py`](code/01_primer_grafo.py), añade un nodo `deduplicar` entre `buscar` y `formatear` que
quite nombres repetidos y escriba en la bitácora cuántos quitó. Comprueba en el diagrama Mermaid que quedó donde
querías.

### Ejercicio 2 — El reductor que faltaba
En el mismo script, el ejemplo final falla con `InvalidUpdateError`. Arréglalo **sin** quitar el paralelismo:
cambia el tipo de `resultados` para que acumule. ¿Qué devuelve ahora el grafo? ¿En qué orden quedan los dos
valores, y puedes contar con ese orden?

### Ejercicio 3 — Tres caminos
En [`code/02_condicionales.py`](code/02_condicionales.py), el enrutador tiene dos destinos. Añade un tercero:
consultas de más de 6 palabras van a `buscar_semantica`. Recuerda añadir el destino al mapa de la arista
condicional. ¿Qué pasa si te olvidas de añadirlo al mapa?

### Ejercicio 4 — Pausa interactiva
En la app, ejecuta [`code/04_humano_en_el_bucle.py`](code/04_humano_en_el_bucle.py) y luego, en la **celda libre**,
inicia un hilo nuevo y **detente** en la pausa:

```python
cfg = {"configurable": {"thread_id": "mi-prueba"}}
pausa = hasta_la_pausa(cfg)
pausa
```

Lee el borrador. En **otra** ejecución de la celda libre, reanúdalo tú con tu decisión
(`app.invoke(Command(resume={"aprobado": ..., "edicion": ...}), cfg)`). ¿Qué tiene `app.get_state(cfg)` entre las
dos ejecuciones?

### Ejercicio 5 — Provocar la trampa de `interrupt`
Mueve la llamada al LLM de `redactar` **dentro** de `aprobar`, antes del `interrupt`. Ejecuta el flujo completo con
`c.reiniciar_contador()` antes y `c.resumen_costo()` después. ¿Cuántas llamadas hubo en comparación con la versión
original? ¿El borrador que viste en la pausa es el mismo que se envió?

### Ejercicio 6 — El umbral
Cambia `UMBRAL` a 6 (imposible de alcanzar) y ejecuta. ¿Qué nodos se ejecutaron, según el historial
(`get_state_history`)? ¿Por qué es importante que el grafo termine "sin candidato" en vez de lanzar un error?

### Ejercicio 7 — Map-reduce con un orquestador
En [`code/05_map_reduce.py`](code/05_map_reduce.py), la lista de ramas la decide la búsqueda. Cámbialo para que la
decida un LLM orquestador (Módulo 5 §7): un nodo `planificar` devuelve un `Plan` con 2-4 **criterios** de
evaluación ("liderazgo", "tiempo real", ...), y `Send` crea una rama por **criterio**, cada una evaluando a los 3
mejores candidatos solo en ese criterio. Acota el número de criterios con `Field(max_length=4)`.

### Ejercicio 8 — Proyecto
Monta el grafo completo del §11 del manual: buscar → map-reduce de evaluación → elegir con umbral → redactar con el
evaluador-optimizador del Módulo 5 como **ciclo** dentro del grafo → aprobar (`interrupt`) → enviar. Usa un
`thread_id` por vacante. Haz que `enviar` falle a propósito una vez (`raise` la primera vez) y demuestra que al
reanudar el hilo **no** se vuelve a pagar la evaluación ni la redacción.

---

<details>
<summary><b>Soluciones</b></summary>

**1.**
```python
def deduplicar(s):
    unicos = list(dict.fromkeys(s["resultados"]))
    return {"resultados": unicos, "bitacora": [f"deduplicar: quitó {len(s['resultados']) - len(unicos)}"]}

g.add_node("deduplicar", deduplicar)
# reemplaza la arista buscar -> formatear por:
g.add_edge("buscar", "deduplicar")
g.add_edge("deduplicar", "formatear")
```

**2.** `resultados: Annotated[list[str], operator.add]`. El grafo devuelve `["de uno", "de dos"]` (o al revés).
**No** cuentes con el orden: los dos nodos corren en el mismo paso y el orden de combinación no es un contrato. Si el
orden importa, ordena en un nodo posterior o guarda cada resultado con una clave (por ejemplo, un `dict` con su
propio reductor que combine diccionarios).

**3.**
```python
def clasificar(s):
    n = len(s["consulta"].split())
    return {"modo": "bm25" if n <= 2 else ("semantica" if n > 6 else "hibrida")}

ra.add_node("buscar_semantica", buscador("semantica"))
ra.add_conditional_edges("clasificar", lambda s: s["modo"],
                         {"bm25": "buscar_bm25", "hibrida": "buscar_hibrida", "semantica": "buscar_semantica"})
ra.add_edge("buscar_semantica", END)
```
Si la función devuelve un destino que no está en el mapa, la ejecución falla al llegar a esa consulta: el mapa es la
lista cerrada de destinos válidos. Por eso conviene declararlo: el error sale pronto y con un mensaje claro.

**4.** Entre las dos ejecuciones, `app.get_state(cfg).next` es `('aprobar',)` y `values` tiene el candidato, el
borrador y los puntajes: el estado vive en el checkpointer, nada está bloqueado esperándote. Podrías reanudar dentro
de una hora (mientras no se reinicie la API, porque `InMemorySaver` vive en memoria).

**5.** Con la llamada antes del `interrupt`, el nodo `aprobar` la ejecuta **dos veces** (al pausar y al reanudar):
hay una llamada más por hilo que en la versión original. Y el borrador enviado **no es** el que viste en la pausa,
porque se generó otro al reanudar. Es exactamente el peligro de la §8: lo que ves al aprobar no es lo que se ejecuta.

**6.** El historial muestra `elegir` y luego el final, sin `redactar` ni `aprobar`. Terminar limpio importa porque
"no hay candidato que cumpla" es un **resultado válido** del proceso, no un fallo: quien opera el sistema debe poder
distinguirlo de un error técnico, y los dos llevan a acciones distintas (ampliar la búsqueda o arreglar el código).

**7.**
```python
class Plan(BaseModel):
    criterios: list[str] = Field(min_length=2, max_length=4)

def planificar(s):
    p = c.llm(Plan, "Lista 2-4 criterios para evaluar candidatos a esta vacante.", s["vacante"])
    return {"criterios": p.criterios}

def repartir(s):
    return [Send("evaluar_criterio", {"criterio": k, "candidatos": s["candidatos"][:3]}) for k in s["criterios"]]
```
Cada rama devuelve sus puntajes en una lista acumulada, y un nodo final los suma por candidato. El `max_length=4`
pone un techo al costo: sin él, un orquestador entusiasta podría proponer 15 criterios y 45 llamadas.

**8.** La clave es que, con checkpointer, cuando `enviar` falla el grafo queda en ese paso. Al volver a invocar el
mismo `thread_id` con `app.invoke(None, cfg)` continúa desde `enviar`, sin repetir evaluación ni redacción. Verifícalo
con `c.resumen_costo()`: el número de llamadas no debe aumentar al reanudar. Para la aprobación, usa
`Command(resume=...)` como en el ejercicio 4.

</details>
