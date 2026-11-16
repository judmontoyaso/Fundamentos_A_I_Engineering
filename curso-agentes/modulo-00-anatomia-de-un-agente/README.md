# Módulo 0 · Cuándo usar (y cuándo no usar) un agente

> **Objetivo:** decidir con números cuándo un problema necesita un bucle autónomo con herramientas y cuándo basta un
> flujo en código, y construir el primer freno que todo agente necesita: un presupuesto de pasos, tokens y dinero que
> vive fuera del modelo.
>
> **Lo que te llevas:** la escalera de autonomía, la cuenta del error compuesto, el bucle de un agente escrito a mano
> (sin frameworks) y un controlador que corta una ejecución atascada antes de que te cueste.

Índice:

1. [Qué es un agente, sin marketing](#1-que-es)
2. [La escalera de autonomía](#2-escalera)
3. [El error compuesto: por qué cada paso cuesta](#3-error)
4. [El entorno del curso: el ATS y el modelo simulado](#4-entorno)
5. [Laboratorio 1: workflow contra agente](#5-lab1)
6. [Anatomía del bucle](#6-bucle)
7. [Laboratorio 2: el presupuesto fuera del modelo](#7-lab2)
8. [Qué hacer con esto en tu proyecto](#8-decision)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 0 · La escalera de autonomía y el riesgo compuesto por paso](/infografias/agentes-m0-escalera-autonomia.png)

---

<a name="1-que-es"></a>
## 1. Qué es un agente, sin marketing

Un **agente** es un programa en el que un modelo de lenguaje decide, en cada vuelta de un bucle, **qué herramienta
llamar a continuación y cuándo terminar**. Todo lo demás (memoria, planificación, subagentes, MCP) son añadidos sobre
esa idea.

La distinción que más sirve en la práctica es la de Anthropic en *Building effective agents* (diciembre de 2024):

- En un **workflow**, el código fija el camino: primero esto, luego aquello. El LLM rellena huecos (extrae, clasifica,
  redacta), pero no decide el orden.
- En un **agente**, el LLM fija el camino. El código solo ejecuta lo que el modelo pide y le devuelve el resultado.

La diferencia no es de sofisticación, es de **quién controla el flujo**. Y ese control tiene precio: cada decisión que
le das al modelo es una decisión que puede salir mal, que hay que pagar en tokens y que hay que poder auditar después.

Este curso enseña a construir el código que rodea al modelo: el **controlador**. Es lo que decide qué se ejecuta de
verdad, cuánto se gasta, qué se guarda y cuándo se detiene todo. El modelo propone; el controlador dispone.

---

<a name="2-escalera"></a>
## 2. La escalera de autonomía

Antes de escribir `while True:`, ubica tu problema en el peldaño más bajo que lo resuelva:

| Nivel | Arquitectura | Quién gobierna el flujo | Llamadas al LLM | Ejemplo en nuestro ATS |
|---|---|---|---|---|
| **1. Extracción estructurada** | `prompt → JSON validado` | Código, 1 paso | 1 | Extraer años, inglés y tecnologías del texto de un CV |
| **2. Workflow fijo** | Cadena, ruteo o paralelo en Python | Código, N pasos conocidos | 1–3 | Leer la vacante → filtrar con reglas → redactar el resumen |
| **3. Agente de lectura acotado** | Bucle con herramientas de solo lectura y presupuesto | El modelo propone, el código limita | 4–12, variable | Explorar el ATS cuando no sabes qué filtros darán resultados |
| **4. Agente con estado y efectos** | Máquina de estados, checkpoints y aprobación humana | Híbrido | Variable, con pausas | Preseleccionar, verificar normas y agendar entrevistas reales |

Subir de peldaño se justifica solo cuando el de abajo **no puede** resolver el problema, no cuando el de arriba
parece más moderno. Las señales de que necesitas un agente:

- **No sabes de antemano cuántos pasos harán falta.** Si la búsqueda devuelve 0 candidatos hay que relajar filtros;
  si devuelve 40, hay que afinarlos. Un DAG fijo no reacciona a eso.
- **El siguiente paso depende del contenido de la observación**, no solo de su forma.
- **El espacio de herramientas es grande** y la combinación correcta cambia de una tarea a otra.

Las señales de que **no** lo necesitas:

- Los datos ya están estructurados y las reglas se pueden escribir en código (este es nuestro caso, y lo vamos a medir).
- El orden de los pasos es siempre el mismo.
- Un error en un paso intermedio es caro o irreversible y no tienes cómo detectarlo.

---

<a name="3-error"></a>
## 3. El error compuesto: por qué cada paso cuesta

Si el modelo elige bien en cada paso con probabilidad $p$ y los pasos son independientes, la probabilidad de que una
trayectoria de $n$ pasos salga entera bien es $p^n$:

| Acierto por paso | 3 pasos | 7 pasos | 11 pasos | 20 pasos |
|---|---|---|---|---|
| 0.99 | 0.97 | 0.93 | 0.90 | 0.82 |
| 0.95 | 0.86 | 0.70 | 0.57 | 0.36 |
| 0.92 | 0.78 | 0.56 | **0.40** | 0.19 |
| 0.90 | 0.73 | 0.48 | 0.31 | 0.12 |

La preselección de `VAC-101` que vas a correr toma **11 pasos**. Un modelo que acierta el 92 % de las veces por paso
termina bien solo 4 de cada 10 veces si nada lo corrige. El supuesto de independencia es optimista en un sentido (los
errores reales se correlacionan: un malentendido temprano arrastra a los siguientes) y pesimista en otro (un buen
controlador detecta y corrige errores a mitad de camino). Los dos efectos son el tema de este curso:

- **Quitar pasos de decisión al modelo** (módulos 1 y 2): cada decisión que pasa a código deja de multiplicar.
- **Detectar y corregir** (módulos 1, 2 y 6): errores accionables, invariantes de estado y políticas que bloquean.
- **Medir** (módulo 7): no con una corrida que salió bien, sino con la probabilidad de que salgan bien *todas*.

Además del acierto, cada paso cuesta **latencia** (una llamada al modelo tarda entre 0,5 y varios segundos) y
**tokens**: en un bucle, el historial completo se reenvía en cada vuelta, así que el costo de entrada crece más rápido
que el número de pasos (lo medimos en el módulo 3).

---

<a name="4-entorno"></a>
## 4. El entorno del curso: el ATS y el modelo simulado

Todos los laboratorios comparten dos archivos de `comun/`.

**`comun/ag_comun.py`** es el ATS (*Applicant Tracking System*) sobre el que opera el agente: 2 vacantes, 8
candidatos, las herramientas y las reglas de negocio.

| Vacante | Qué pide | Pasan la búsqueda (habilidades y sueldo) | Bloqueados al verificar | Terna correcta |
|---|---|---|---|---|
| `VAC-101` | Senior AI Engineer, híbrido en Bogotá, 6.500 USD, inglés B2, 4 años | `CAND-01`, `CAND-03`, `CAND-04`, `CAND-07` | `CAND-04` (1 año, inglés A2), `CAND-07` (inglés B1, vive en Medellín) | `CAND-01`, `CAND-03` |
| `VAC-102` | Platform / MLOps, remoto, 7.000 USD, inglés B2, 5 años | `CAND-05`, `CAND-08` | `CAND-08` (contactado hace 45 días: enfriamiento de 90) | `CAND-05` |

Dos funciones son la **verdad** contra la que se mide todo el curso:

- `motivos_bloqueo(vacante, candidato)` aplica las reglas en código: requisitos, años, inglés, presupuesto,
  enfriamiento y modalidad. Lista vacía = elegible.
- `terna_correcta(vacante_id)` devuelve los elegibles según esas reglas.

Fíjate en `CAND-04`: declara todas las habilidades para salir en la búsqueda y su CV trae escondida una orden para el
agente. Lo usamos en el módulo 6.

**`comun/ag_modelo.py`** define una interfaz, `responder(mensajes, herramientas) -> Respuesta`, con dos
implementaciones:

- `ModeloOpenAI` llama a la API real con *tool calling* si defines `OPENAI_API_KEY` (el modelo se elige con `MODELO`,
  por defecto `gpt-4.1-mini`).
- `ModeloSimulado` es una política fija, sin red, que sigue el procedimiento de preselección. Sus defectos se encienden
  por parámetro: `errata=True` (escribe mal una habilidad), `terco=True` (repite la misma llamada), `p_descuido=0.25`
  (da por bueno a un candidato sin verificarlo), `obedece_inyeccion=True` (hace lo que le ordena un dato).

El modelo simulado **no mide la calidad de un LLM**: mide tu controlador. Si tu código corta el bucle, corrige la
errata y bloquea la inyección con el simulado, lo hará también con un modelo real cuando cometa esos errores. Los
números sobre cuántas veces los comete un modelo concreto solo salen de correr los mismos scripts con tu API key. Para
forzar el simulado aunque tengas clave: `AGENTE_SIMULADO=1`.

Los costos que imprimen los laboratorios usan 0,40 USD por millón de tokens de entrada y 1,60 de salida (precio de un
modelo pequeño). Ajusta `PRECIO_ENTRADA_USD_1M` y `PRECIO_SALIDA_USD_1M` al modelo que uses. Los tokens del simulado
se estiman con 4 caracteres por token; con un modelo real vienen del proveedor.

---

<a name="5-lab1"></a>
## 5. Laboratorio 1: workflow contra agente

[`code/01_workflow_vs_agente.py`](code/01_workflow_vs_agente.py) resuelve la misma preselección por los dos caminos.

`workflow_fijo` aplica `motivos_bloqueo` a los 8 candidatos en Python. `bucle_agente` le da al modelo solo el
identificador de la vacante y 5 herramientas, y lo deja explorar: `obtener_vacante` → `buscar_candidatos` → ficha y
verificación de cada uno de los 4 encontrados → `entregar_terna`.

Resultado de nuestra corrida (modelo simulado):

| | `workflow_fijo` (`VAC-101`) | Agente (`VAC-101`) | Agente (`VAC-102`) |
|---|---|---|---|
| Llamadas al modelo | 0 | 11 | 7 |
| Tokens de entrada | 0 | 16.446 | 7.862 |
| Tokens de salida | 0 | 224 | 153 |
| Costo | 0 USD | 0,0069 USD | 0,0034 USD |
| Latencia | 0,03 ms | 11 llamadas (con un modelo real, 5–20 s) | 7 llamadas |
| Terna | `CAND-01`, `CAND-03` | `CAND-01`, `CAND-03` | `CAND-05` |

Los dos aciertan. Uno cuesta cero y tarda microsegundos; el otro cuesta poco, pero tarda segundos y puede fallar de 11
formas distintas. Cuando los datos ya están estructurados y las reglas se pueden escribir, **el workflow gana siempre**.

Observa también la asimetría de tokens: 16.446 de entrada contra 224 de salida. El modelo escribe poco (una llamada a
herramienta son unas decenas de tokens) pero lee todo el historial en cada vuelta. En un agente, **el costo está en la
entrada**, y crece con cada observación que se acumula.

¿Entonces para qué sirve el agente aquí? Para cuando el mundo no sea tan ordenado: CVs en texto libre que hay que
interpretar, búsquedas que devuelven 0 y obligan a relajar requisitos, fuentes que se consultan solo si hace falta. En
ese caso la pregunta deja de ser "¿agente o workflow?" y pasa a ser "¿cuánto del flujo puedo seguir controlando en
código?". El resto del curso responde esa pregunta.

---

<a name="6-bucle"></a>
## 6. Anatomía del bucle

El bucle de `bucle_agente` es el mismo que encontrarás dentro de cualquier framework. Escrito a mano, tiene cinco
partes:

```python
while True:
    presupuesto.abrir_paso()                          # 1. freno: ¿queda presupuesto para otra llamada?
    resp = modelo.responder(mensajes, esquemas)       # 2. el modelo propone (texto o llamadas a herramientas)
    presupuesto.registrar(resp.tokens_entrada, resp.tokens_salida)
    if not resp.llamadas:                             # 3. sin llamadas = el modelo cree que terminó
        break
    mensajes.append({"role": "assistant", "tool_calls": [...]})
    for tc in resp.llamadas:                          # 4. el controlador ejecuta (o no) cada llamada
        resultado = ejecutar_herramienta_ats(tc.nombre, tc.argumentos)
        mensajes.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(resultado)})
        if tc.nombre == "entregar_terna":             # 5. condición de fin explícita
            ...
```

Tres decisiones de diseño que vas a repetir en todo el curso:

1. **El fin lo marca una herramienta** (`entregar_terna`), no un texto del modelo. Así el resultado final tiene
   esquema, se puede validar y queda en la trayectoria como cualquier otro paso.
2. **El resultado de cada herramienta vuelve como mensaje `tool`** con el `tool_call_id` de la llamada. Es el formato
   que exigen las APIs con *tool calling*: si falta la respuesta a una llamada, la siguiente petición falla.
3. **Entre lo que el modelo pide y lo que se ejecuta está tu código** (paso 4). Hoy solo ejecuta; en los próximos
   módulos ese punto valida argumentos, bloquea transiciones ilegales, pide aprobación humana y cachea efectos.

---

<a name="7-lab2"></a>
## 7. Laboratorio 2: el presupuesto fuera del modelo

Pedirle al modelo en el prompt "no uses más de 8 pasos" es una sugerencia. El modelo no lleva la cuenta de forma
fiable, no sabe cuánto cuesta cada token y, cuando se atasca, es justo cuando menos caso hace a las instrucciones. Un
límite de gasto tiene que ser una **invariante del programa**.

`PresupuestoAgente` (en `comun/ag_comun.py`) lleva tres contadores y lanza `PresupuestoAgotado` al pasarse:

- `abrir_paso()` se llama **antes** de cada llamada al modelo: el paso que no cabe no se paga.
- `registrar(entrada, salida)` suma los tokens reales de la respuesta y comprueba el tope de tokens y de dólares.

[`code/02_presupuesto_y_frenos.py`](code/02_presupuesto_y_frenos.py) lo prueba en tres escenarios:

| Escenario | Límites | Qué pasa | Pasos | Tokens de entrada | Costo |
|---|---|---|---|---|---|
| Ejecución sana | 16 pasos, 30.000 tokens, 0,05 USD | Completa, terna correcta | 11 | 15.915 | 0,0067 USD |
| Modelo terco (repite la misma búsqueda) | 5 pasos | Cortado por `max_pasos=5` | 5 | 3.860 | 0,0017 USD |
| Tope de tokens estricto | 1.500 tokens | Cortado por `max_tokens=1500` | 3 | 2.383 | 0,0010 USD |

El segundo caso es el importante. Un agente atascado no falla con una excepción: sigue llamando, contento, hasta que
alguien lo para. Sin el freno, esa ejecución habría seguido hasta el límite del proveedor o hasta el *timeout* del
servidor, cobrando cada vuelta. Con el freno, la pérdida queda acotada a 5 llamadas.

El tercer caso muestra la otra cara: un tope demasiado bajo corta ejecuciones sanas. Los límites se calibran con datos:
corre tu agente sobre un conjunto de tareas reales, mira la distribución de pasos y tokens, y pon el límite por encima
del percentil 99 de las ejecuciones buenas. Lo que quede por encima es, casi siempre, un bucle.

Dos detalles de implementación:

- El tope de dinero se calcula con precios por token, que **cambian por modelo y en el tiempo**. Léelos de
  configuración, no los escribas en el código.
- Cuando el freno salta, **la ejecución no se pierde**: el historial sigue en memoria. En el módulo 2 lo guardamos como
  checkpoint para poder reanudarlo o revisarlo.

---

<a name="8-decision"></a>
## 8. Qué hacer con esto en tu proyecto

Una lista corta para decidir, antes de escribir el bucle:

1. **¿Puedo escribir el flujo como una secuencia fija?** Si sí, escribe el workflow y usa el LLM solo donde hay texto
   libre que interpretar.
2. **Si necesito un agente, ¿qué decisiones puedo sacarle?** Cada regla que pasa a código (filtros, validaciones,
   orden obligatorio) deja de multiplicar el error.
3. **¿Cuánto puede gastar una ejecución, como máximo?** Pon el presupuesto antes del primer despliegue, no después de
   la primera factura.
4. **¿Qué herramientas tienen efectos?** Sepáralas desde ya: en el módulo 6 les ponemos aprobación humana.
5. **¿Cómo voy a saber si funciona?** Necesitas una verdad (aquí, `terna_correcta`) y varias corridas por tarea. Lo
   formalizamos en el módulo 7.

En el siguiente módulo atacamos la fuente de error más barata de eliminar: herramientas mal diseñadas.
