# Módulo 3 · Presupuesto de contexto, poda y memoria

> **Objetivo:** controlar cuánto lee el modelo en cada paso, y recordar entre ejecuciones lo que un humano corrigió.
>
> **Lo que te llevas:** la cuenta de por qué el costo de un agente crece más rápido que sus pasos, una poda de
> observaciones viejas que ahorra el 29 % de los tokens de entrada sin cambiar el resultado, y una memoria episódica
> que hace que una corrección de la reclutadora se aplique sola en la siguiente ejecución.

Índice:

1. [Por qué el contexto crece más rápido que los pasos](#1-crece)
2. [Dos problemas: costo y atención](#2-problemas)
3. [Tres técnicas de higiene de contexto](#3-tecnicas)
4. [Laboratorio 1: poda de observaciones](#4-lab1)
5. [Memoria: qué recordar entre ejecuciones](#5-memoria)
6. [Laboratorio 2: una corrección que se recuerda](#6-lab2)
7. [Riesgos de la memoria](#7-riesgos)
8. [Lista de revisión](#8-lista)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 3 · Presupuesto de contexto, poda de observaciones y memoria episódica](/infografias/agentes-m3-poda-contexto-memoria.png)

---

<a name="1-crece"></a>
## 1. Por qué el contexto crece más rápido que los pasos

Las APIs de chat no tienen memoria: en cada llamada se envía el historial completo. En un agente, el historial crece
con cada observación. Si la observación del paso $i$ ocupa $T_i$ tokens, la llamada del paso $n$ lleva
$T_1 + T_2 + \dots + T_{n-1}$ tokens de observaciones, y el total facturado en $n$ pasos es:

$$\sum_{k=1}^{n} \sum_{i<k} T_i \;\approx\; T \cdot \frac{n^2}{2} \quad \text{si todas las observaciones miden } T$$

**Cuadrático en el número de pasos.** Duplicar los pasos cuadruplica, aproximadamente, los tokens de entrada. Por eso
en el módulo 0 la entrada era 70 veces la salida (16.446 frente a 224).

El *prompt caching* de los proveedores abarata el prefijo repetido (el system prompt, los esquemas de herramientas y
los mensajes viejos que no cambian), con descuentos grandes sobre los tokens cacheados. Ayuda mucho, pero no elimina el
problema: el contexto sigue creciendo, y con él la latencia y el riesgo de que el modelo se pierda.

---

<a name="2-problemas"></a>
## 2. Dos problemas: costo y atención

**Costo.** Cada observación vieja se vuelve a pagar en todos los pasos que siguen.

**Atención.** Más contexto no es mejor contexto. Los modelos usan peor la información que está en medio de un contexto
largo que la que está al principio o al final (*Lost in the Middle*, Liu et al., 2023), y en un agente el contexto
largo está lleno de observaciones parecidas: fichas de cuatro candidatos con los mismos campos. El riesgo concreto es
mezclar atributos: atribuirle al candidato del paso 9 el inglés del candidato descartado en el paso 4.

La conclusión práctica: el contexto es un **presupuesto**, como los pasos y los dólares, y se gestiona en el
controlador.

---

<a name="3-tecnicas"></a>
## 3. Tres técnicas de higiene de contexto

**1. Poda de observaciones (*observation masking*).** Deja íntegras las últimas $K$ observaciones y reemplaza el cuerpo
de las anteriores por una versión mínima (el id y el dato que importa) o por un marcador. El razonamiento del modelo y
las llamadas se conservan; lo que se recorta es el volumen de las respuestas viejas. En agentes de programación, esta
técnica simple ha dado resultados comparables a resumir el historial con un LLM, a una fracción del costo (Lindenbauer
et al., 2025).

**2. Estado estructurado en lugar de prosa.** Lo que se sabe con certeza vive en el estado del controlador (módulo 2):
`verificados = {"CAND-01": True, ...}`. Si hay que recordárselo al modelo, se le inyecta esa tabla compacta, no las
fichas completas. Un resumen en prosa libre pierde justo lo que importa: identificadores exactos y cifras.

**3. Compactación por resumen.** Cuando el historial supera un umbral, un LLM resume la parte vieja. Es la técnica más
flexible y la más arriesgada: cuesta una llamada extra, puede perder detalles y puede alucinar. Úsala para tareas largas
y abiertas, y siempre con el estado estructurado como respaldo.

Antes de cualquiera de las tres, aplica la regla 4 del módulo 1: **que la herramienta no devuelva basura**. La poda más
barata es la que no hace falta.

---

<a name="4-lab1"></a>
## 4. Laboratorio 1: poda de observaciones

[`code/01_podar_observaciones.py`](code/01_podar_observaciones.py) simula una API verbosa: cada ficha de candidato
llega con 45 líneas de auditoría que no sirven para decidir (como pasa con muchos sistemas empresariales). Corre la
preselección dos veces:

- **Sin poda**, el modelo recibe todo el historial.
- **Con poda**, `podar_observaciones_antiguas(mensajes, conservar_ultimas=2)` deja intactas las dos últimas
  observaciones y reduce las anteriores: de una ficha queda `{"id", "nombre", "resumen_podado": true}`; del resto, se
  quita la auditoría.

| | Sin poda | Con poda |
|---|---|---|
| Pasos | 11 | 11 |
| Tokens de entrada | 27.229 | 19.315 |
| Costo | 0,0113 USD | 0,0081 USD |
| Terna | `CAND-01`, `CAND-03` | `CAND-01`, `CAND-03` |
| Ahorro de entrada | | **29,1 %** |

Mismo resultado, 29 % menos de tokens de entrada. Dos detalles del código que importan:

- **La poda se aplica a la vista que recibe el modelo**, no al historial guardado. El checkpoint (módulo 2) conserva
  todo; solo cambia lo que se envía. Así puedes auditar después y cambiar la política de poda sin perder datos.
- **Se poda después de decidir, no antes.** El modelo ve la ficha completa en el paso en que la necesita (verificar a
  ese candidato). Lo que se recorta es lo que ya no va a usar.

Cuándo no podar: si el modelo necesita comparar observaciones viejas entre sí (por ejemplo, ordenar candidatos por un
campo que solo está en las fichas), la poda le quita justo eso. Para ese caso, guarda el campo en el estado
estructurado antes de podar.

---

<a name="5-memoria"></a>
## 5. Memoria: qué recordar entre ejecuciones

La poda gestiona la memoria **dentro** de una ejecución. Entre ejecuciones, el modelo no recuerda nada: cada vez
empieza desde el system prompt. Hay tres tipos de memoria que vale la pena distinguir:

| Tipo | Qué guarda | Ejemplo en el ATS | Dónde vive |
|---|---|---|---|
| De trabajo | El estado de la ejecución actual | Candidatos verificados hasta ahora | Estado del controlador, checkpoint |
| Episódica | Lo que se aprendió en ejecuciones pasadas | "Para VAC-101 el equipo exige FastAPI" | Tabla indexada por entidad (vacante, cliente) |
| Semántica | Conocimiento general del dominio | Políticas de la empresa, catálogo de habilidades | Documentos, RAG, herramientas |

La memoria episódica es la que convierte una corrección humana en comportamiento: la reclutadora corrige una vez, y el
agente lo aplica la próxima vez sin que nadie toque el código ni el prompt base.

Lo que **sí** conviene recordar: reglas verificadas por una persona, con su origen y fecha, indexadas por la entidad a
la que aplican. Lo que **no**: conclusiones del propio modelo sin revisar, datos personales que no hacen falta, y
cualquier cosa extraída de un documento externo (sección 7).

---

<a name="6-lab2"></a>
## 6. Laboratorio 2: una corrección que se recuerda

[`code/02_memoria_episodica.py`](code/02_memoria_episodica.py) guarda la memoria en `salida/m3_memoria_episodica.json`,
una lista de reglas con `vacante_id`, `regla` y `origen`.

1. **Sesión 1**, sin memoria: el agente busca con los 4 requisitos de la vacante y entrega `CAND-01` y `CAND-03`.
2. El líder técnico revisa y corrige: para `VAC-101` el equipo exige además FastAPI. Se registra
   `REQUISITO_EXTRA: FastAPI` con origen `revisión_humana_sesion_1`.
3. **Sesión 2**: al empezar, el controlador recupera las reglas de esa vacante y las añade al system prompt. El agente
   busca con 5 habilidades y entrega solo a `CAND-01` (el único con FastAPI).

| | Sesión 1 | Sesión 2 |
|---|---|---|
| Recuerdos inyectados | 0 | 1 |
| Habilidades buscadas | Python, SQL, RAG, Evaluación de LLMs | las mismas + FastAPI |
| Terna | `CAND-01`, `CAND-03` | `CAND-01` |

La recuperación es por clave exacta (`vacante_id`), no por similitud. Para una memoria pequeña y bien indexada es lo
correcto: barato, predecible y fácil de auditar. Cuando las memorias son muchas y no tienen una clave natural, se
recuperan por embeddings, con el costo de que a veces llega una memoria que no aplica.

---

<a name="7-riesgos"></a>
## 7. Riesgos de la memoria

La memoria persistente es una superficie de ataque y de error:

- **Envenenamiento.** Si el agente puede escribir en su memoria a partir de lo que lee, un CV malicioso puede dejar una
  "regla" que afecte a todas las ejecuciones futuras. Escribe en la memoria solo desde acciones humanas o desde código
  que valida, nunca desde texto libre de un documento.
- **Reglas obsoletas.** La vacante cambia y la regla sigue ahí. Guarda fecha y origen, y dales caducidad o revisión.
- **Contradicciones.** Dos reglas incompatibles para la misma vacante. Resuélvelas al escribir (la nueva reemplaza a la
  vieja) y no al leer.
- **Datos personales.** Una memoria que guarda opiniones sobre candidatos es una base de datos personales, con las
  mismas obligaciones legales (en Colombia, la Ley 1581 de 2012).

---

<a name="8-lista"></a>
## 8. Lista de revisión

- [ ] Sabes cuántos tokens de entrada usa una ejecución típica y cómo crecen con los pasos.
- [ ] Las herramientas devuelven solo lo necesario (la poda más barata).
- [ ] Las observaciones viejas se podan en la vista del modelo, y el historial completo se conserva aparte.
- [ ] Los hechos ciertos viven en el estado estructurado, no solo en el historial.
- [ ] La memoria entre ejecuciones guarda reglas con origen, fecha y entidad, escritas por humanos o por código.
- [ ] Nada que venga de un documento externo se escribe directamente en la memoria.

En el siguiente módulo sacamos las herramientas del proceso del agente con el Model Context Protocol.
