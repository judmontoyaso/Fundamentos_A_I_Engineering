# Módulo 2 · Máquinas de estados, checkpoints e idempotencia

> **Objetivo:** que el procedimiento lo haga cumplir el código, no el prompt, y que una ejecución que se cae a mitad
> de camino se pueda reanudar sin repetir lo que ya tuvo efectos fuera.
>
> **Lo que te llevas:** una máquina de estados con invariantes que bloquea una terna sin verificar, un checkpoint en
> disco después de cada paso y una caché de idempotencia que impide agendar dos veces la misma entrevista.

Índice:

1. [El prompt no es un contrato](#1-prompt)
2. [Estado explícito e invariantes](#2-estado)
3. [Laboratorio 1: la guarda que atrapa el descuido](#3-lab1)
4. [Qué guardar en un checkpoint](#4-checkpoint)
5. [Idempotencia: la única forma segura de reintentar](#5-idempotencia)
6. [Laboratorio 2: caída en el paso 6 y reanudación](#6-lab2)
7. [Cómo lo resuelven los frameworks](#7-frameworks)
8. [Lista de revisión](#8-lista)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 2 · Máquina de estados, checkpoints e idempotencia](/infografias/agentes-m2-maquina-estados-checkpoints.png)

---

<a name="1-prompt"></a>
## 1. El prompt no es un contrato

El system prompt del módulo 0 dice "verifica la elegibilidad de cada candidato antes de entregar la terna". El modelo
lo cumple casi siempre. "Casi siempre" es el problema: cuando el historial es largo, cuando una observación es ambigua
o cuando el modelo concluye que "ya es obvio" que un candidato sirve, se salta el paso. Y la terna sale con alguien
que está en enfriamiento o que no habla el inglés que pide la vacante.

Todo lo que **tiene que pasar siempre** se saca del prompt y se escribe en el controlador: el orden obligatorio de los
pasos, lo que debe estar comprobado antes de una acción, lo que no puede repetirse. El prompt queda para orientar; el
código, para garantizar.

---

<a name="2-estado"></a>
## 2. Estado explícito e invariantes

El controlador mantiene un **estado de negocio** aparte del historial de mensajes: lo que ya se sabe con certeza
porque lo devolvió una herramienta. En [`code/01_maquina_de_estados.py`](code/01_maquina_de_estados.py):

```python
@dataclass
class EstadoPreseleccion:
    vacante_id: str
    vacante_cargada: bool = False
    candidatos_buscados: list[str] = field(default_factory=list)
    verificados: dict[str, bool] = field(default_factory=dict)   # candidato -> elegible según la regla
```

Y dos funciones:

- `registrar_resultado(herramienta, args, res)` actualiza el estado **solo con resultados exitosos de herramientas**,
  nunca con lo que el modelo afirma en texto.
- `validar_transicion(herramienta, args)` se llama **antes** de ejecutar y devuelve un bloqueo si la llamada rompe una
  precondición:
  - no se busca sin haber cargado la vacante;
  - no se entrega una terna con candidatos que no pasaron por `verificar_elegibilidad`;
  - no se entrega una terna con candidatos que la verificación marcó como no elegibles.

Esto es una **máquina de estados** aunque no tenga un diagrama: cada herramienta es una transición, y cada transición
tiene precondiciones que se comprueban con datos. La ventaja frente a confiar en el modelo es que una invariante en
código se cumple el 100 % de las veces, y se puede probar con un test.

---

<a name="3-lab1"></a>
## 3. Laboratorio 1: la guarda que atrapa el descuido

El laboratorio usa un modelo descuidado al extremo (`p_descuido=1.0`): encuentra 4 candidatos para `VAC-101` y los da
a todos por buenos sin verificar ninguno.

| | Sin guarda | Con guarda |
|---|---|---|
| Terna entregada | `CAND-01`, `CAND-03`, `CAND-04`, `CAND-07` | `CAND-01`, `CAND-03` |
| ¿Correcta? | No | Sí |
| Bloqueos | ninguno | 1: "intentaste incluir [...] sin haber llamado antes a verificar_elegibilidad" |

Sin guarda, `CAND-04` (1 año de experiencia, inglés A2) y `CAND-07` (inglés B1, vive en Medellín para una vacante
híbrida en Bogotá) llegan a la terna. Con guarda, el intento de cierre se bloquea, el controlador ejecuta las
verificaciones que faltaban y entrega solo a los elegibles.

Hay dos formas de reaccionar a una transición bloqueada, y el laboratorio usa la segunda:

1. **Devolver el bloqueo al modelo** como observación de error, para que haga lo que falta. Más autónomo, cuesta más
   pasos y depende de que el modelo entienda el mensaje.
2. **Completar en código lo que falta** (aquí: verificar a los pendientes) y continuar. Más barato y determinista;
   aplicable cuando lo que falta es mecánico y no requiere criterio.

Elige la segunda siempre que puedas escribir lo que falta sin el modelo.

---

<a name="4-checkpoint"></a>
## 4. Qué guardar en un checkpoint

Un agente de 13 pasos con un modelo real tarda entre 20 segundos y varios minutos. En ese tiempo pasan cosas: el
proceso se reinicia en un despliegue, el proveedor devuelve un 529, el contenedor se queda sin memoria. Si el estado
vive solo en memoria, se pierde todo, incluido el dinero gastado.

Un **checkpoint** es una fotografía serializable de la ejecución, guardada después de cada paso. Debe permitir que
**otro proceso** la reanude. Para eso necesita:

- **Los mensajes completos**: el historial que se le envía al modelo, con las llamadas y sus resultados.
- **El estado de negocio** (sección 2) y el número de paso.
- **La caché de idempotencia** (sección 5): qué llamadas con efectos ya se ejecutaron y qué devolvieron.
- **El gasto acumulado**, para que el presupuesto no se reinicie al reanudar.
- **Si está pausada esperando a un humano**, y qué propuesta espera (módulo 6).

Dónde guardarlo: un archivo JSON vale para un laboratorio; en producción, una fila en Postgres o una clave en Redis
por `ejecucion_id`, escrita en la misma transacción que marca el paso como hecho.

---

<a name="5-idempotencia"></a>
## 5. Idempotencia: la única forma segura de reintentar

Reanudar desde un checkpoint tiene una trampa. Si el proceso se cayó **después** de llamar a `agendar_entrevista` pero
**antes** de guardar el checkpoint, al reanudar el modelo volverá a pedir esa entrevista, y la reclutadora recibirá dos
invitaciones.

La solución es que repetir una llamada con efectos **no repita el efecto**. Cada llamada recibe una clave de
idempotencia derivada de lo que identifica la operación:

```python
def clave_idempotencia(herramienta, argumentos):
    cuerpo = json.dumps({"h": herramienta, "a": argumentos}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()[:16]
```

Antes de ejecutar, el controlador mira si la clave ya está en la caché. Si está, devuelve el resultado guardado sin
tocar el sistema externo. Dos matices de producción:

- **La clave debe incluir el id de la ejecución** cuando la misma acción es legítima en ejecuciones distintas (dos
  procesos de selección pueden entrevistar al mismo candidato). Sin él, la segunda ejecución quedaría bloqueada.
- **La caché local no basta si la caída ocurre entre el efecto y el guardado.** Por eso las APIs serias aceptan una
  cabecera de idempotencia (`Idempotency-Key` en Stripe; `X-Idempotency-Key` en Mercado Pago): el servidor externo
  recuerda la clave y no duplica. La web de este curso la usa al crear el cobro. Si el sistema externo no la soporta,
  consulta antes de crear ("¿ya existe una entrevista para este candidato y esta vacante?").

---

<a name="6-lab2"></a>
## 6. Laboratorio 2: caída en el paso 6 y reanudación

[`code/02_checkpoints_e_idempotencia.py`](code/02_checkpoints_e_idempotencia.py) corre el agente con la herramienta
`agendar_entrevista` disponible y un modelo que agenda una entrevista con cada elegible. El estado se guarda en
`salida/m2_checkpoint.json` después de cada paso.

1. **Primera corrida:** el proceso "se cae" al llegar al paso 6. Quedan guardados 6 pasos y 6 llamadas en la caché.
2. **Reanudación:** un nuevo ejecutor carga el checkpoint y continúa desde el paso 6.
3. **Prueba de idempotencia:** se repite a propósito una llamada a `agendar_entrevista` ya hecha.

Resultado:

| | |
|---|---|
| Pasos totales (antes y después de la caída) | 13 |
| Terna | `CAND-01`, `CAND-03` |
| Entrevistas creadas en el calendario externo | 2 (una por elegible) |
| Reintento duplicado | bloqueado por la caché |

Abre `salida/m2_checkpoint.json` después de correrlo: ahí está todo lo necesario para que otra máquina continúe la
ejecución. Esa misma estructura es la que se muestra a un humano cuando el agente se pausa para pedir aprobación.

---

<a name="7-frameworks"></a>
## 7. Cómo lo resuelven los frameworks

Lo que escribiste a mano es lo que ofrecen los frameworks de orquestación. En LangGraph (visto en el curso de AI
Engineering): un grafo de nodos con un `State` tipado es la máquina de estados, un *checkpointer* (`SqliteSaver`,
`PostgresSaver`) guarda el estado después de cada nodo bajo un `thread_id`, e `interrupt` pausa la ejecución para un
humano. Temporal y otros motores de *durable execution* hacen lo mismo a nivel de proceso: reejecutan el código desde el
historial de eventos y exigen que las actividades con efectos sean idempotentes.

Ninguno resuelve por ti la idempotencia del efecto externo: eso sigue siendo responsabilidad de cada herramienta.

---

<a name="8-lista"></a>
## 8. Lista de revisión

- [ ] Las reglas que deben cumplirse siempre están en el controlador, no solo en el prompt.
- [ ] El estado de negocio se actualiza con resultados de herramientas, nunca con afirmaciones del modelo.
- [ ] Cada transición crítica tiene precondiciones comprobadas antes de ejecutarse, con un test que las cubre.
- [ ] Hay un checkpoint después de cada paso, con mensajes, estado, caché de idempotencia y gasto.
- [ ] Toda herramienta con efectos es idempotente, idealmente también en el sistema externo.
- [ ] Sabes reanudar una ejecución desde otro proceso, y lo has probado matando el proceso a mitad.

En el siguiente módulo atacamos el costo: un historial que crece en cada paso.
