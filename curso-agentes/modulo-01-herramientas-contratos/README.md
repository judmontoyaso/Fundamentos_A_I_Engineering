# Módulo 1 · Diseño de herramientas y contratos poka-yoke

> **Objetivo:** diseñar herramientas que un modelo use bien a la primera y, cuando se equivoque, sepa corregirse
> solo.
>
> **Lo que te llevas:** las cinco reglas de una herramienta para agentes, un contrato con JSON Schema estricto, y la
> medida de cuánto vale un mensaje de error bien escrito: en el laboratorio, la diferencia entre entregar la terna
> correcta y no entregar nada.

Índice:

1. [La herramienta es la interfaz de usuario del modelo](#1-interfaz)
2. [Cinco reglas](#2-reglas)
3. [El contrato: JSON Schema que el modelo lee y tu código hace cumplir](#3-contrato)
4. [Laboratorio 1: herramienta frágil contra contrato poka-yoke](#4-lab1)
5. [Errores accionables](#5-errores)
6. [Laboratorio 2: el mismo error, opaco y accionable](#6-lab2)
7. [Cuántas herramientas, y cómo nombrarlas](#7-cuantas)
8. [Lista de revisión](#8-lista)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 1 · Comparación entre una API CRUD cruda y una herramienta poka-yoke diseñada para LLMs](/infografias/agentes-m1-herramientas-poka-yoke.png)

---

<a name="1-interfaz"></a>
## 1. La herramienta es la interfaz de usuario del modelo

Muchos agentes que fallan en producción no fallan porque el modelo razone mal, sino porque **sus herramientas son un
espejo de la API interna**: endpoints CRUD, códigos numéricos, campos que solo entiende quien leyó la documentación.

Una API pensada para personas asume que quien la llama leyó el manual una vez y lo recuerda. Un modelo decide en cada
turno a partir de tres cosas: **el nombre de la herramienta, la descripción de sus parámetros y lo que devolvieron las
llamadas anteriores**. No tiene más información que esa. Si un parámetro se llama `t` y acepta `1`, `2` o `3`, el modelo va a
adivinar.

*Poka-yoke* es un término de manufactura japonesa: diseñar la pieza para que sea imposible montarla mal (un enchufe que
solo entra en una posición). Aplicado a herramientas: que los argumentos incorrectos no se puedan expresar, y que los
que se cuelen se rechacen con un mensaje que diga cómo arreglarlos.

---

<a name="2-reglas"></a>
## 2. Cinco reglas

**1. Una herramienta por operación de negocio, no por endpoint.** Si para saber si un candidato sirve hay que llamar a
`obtener_usuario(id)`, `obtener_historial(uid)` y `obtener_banda_salarial(uid)`, son tres pasos de decisión (y tres
oportunidades de error compuesto) donde bastaba uno. En nuestro ATS, `verificar_elegibilidad(vacante_id,
candidato_id)` aplica las seis reglas de negocio de una vez.

**2. Tipos cerrados y nombres que se explican solos.** `modalidad: "remoto" | "hibrido" | "presencial"` en vez de
`modo: int`. IDs como `enum` cuando el conjunto es pequeño (nuestras vacantes), y un catálogo cerrado cuando el
modelo tiene que elegir valores (las habilidades).

**3. Validar y normalizar en la frontera.** El schema dice qué se espera; tu código lo comprueba de verdad, porque el
modelo puede devolver argumentos que no cumplen el schema. Normaliza lo que sea inofensivo (mayúsculas, espacios) y
rechaza con explicación lo demás.

**4. Salidas recortadas y con contexto.** Nunca devuelvas 40 KB de JSON con 120 columnas internas: cada token de la
observación se vuelve a pagar en cada vuelta (módulo 3). Devuelve los campos que sirven para decidir, más
`total` y, si hay más resultados, cuántos quedaron fuera.

**5. Errores accionables.** Un `KeyError: 'VAC-99'` no le dice nada al modelo. `{"ok": false, "error": "Vacante
'VAC-99' no encontrada.", "vacantes_validas": ["VAC-101", "VAC-102"]}` le dice exactamente qué hacer en el siguiente
turno.

---

<a name="3-contrato"></a>
## 3. El contrato: JSON Schema que el modelo lee y tu código hace cumplir

Cada herramienta del ATS tiene un esquema en `ESQUEMAS_HERRAMIENTAS` (`comun/ag_comun.py`). Este es el de la búsqueda:

```json
{
  "name": "buscar_candidatos",
  "description": "Busca candidatos en el ATS que declaren todas las habilidades indicadas y cuya aspiración no supere max_aspiracion_usd.",
  "parameters": {
    "type": "object",
    "properties": {
      "habilidades": {"type": "array", "items": {"type": "string"}, "minItems": 1},
      "max_aspiracion_usd": {"type": "integer", "minimum": 1000, "maximum": 20000}
    },
    "required": ["habilidades", "max_aspiracion_usd"],
    "additionalProperties": false
  }
}
```

Tres cosas a notar:

- **La descripción es documentación para el modelo**, no para ti. Dice qué hace la búsqueda (todas las habilidades,
  tope de sueldo) en una frase que el modelo puede usar para decidir si es la herramienta correcta.
- **Los rangos (`minimum`, `maximum`) y `additionalProperties: false`** le dicen al modelo qué no hacer y le dan a tu
  validador una regla que comprobar.
- **El schema no se cumple solo.** Algunos proveedores ofrecen un modo estricto que garantiza que los argumentos
  cumplen el schema (en OpenAI, `strict: true`; exige que todas las propiedades estén en `required` y
  `additionalProperties: false`). Aun así, valida en tu código: el schema no sabe que "Postgress" no está en tu
  catálogo, ni que el candidato está en enfriamiento.

Las habilidades no van como `enum` en el schema a propósito: en un ATS real el catálogo tiene cientos de valores y
cambia. Se validan en la ejecución, y ahí es donde entra la regla 5.

---

<a name="4-lab1"></a>
## 4. Laboratorio 1: herramienta frágil contra contrato poka-yoke

[`code/01_herramienta_fragil_vs_poka_yoke.py`](code/01_herramienta_fragil_vs_poka_yoke.py) compara dos diseños.

La **herramienta frágil** recibe una consulta en texto libre. Ante `SELECT * FROM candidatos; DROP TABLE` devuelve:

```json
{"error": "SQLSyntaxError near ';' at line 1 (tabla interna expuesta: ats_prod_candidates_v2)"}
```

Tres problemas en una línea: el modelo puede escribir cualquier cosa (incluido SQL destructivo si alguien se lo pide
en un dato, módulo 6), el error filtra el nombre de una tabla interna, y no dice qué hacer. Si la consulta funciona,
devuelve un volcado sin límite.

El **contrato poka-yoke** se prueba con cuatro casos. Lo que devuelve cada uno:

| Caso | Entrada | Respuesta |
|---|---|---|
| Búsqueda válida | `["Python", "RAG"]`, tope 6.500 | `ok: true`, `total: 4`, solo id, nombre, ciudad, aspiración y habilidades |
| Vacante inexistente | `VAC-999` | `ok: false`, `"Vacante 'VAC-999' no encontrada."`, `vacantes_validas: ["VAC-101", "VAC-102"]` |
| Habilidad con errata | `"Evaluacion de LLM"` | `ok: false`, `sugerencias: {"Evaluacion de LLM": ["Evaluación de LLMs"]}`, catálogo completo |
| Presupuesto inválido | `-50` | `ok: false`, `"El parámetro 'max_aspiracion_usd' debe ser un entero >= 1000."` |

Cada respuesta de error trae **el dato que falta para la siguiente llamada**: la lista de vacantes válidas, la
habilidad más parecida del catálogo, la regla que se incumplió. Las sugerencias salen de `difflib.get_close_matches`
sobre el catálogo: barato, determinista y suficiente para erratas. Para sinónimos ("LLM evals" ↔ "Evaluación de
LLMs") haría falta una tabla de alias o una búsqueda por embeddings.

---

<a name="5-errores"></a>
## 5. Errores accionables

Un error para un agente tiene que responder tres preguntas:

1. **¿Qué pasó?** En lenguaje del dominio, no del motor: "habilidad no reconocida", no "KeyError".
2. **¿Por qué?** La regla concreta: "debe ser un entero ≥ 1000", "último contacto hace 20 días (mínimo 90)".
3. **¿Qué hago ahora?** Valores válidos, la sugerencia más cercana, o la herramienta que hay que llamar antes.

Y tiene que **no revelar** lo que no debe: nombres de tablas, rutas, trazas, existencia de registros a los que el
usuario no tiene acceso. La respuesta de error es un dato más que el modelo lee y que puede acabar en la respuesta al
usuario.

Distingue también dos clases de fallo:

- **Errores de negocio y de argumentos** (vacante inexistente, habilidad desconocida): se devuelven al modelo como
  observación con `ok: false`. Son información para el siguiente paso.
- **Errores de infraestructura** (la base de datos no responde): reintenta en el controlador con espera exponencial,
  sin gastar un turno del modelo. Si tras los reintentos sigue fallando, entonces sí devuelve un error claro ("el ATS
  no responde; reintenta más tarde") o corta la ejecución.

---

<a name="6-lab2"></a>
## 6. Laboratorio 2: el mismo error, opaco y accionable

[`code/02_errores_accionables.py`](code/02_errores_accionables.py) corre el agente con un modelo que escribe mal una
habilidad en su primera búsqueda (`errata=True`: "Evaluacion de LLM" en lugar de "Evaluación de LLMs"). Lo único que
cambia entre las dos corridas es el parámetro `sugerir_en_error` de la herramienta.

| | Error opaco | Error accionable |
|---|---|---|
| Respuesta a la búsqueda con errata | `"Sin resultados para los filtros enviados."` | `"Habilidades no reconocidas..."` + `sugerencias` |
| Búsquedas realizadas | 1 | 2 (la segunda, corregida) |
| Candidatos encontrados | 0 | 4 |
| Pasos totales | 3 | 12 |
| Terna entregada | **ninguna** | `CAND-01`, `CAND-03` |

Con el error opaco, el agente concluye que no hay candidatos y cierra con una terna vacía. Es el peor tipo de fallo:
**no parece un fallo**. No hay excepción ni alerta; hay un informe que dice "no hay nadie", y la reclutadora lo cree.

Con el error accionable, el agente aplica la sugerencia en el siguiente turno y termina bien con un solo paso extra
(12 contra los 11 de una corrida sin errata).

El modelo simulado aplica la sugerencia de forma mecánica. Un modelo real suele hacerlo también, siempre que la
sugerencia sea explícita y esté en el mismo mensaje del error. Repite el laboratorio con tu API key para comprobarlo
con tu modelo.

---

<a name="7-cuantas"></a>
## 7. Cuántas herramientas, y cómo nombrarlas

Cada esquema de herramienta viaja en **todas** las llamadas al modelo. Con 5 herramientas, unos cientos de tokens; con
40, varios miles por paso, y la elección empeora: el modelo confunde herramientas parecidas y elige la equivocada.

Pautas:

- **Expón solo las herramientas de la etapa actual.** En el módulo 4 lo hacemos con una lista blanca por etapa.
- **Nombres con verbo y objeto de negocio:** `verificar_elegibilidad`, `consultar_ficha_candidato`. Evita genéricos
  como `get`, `query`, `run`.
- **Prefijos por sistema cuando hay varios:** `ats_buscar_candidatos`, `calendario_crear_evento`. MCP los usa para
  evitar choques de nombre entre servidores.
- **Una herramienta de cierre** (`entregar_terna`) con esquema propio, para que el resultado final sea validable.
- **Si dos herramientas siempre se llaman juntas, fusiónalas.** Si una tiene diez parámetros opcionales que se combinan
  de formas raras, divídela.

---

<a name="8-lista"></a>
## 8. Lista de revisión

Antes de darle una herramienta a un agente:

- [ ] El nombre y la descripción bastan para saber cuándo usarla, sin leer el código.
- [ ] Los parámetros tienen tipos cerrados, rangos y `additionalProperties: false`.
- [ ] Tu código valida los argumentos aunque el proveedor diga que cumplen el schema.
- [ ] La salida trae solo lo necesario para decidir, más el total y lo que quedó fuera.
- [ ] Cada error dice qué pasó, por qué y qué hacer, sin filtrar internos.
- [ ] Los errores de infraestructura se reintentan en el controlador, no en el modelo.
- [ ] Sabes si tiene efectos (escritura, envío, cobro). Si los tiene, ve al módulo 6 antes de exponerla.

En el siguiente módulo, el controlador deja de confiar en que el modelo siga el procedimiento: lo hace cumplir.
