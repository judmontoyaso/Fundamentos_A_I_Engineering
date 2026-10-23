# Módulo 9 · Ejercicios

Son ejercicios de proyecto: cada uno cambia algo del sistema y se valida con la evaluación de punta a punta
([`code/03_evaluacion_e2e.py`](code/03_evaluacion_e2e.py)). Anota los números **antes** de cambiar nada.

---

### Ejercicio 1 — Tu línea base
Ejecuta `00_sistema.py`, `01_ingesta.py` y `03_evaluacion_e2e.py` dos veces seguidas. Anota en una tabla todas las
métricas de las dos ejecuciones. ¿Qué números cambian entre ejecuciones sin que hayas tocado nada? Esa variación es el
"ruido" contra el que tendrás que comparar cualquier mejora.

### Ejercicio 2 — Un CV nuevo y difícil
Añade a `00_datos_cvs.py` dos CVs: uno escrito todo en una línea, sin secciones, y uno de alguien con experiencia en
streaming **sin** usar esa palabra ("procesamiento de eventos con colas de mensajes"). Añade a `03` un pedido para
cada uno. ¿El sistema los encuentra? Si no, ¿falla la extracción, la búsqueda o la evaluación? Usa la traza para
saberlo.

### Ejercicio 3 — Optimiza el nodo más caro
Siguiendo el §6 del manual, cambia la política de salida y el juez de fidelidad para que usen un modelo más barato
(define una variable `MODELO_GUARDRAILS` en `.env` y úsala en esas dos llamadas). Corre la evaluación. ¿Bajó la
latencia o el costo? ¿Se mantuvo la calidad? ¿Lo aceptarías?

### Ejercicio 4 — Ahorrar la extracción de memoria
Añade al nodo `memoria` una regla barata que decida si vale la pena llamar al extractor (por ejemplo, solo si el
pedido contiene "exijo", "prefiero", "necesito que", "requisito"…). Mide cuántas llamadas ahorra en la evaluación y si
algún recuerdo importante se pierde (prueba el caso de Ana del `02`).

### Ejercicio 5 — Invitar con aprobación
Añade al grafo una rama: si el pedido contiene "invita a", el sistema redacta la invitación para el candidato mejor
puntuado y **se detiene** con `interrupt` (Módulo 6) hasta que el reclutador la apruebe. Recuerda: el correo del
candidato está en `s.contactos`, fuera del índice; úsalo solo en el nodo que "envía".

### Ejercicio 6 — El asistente en la app
La app ya sirve el sistema en la página **Asistente de selección (en vivo)**: lee
[`app/backend/curso_api/asistente.py`](../app/backend/curso_api/asistente.py) y los endpoints `/api/asistente/*` de
`main.py`. Haz en la página los cinco pedidos de ejemplo y abre la traza de cada uno. Después responde: el `usuario`
llega en el cuerpo de la petición; ¿qué puede hacer cualquiera que conozca el nombre de otro reclutador? ¿Qué
tendrías que cambiar para que salga de un inicio de sesión?

### Ejercicio 7 — Busca un sesgo
Pide a otra persona 10 pedidos que intenten, de forma disimulada, que el sistema discrimine o filtre datos personales.
Pásalos por el sistema. ¿Cuántos se colaron, y en qué capa debió atraparlos? Convierte cada fallo en un caso de `03`.

### Ejercicio 8 — Tu informe final
Escribe una página para alguien que tiene que decidir si usar este asistente en su equipo de selección. Incluye: qué
hace, qué números tiene (con su tamaño de muestra), qué riesgos conoces, qué falta para producción (§7) y tu
recomendación. Es el entregable que de verdad se le pide a un AI engineer.

### Ejercicio 9 — Volver a K_CV = 4 sin perder a nadie
El arreglo 5 del §4 subió `K_CV` a 6 y la consulta cuesta un tercio más. Escribe 5 pedidos **largos** (con dos o tres
requisitos, como los de un reclutador real) con sus candidatos correctos y mide solo la recuperación, sin llamadas al
modelo: el puesto de cada correcto con `s.buscar(pedido, k_cv=10)`. Después prueba una de las causas: otro modelo de
embeddings (`EMB_BACKEND=openai` en `app/backend/.env` y reinicia la API) o un reranking del top 8 (Módulo 4,
`06_reranking.py`). ¿Con cuál entran todos los correctos en los 4 primeros? ¿Cuánto cuesta cada opción frente a evaluar
2 candidatos más?

---

<details>
<summary><b>Pistas</b></summary>

**1.** Lo normal es que varíen la latencia (mucho, según la carga del proveedor), los tokens de razonamiento y, a
veces, algún puntaje de evaluación. Si una mejora no supera esa variación, no puedes afirmar que mejoró.

**2.** Para separar dónde falla: mira en la traza si el candidato aparece en `buscar` (si no, es recuperación) y
qué puntaje le dio `evaluar` (si es bajo, es evaluación). Si la extracción lo dejó sin skills, es ingesta.

**3.** Un modelo más barato suele acertar en las clasificaciones de política. El juez de fidelidad es más delicado:
mira en especial los casos sutiles del Módulo 7 (exageraciones, números cambiados). Acepta el cambio solo si la
evaluación no empeora más allá del ruido del ejercicio 1.

**4.** Una regla así ahorra casi todas las extracciones de la evaluación (los pedidos de búsqueda no expresan
preferencias), pero puede perder requisitos dichos de otra forma ("solo me sirven perfiles con inglés"). Es un
equilibrio entre costo y memoria: mídelo con conversaciones reales.

**5.** La estructura es la del `04_humano_en_el_bucle.py` del Módulo 6: un nodo que redacta, un nodo que solo hace
`interrupt` y un nodo que "envía". El grafo necesita un checkpointer y un `thread_id` por consulta para poder
reanudarse.

**6.** El endpoint es una función de pocas líneas. Lo difícil es la identidad: con el `usuario` en el cuerpo,
cualquiera puede leer **y borrar** la memoria de otro reclutador poniendo su nombre (la página lo permite). Tiene que
salir de un token validado por el backend (una sesión o un JWT), y el endpoint debe ignorar cualquier `usuario` que
mande el cliente. Para uso personal en `127.0.0.1` es aceptable; en un servidor compartido, no.

**7.** Los que suelen colarse son los indirectos: código postal o barrio, universidad, "cultura de la empresa",
"presencia". Algunos son legítimos según el contexto. Por eso este ejercicio necesita a otra persona, y por eso cada
caso dudoso merece una discusión, no solo una regla.

**8.** No hay solución única. Una buena señal: que alguien que no hizo el curso entienda tu recomendación y sus
límites sin preguntarte nada.

**9.** Con la medición del §4 como referencia: con MiniLM, el modo solo denso dejaba a la correcta hasta el puesto 9 en
pedidos largos y la fusión con RRF, en el 5-6. Al escribir el curso, `text-embedding-3-small` en modo solo denso puso
a las dos correctas en los puestos 3 y 4 en los mismos pedidos largos: dentro del top 4, pero justo. Un reranking con
LLM ordena el top por el pedido completo, a cambio de una llamada y unos segundos por consulta (Módulo 4). Un embedding
mejor no añade llamadas pero obliga a reindexar. Compara contra la alternativa actual (2 evaluaciones más, en
paralelo) y decide con los números de tus 5 pedidos, no con los de este manual.

</details>
