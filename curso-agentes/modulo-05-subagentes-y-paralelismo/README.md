# Módulo 5 · Subagentes, delegación y ejecución paralela

> **Objetivo:** saber cuándo dividir un agente en un orquestador y varios trabajadores, y cuándo es tirar tokens.
>
> **Lo que te llevas:** las dos razones reales para usar subagentes (contexto limpio y latencia), un orquestador con
> trabajadores en paralelo que reduce la latencia 3,8 veces en el laboratorio, un map-reduce sobre todo el ATS, y el
> costo que casi nadie cuenta: los sistemas multiagente gastan bastantes más tokens.

Índice:

1. [Roles teatrales contra límites físicos](#1-roles)
2. [El patrón orquestador-trabajadores](#2-patron)
3. [Laboratorio 1: secuencial contra paralelo](#3-lab1)
4. [Laboratorio 2: map-reduce sobre el ATS](#4-lab2)
5. [El costo de dividir](#5-costo)
6. [Paralelismo en producción](#6-produccion)
7. [Cuándo sí y cuándo no](#7-decision)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 5 · Patrón orquestador y subagentes en paralelo con ventanas de contexto limpias](/infografias/agentes-m5-subagentes-map-reduce.png)

---

<a name="1-roles"></a>
## 1. Roles teatrales contra límites físicos

Un diseño frecuente de "sistema multiagente" reparte personajes: un *Agente Gerente*, un *Agente Analista* y un
*Agente Crítico* que conversan entre sí. Se ve bien en un diagrama y se comporta mal en producción: cada mensaje entre
agentes es una llamada más, el error compuesto del módulo 0 se multiplica por el número de agentes, y nadie sabe qué
agente decidió qué.

Hay dos razones de ingeniería para dividir el trabajo, y ninguna tiene que ver con personajes:

1. **Contexto limpio.** Si hay que estudiar a fondo 8 candidatos (CV, repositorios, entrevistas previas: unos 4.000
   tokens cada uno), hacerlo en un solo hilo deja 32.000 tokens de detalle en la ventana del agente principal, con los
   problemas de costo y atención del módulo 3. Con un trabajador por candidato, cada uno lee solo lo suyo y devuelve un
   dictamen de unas decenas de tokens.
2. **Latencia.** Si cada evaluación tarda 3 segundos, 8 en serie son 24 segundos; en paralelo, lo que tarde la más
   lenta.

Si tu problema no tiene ninguna de las dos, no necesitas subagentes.

---

<a name="2-patron"></a>
## 2. El patrón orquestador-trabajadores

- El **orquestador** planifica, reparte subtareas acotadas y combina los resultados. No lee los documentos pesados.
- Cada **trabajador** recibe solo su objetivo (evaluar un candidato), las herramientas mínimas para hacerlo y un
  esquema de salida cerrado. Empieza con un contexto vacío y termina al entregar su resultado.
- **La comunicación es solo vertical**: los trabajadores responden al orquestador y no hablan entre sí. Eso mantiene
  la trayectoria auditable.

El contrato de salida del trabajador es lo más importante del patrón. Si devuelve texto libre, el orquestador tiene que
interpretarlo (otra fuente de error) y vuelve a crecer su contexto. Si devuelve un esquema cerrado
(`{"candidato_id", "elegible", "motivos_bloqueo"}`), combinar es código.

---

<a name="3-lab1"></a>
## 3. Laboratorio 1: secuencial contra paralelo

En [`code/01_orquestador_trabajadores.py`](code/01_orquestador_trabajadores.py), el orquestador carga la vacante y
busca candidatos en código (son pasos fijos: no hace falta que un modelo los decida), y lanza un trabajador por
candidato. Cada trabajador hace su llamada al modelo con la ficha completa y devuelve un dictamen compacto. El modelo
simulado tarda 60 ms por respuesta para que la latencia se note.

Resultado de una corrida (la latencia varía un poco entre corridas):

| | Secuencial | Paralelo (`ThreadPoolExecutor`) |
|---|---|---|
| Candidatos evaluados | 4 | 4 |
| Latencia total | 245,7 ms | 64,0 ms |
| Aceleración | | **3,84×** |
| Tokens leídos por los trabajadores | 792 | 792 |
| Tokens que recibe el orquestador | 37 | 37 |
| Terna | `CAND-01`, `CAND-03` | `CAND-01`, `CAND-03` |

Dos lecturas:

- **El paralelismo baja la latencia, no el costo.** Los trabajadores leen lo mismo en los dos modos.
- **El orquestador recibe 37 tokens en vez de 792.** Esa es la ganancia de contexto: lo que el orquestador necesita
  para decidir son cuatro veredictos, no cuatro fichas.

Las llamadas al modelo esperan la red, así que hilos o `asyncio` sirven aunque Python tenga el GIL: el tiempo se va en
esperar, no en calcular.

---

<a name="4-lab2"></a>
## 4. Laboratorio 2: map-reduce sobre el ATS

[`code/02_map_reduce_cvs.py`](code/02_map_reduce_cvs.py) cruza las 2 vacantes con los 8 candidatos: 16 evaluaciones
independientes.

- **Map:** cada par `(vacante, candidato)` se evalúa por separado, sin estado compartido.
- **Reduce:** se agrupa por vacante, se filtran los elegibles y se ordenan por disponibilidad y aspiración.

Resultado: `VAC-101` → `CAND-03` (10 días, 5.900 USD) y `CAND-01` (15 días, 6.200 USD); `VAC-102` → `CAND-05`. Las
dos coinciden con la terna correcta.

Map-reduce es la forma más segura de paralelismo con LLMs: cada tarea es independiente, el resultado de cada una se
puede validar con su esquema, y el reduce es código determinista. Si una tarea falla, se reintenta sola sin repetir
las demás.

---

<a name="5-costo"></a>
## 5. El costo de dividir

Los subagentes **no** ahorran tokens en general. Cada trabajador repite el system prompt, los esquemas de sus
herramientas y parte del contexto de la tarea, y el orquestador hace sus propias llamadas para planificar y combinar.
Anthropic, al describir su sistema de investigación multiagente (2025), contó que sus agentes usaban unas 4 veces más
tokens que un chat, y los sistemas multiagente unas 15 veces más; a cambio, en tareas de investigación amplias, el
multiagente rendía bastante mejor que un solo agente.

Es un intercambio: más tokens a cambio de menos latencia y mejor calidad en tareas que se dividen bien. Antes de
dividir, haz la cuenta para tu caso (ejercicio 3): tokens del monolito, tokens de orquestador más trabajadores,
latencia de cada uno, y cuánto vale para tu usuario cada segundo ahorrado.

---

<a name="6-produccion"></a>
## 6. Paralelismo en producción

- **Límites del proveedor.** Lanzar 40 trabajadores a la vez dispara errores 429. Acota la concurrencia con un pool de
  tamaño fijo o un `asyncio.Semaphore` y reintenta con espera exponencial.
- **Presupuesto global.** Cada trabajador tiene su presupuesto, y el orquestador uno que incluye el de todos. Si no,
  diez trabajadores "dentro de su límite" suman diez veces lo esperado.
- **Fallos parciales.** Decide qué hacer si 1 de 8 trabajadores falla: reintentar, marcar ese candidato como "no
  evaluado" o abortar. Lo que no se puede hacer es tratarlo como "no elegible" sin decirlo.
- **Trazabilidad.** Cada trabajador registra su trayectoria con el id de la ejecución padre. Sin eso, depurar una
  terna equivocada es adivinar qué trabajador se equivocó.
- **Efectos.** Los trabajadores de este patrón solo leen. Si un trabajador puede escribir, dos trabajadores pueden
  escribir lo mismo a la vez: idempotencia (módulo 2) obligatoria.

---

<a name="7-decision"></a>
## 7. Cuándo sí y cuándo no

| Situación | ¿Subagentes? |
|---|---|
| Muchas subtareas independientes con documentos grandes | Sí: contexto limpio y paralelismo |
| La latencia importa y las subtareas no dependen unas de otras | Sí, en paralelo |
| Pasos que dependen del anterior (buscar, luego filtrar, luego decidir) | No: un agente o un workflow |
| Subtareas que comparten mucho contexto | No: repetirías ese contexto en cada trabajador |
| Una tarea corta y barata | No: el costo del orquestador supera la ganancia |

En nuestro ATS, con 4 candidatos y fichas pequeñas, un solo agente basta. El patrón empieza a pagar con decenas de
candidatos o con documentos largos por candidato.

En el siguiente módulo, el agente aprende a no hacer cosas: aprobación humana y defensa contra inyección.
