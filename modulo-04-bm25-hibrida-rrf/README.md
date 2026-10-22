# Módulo 4 · BM25, búsqueda híbrida y Reciprocal Rank Fusion

> **Objetivo:** entender la búsqueda **léxica** (BM25) por dentro, saber cuándo le gana a la semántica, y combinar
> las dos en una **búsqueda híbrida** con **Reciprocal Rank Fusion (RRF)**, implementada de punta a punta en Qdrant
> y **medida** contra cada búsqueda por separado.
>
> **Pieza del proyecto:** el buscador de CVs pasa a ser híbrido. Encuentra a quien escribió "AWS" cuando la consulta
> dice "AWS" (léxica) y también a quien escribió "Kafka y Flink" cuando la consulta dice "streaming" (semántica).

Índice:

1. [Dónde falla la búsqueda semántica](#1-falla-semantica)
2. [Búsqueda léxica: el índice invertido](#2-lexica)
3. [BM25 por dentro](#3-bm25)
4. [Tokenizar en español: la mitad del trabajo](#4-tokenizar)
5. [Cuándo gana cada una](#5-cuando)
6. [Búsqueda híbrida: el problema de combinar puntajes](#6-hibrida)
7. [Reciprocal Rank Fusion](#7-rrf)
8. [Variantes: RRF ponderado y DBSF](#8-variantes)
9. [BM25 como vector disperso](#9-dispersos)
10. [Híbrida de punta a punta en Qdrant](#10-qdrant)
11. [Después de fusionar: re-ranking](#11-rerank)
12. [Medir: léxica vs. semántica vs. híbrida](#12-medir)
13. [Proyecto del módulo](#13-proyecto)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-falla-semantica"></a>
## 1. Dónde falla la búsqueda semántica

En el Módulo 2 la búsqueda semántica brilló: encontró a la candidata de "Kafka y Flink" con una consulta sobre
"streaming" sin una sola palabra en común. Pero en el laboratorio también viste su punto débil: con un modelo pequeño,
una PM que tenía "datos" en sus áreas **empató** con la experta en streaming. Los embeddings comprimen el significado
en unos cientos de números, y en esa compresión se pierde lo **exacto**:

- **Siglas y códigos:** "ISO 27001", "AWS", "SAP FI/CO", "NIT 900.123.456". Un embedding no sabe que "ISO 27001" no es
  "ISO 9001": los dos "suenan" a normas ISO.
- **Nombres propios y productos raros:** "Qdrant", "dbt", "Airbyte". Si el modelo casi no los vio al entrenar, su
  vector es ruido.
- **Versiones y números:** "Python 2" vs "Python 3.12", "5 años" vs "15 años".
- **Coincidencia literal que el usuario espera:** quien busca "LangGraph" quiere ver CVs que dicen "LangGraph",
  no CVs "parecidos a orquestación de agentes".

Para todo eso existe una técnica de los años 90 que sigue invicta en su terreno: la búsqueda **léxica** con **BM25**.

---

<a name="2-lexica"></a>
## 2. Búsqueda léxica: el índice invertido

La búsqueda léxica compara **términos**, no significados. Su estructura central es el **índice invertido**, el mismo
de un buscador web o del índice al final de un libro: para cada término, la lista de documentos que lo contienen.

```
"kafka"  -> [cv_1, cv_7]
"aws"    -> [cv_1, cv_3, cv_9]
"sap"    -> [cv_4]
```

Buscar "kafka aws" es leer dos listas y combinarlas: no hay que comparar la consulta contra cada documento, por eso
escala a miles de millones de documentos. La pregunta interesante no es *cuáles* documentos contienen los términos
(eso lo da el índice), sino **en qué orden** mostrarlos. Ahí entra BM25.

---

<a name="3-bm25"></a>
## 3. BM25 por dentro

BM25 (*Best Matching 25*) puntúa un documento `D` para una consulta `Q` sumando, por cada término `q` de la consulta,
cuánto aporta ese término:

```
                        f(q,D) · (k1 + 1)
BM25(D,Q) = Σ IDF(q) · ─────────────────────────────────────
           q∈Q          f(q,D) + k1 · (1 − b + b · |D| / avgdl)

IDF(q) = ln( (N − n(q) + 0.5) / (n(q) + 0.5) + 1 )
```

Donde `f(q,D)` es cuántas veces aparece el término en el documento, `|D|` la longitud del documento, `avgdl` la
longitud media, `N` el número de documentos y `n(q)` en cuántos aparece el término. Tres ideas, cada una con su
razón de ser:

**1. IDF: los términos raros pesan más.** "de" aparece en todos los CVs: no distingue a nadie, su IDF es casi 0.
"Flink" aparece en uno: si la consulta lo pide, ese CV es casi seguro relevante. El IDF es lo que hace que BM25
"entienda" qué palabra de tu consulta importa.

**2. Saturación (`k1`): repetir un término rinde cada vez menos.** Si el documento tiene la longitud media, el
factor de frecuencia vale `f·(k1+1)/(f+k1)`. Con el valor típico `k1 = 1.2`:

| apariciones `f` | 1 | 2 | 5 | 10 | ∞ |
|---|---|---|---|---|---|
| aporte | 1.00 | 1.38 | 1.77 | 1.96 | 2.20 |

Escribir "Python" diez veces en el CV no te da diez veces más puntaje: el aporte satura cerca de 2.2. Esto protege
contra documentos que repiten palabras para posicionarse (*keyword stuffing*).

**3. Normalización por longitud (`b`): un CV largo no gana solo por ser largo.** Un documento de 5 páginas contiene
más palabras y por azar más coincidencias. Con `b = 0.75` (típico), el denominador crece con `|D|/avgdl` y penaliza
a los documentos más largos que la media. Con `b = 0` no hay normalización; con `b = 1`, es completa.

> Implementar BM25 te lleva 30 líneas y es la mejor forma de entenderlo. Está hecho de cero, comentado, en
> [`code/01_bm25_desde_cero.py`](code/01_bm25_desde_cero.py). Fíjate en que **no hay ningún modelo**: BM25 no se
> entrena, no usa GPU y es totalmente explicable (sabes exactamente por qué un documento quedó primero).

---

<a name="4-tokenizar"></a>
## 4. Tokenizar en español: la mitad del trabajo

BM25 compara términos, así que **qué cuenta como término** decide todo. Un tokenizador ingenuo (`texto.split()`)
convierte "Python," "python" y "PYTHON" en tres términos distintos. Lo mínimo para español:

1. **Minúsculas.**
2. **Quitar tildes:** "programación" = "programacion" (los CVs mezclan ambas).
3. **Separar por caracteres no alfanuméricos**, pero cuidando los términos técnicos: "c++", "c#", ".net", "node.js"
   pierden su identidad si borras los símbolos. Por eso conviene una lista de excepciones.
4. **Quitar *stopwords*** ("de", "la", "en", "con"…): no aportan señal y alargan los índices.
5. **Opcional, *stemming*:** reducir "desarrollador", "desarrollo", "desarrollando" a una raíz común ("desarroll").
   Sube el recall y a veces mezcla palabras que no tienen nada que ver. Mídelo antes de dejarlo puesto.

La consulta y los documentos deben pasar **por el mismo tokenizador**. Es la trampa número uno de la búsqueda
léxica: indexar con un análisis y buscar con otro.

---

<a name="5-cuando"></a>
## 5. Cuándo gana cada una

| Situación | Gana | Por qué |
|---|---|---|
| Siglas, códigos, nombres de producto | **BM25** | Coincidencia exacta; el embedding los difumina |
| Sinónimos, paráfrasis, otro idioma | **Semántica** | BM25 no sabe que "streaming" ≈ "tiempo real" |
| Consultas de 1-2 palabras técnicas | **BM25** | Poco contexto para que el embedding acierte |
| Consultas largas en lenguaje natural | **Semántica** | Captura la intención, no las palabras |
| Términos que el modelo nunca vio | **BM25** | Un término desconocido para el modelo sigue siendo un término |
| Explicar por qué salió un resultado | **BM25** | Puedes señalar los términos que coincidieron |

No compiten: **fallan en lugares distintos**. Cuando dos métodos se equivocan en casos distintos, combinarlos suele
ser mejor que cualquiera de los dos. Esa es toda la tesis de la búsqueda híbrida.

---

<a name="6-hibrida"></a>
## 6. Búsqueda híbrida: el problema de combinar puntajes

La idea obvia es sumar los puntajes: `final = puntaje_bm25 + puntaje_coseno`. No funciona, porque **están en escalas
incomparables**:

- BM25 no tiene techo: 12.4 en una colección, 3.1 en otra, según el largo de la consulta y la rareza de los términos.
- El coseno vive en `[-1, 1]`, y en la práctica casi siempre entre 0.2 y 0.9.

Sumados, BM25 aplasta al coseno. El arreglo habitual es **normalizar** (por ejemplo min-max, llevar cada lista a
`[0, 1]`) y luego hacer una suma ponderada `α·léxica + (1−α)·semántica`. Funciona, pero es frágil:

- Min-max **exagera diferencias diminutas**. Si los cosenos son 0.82, 0.80 y 0.79, tras normalizar quedan 1.0, 0.33 y
  0.0: una diferencia de 0.03 se convirtió en una de 1.0.
- Un solo valor atípico deforma toda la escala.
- `α` hay que calibrarlo, y el valor bueno cambia con cada colección y cada tipo de consulta.

Hay una forma de combinar que **ignora los puntajes** y usa solo el orden. Es más simple, no hay que calibrar nada, y
en la práctica es muy difícil de superar.

---

<a name="7-rrf"></a>
## 7. Reciprocal Rank Fusion

**RRF** (Cormack, Clarke y Büttcher, 2009) puntúa cada documento según **en qué puesto** quedó en cada lista:

```
RRF(d) = Σ   1 / (k + rango_r(d))        con k = 60 en el artículo original
        r∈R
```

Un documento suma `1/(k + puesto)` por cada lista donde aparece. Ejemplo con dos buscadores y `k = 60`:

| Documento | Puesto BM25 | Puesto semántico | RRF |
|---|---|---|---|
| A | 1 | 2 | 1/61 + 1/62 = **0.03252** |
| C | 3 | 1 | 1/63 + 1/61 = **0.03227** |
| B | 2 | — | 1/62 = 0.01613 |
| D | — | 3 | 1/63 = 0.01587 |

Orden final: **A, C, B, D**. Los documentos que **ambos** buscadores ponen arriba ganan con claridad, y lo que
encuentra uno solo queda detrás pero no se pierde. Por qué funciona tan bien:

- **Inmune a la escala:** solo usa puestos. Da igual que BM25 dé 12.4 y el coseno 0.8.
- **Sin calibración:** `k = 60` funciona razonablemente en casi cualquier colección. Lo que hace `k` es suavizar: con
  `k` grande, ser primero o quinto importa poco; con `k` pequeño, el primer puesto pesa mucho más.
- **Premia el consenso:** aparecer en las dos listas suma dos veces.

Su límite: **no sabe desempatar desacuerdos simétricos.** Si BM25 dice [Andrés, Sofía] y la semántica [Sofía,
Andrés], los dos suman exactamente `1/61 + 1/62` y el orden final lo decide el desempate de la implementación, no la
relevancia. Pasa en el laboratorio con "ISO 27001". Para eso existen los pesos (§8) y el re-ranking (§11).

> En Qdrant: su RRF usa por defecto `k = 2` y **cuenta los puestos desde 0**, es decir `1/(k + rango₀)`. Puedes fijar
> `k = 60` (y pesos) con `RrfQuery(rrf=Rrf(k=60))`. El orden final cambia poco entre una convención y otra; lo que
> cambia es la escala del puntaje, así que **no compares puntajes RRF de configuraciones distintas.**

Implementación de cero y comparación con la suma normalizada en [`code/03_rrf.py`](code/03_rrf.py).

---

<a name="8-variantes"></a>
## 8. Variantes: RRF ponderado y DBSF

- **RRF ponderado:** `Σ w_r / (k + rango)`. Si tus usuarios buscan sobre todo por siglas, das más peso a BM25.
  Vuelve a haber un hiperparámetro que calibrar, así que úsalo solo si tu evaluación muestra que una de las dos
  búsquedas es claramente mejor en tus consultas.

  > **Verifica la librería antes de confiar en ella.** Qdrant expone `Rrf(k=60, weights=[...])`, pero al medirlo en
  > este curso (`qdrant-client` 1.20, modo embebido) su efecto **no** coincidió con la fórmula: con pesos `[1, 3]` el
  > documento favorecido fue el de la lista con peso 1, y los puntajes casi no se movieron. Puede ser una semántica
  > distinta o un detalle del modo embebido; no lo pude contrastar con el servidor. Si necesitas RRF ponderado, haz
  > la fusión tú mismo con los resultados de cada búsqueda: es una función de cinco líneas
  > ([`code/03_rrf.py`](code/03_rrf.py), `rrf(rankings, k, pesos)`) y sabes exactamente qué calcula.
- **DBSF** (*Distribution-Based Score Fusion*), disponible en Qdrant como `Fusion.DBSF`: normaliza cada lista usando
  su media y desviación (en lugar de min-max), que es más robusto a valores atípicos, y luego suma. Es una fusión por
  puntaje bien hecha. Pruébala frente a RRF con tu evaluación; no hay un ganador universal.

---

<a name="9-dispersos"></a>
## 9. BM25 como vector disperso

Un embedding es un vector **denso**: cientos de dimensiones, casi todas distintas de cero. BM25 se puede ver como un
vector **disperso**: una dimensión por término del vocabulario (decenas de miles), casi todas en cero, y valores solo
en los términos que aparecen en el documento.

```
denso    [0.12, -0.03, 0.88, ..., 0.41]           384 valores, todos distintos de cero
disperso {"kafka": 1.71, "flink": 1.71, "aws": 1.0} 3 valores no nulos de un vocabulario enorme
```

El producto punto de dos vectores dispersos solo toca los términos en común, y esa es exactamente la suma de BM25. Si
guardas en cada documento el **factor de frecuencia** de cada término (la fracción de la §3, ya con saturación y
normalización por longitud) y dejas que la base de datos aplique el **IDF**, el producto punto con la consulta da el
puntaje BM25. Qdrant hace la parte del IDF con `SparseVectorParams(modifier=Modifier.IDF)`.

Dos detalles prácticos:

- **El índice de cada término** debe ser estable: usa un hash determinista como `crc32`. El `hash()` de Python cambia
  en cada ejecución (por seguridad), y si lo usas, tu índice deja de coincidir con tus consultas al reiniciar.
- **Vectores dispersos aprendidos (SPLADE y similares):** un modelo decide qué términos poner y con qué peso, incluso
  términos que *no* están en el texto pero son relevantes (para "Kafka" puede añadir "streaming"). Son un punto medio
  entre BM25 y los embeddings. Vale la pena conocerlos; para empezar, BM25 es más simple, rápido y explicable.

---

<a name="10-qdrant"></a>
## 10. Híbrida de punta a punta en Qdrant

Qdrant guarda **varios vectores con nombre** en el mismo punto, así que cada CV lleva su vector denso y su vector BM25.
La consulta híbrida usa la **Query API**: dos *prefetch* (uno por buscador) y una fusión.

```python
from qdrant_client import models

client.create_collection(
    "cvs",
    vectors_config={"denso": models.VectorParams(size=384, distance=models.Distance.COSINE)},
    sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
)

client.upsert("cvs", points=[
    models.PointStruct(id=i, payload=meta, vector={
        "denso": embed([texto])[0].tolist(),
        "bm25": vector_bm25_documento(texto),   # índices crc32 + factor de frecuencia
    })
    for i, (texto, meta) in enumerate(datos)
])

hits = client.query_points(
    "cvs",
    prefetch=[
        models.Prefetch(query=embed([consulta])[0].tolist(), using="denso", limit=20),
        models.Prefetch(query=vector_bm25_consulta(consulta), using="bm25", limit=20),
    ],
    query=models.RrfQuery(rrf=models.Rrf(k=60)),   # o models.FusionQuery(fusion=models.Fusion.RRF)
    limit=5,
).points
```

Cada *prefetch* trae sus candidatos (20 por lado) y la fusión decide el top-5 final. Puedes añadir `filter=` a cada
*prefetch* para combinar con la metadata del Módulo 3: "híbrida, pero solo seniors". Código completo, ejecutable sin
Docker, en [`code/04_hibrida_qdrant.py`](code/04_hibrida_qdrant.py).

---

<a name="11-rerank"></a>
## 11. Después de fusionar: re-ranking

La fusión decide qué candidatos llegan arriba usando señales baratas. Un **re-ranker** (un *cross-encoder* que lee la
consulta y el documento **juntos**) es mucho más preciso, pero cuesta mucho más por documento. El patrón estándar:

```
híbrida (barata) -> top 50  ->  re-ranker (caro) -> top 5  ->  LLM (Módulo 3)
```

Solo pagas el re-ranker sobre 50 documentos, no sobre toda la colección. Mide si te compensa: si la híbrida ya pone
lo relevante en el top 5, el re-ranker solo añade latencia.

---

<a name="12-medir"></a>
## 12. Medir: léxica vs. semántica vs. híbrida

Todo lo anterior es teoría hasta que lo mides en **tus** consultas. Con el set etiquetado del Módulo 2 (`recall@k`,
`MRR`), corre las tres búsquedas sobre las mismas consultas y compáralas:

| Búsqueda | recall@3 | MRR |
|---|---|---|
| BM25 | ? | ? |
| Semántica | ? | ? |
| Híbrida (RRF) | ? | ? |

Lo esperable es que la híbrida **no sea peor que la mejor de las dos** en el total y que gane en las consultas
mixtas. Lo que **no** debes esperar es que gane en todas: en una consulta puramente léxica, BM25 solo puede ser igual
o mejor. El laboratorio [`code/05_comparar_busquedas.py`](code/05_comparar_busquedas.py) imprime la tabla real y el
desglose por consulta, para que veas **dónde** gana y pierde cada una.

> Si tu tabla dice que la híbrida es peor que una de las dos, no lo escondas: mira qué consultas pierde. Suele
> deberse a un tokenizador malo para BM25 (§4) o a un `limit` de *prefetch* demasiado bajo, que deja fuera candidatos
> buenos antes de fusionar.

### Lo que salió en el corpus del laboratorio (8 CVs, 11 consultas, modelo local MiniLM)

| Búsqueda | recall@3 | MRR | recall@3 en paráfrasis |
|---|---|---|---|
| BM25 | 0.77 | 0.82 | 0.33 |
| Semántica | 0.95 | 0.91 | 1.00 |
| Híbrida (RRF) | 0.95 | 0.91 | 1.00 |

Lectura honesta:

- **BM25 se hunde en las paráfrasis** ("experiencia con streaming", "aprendizaje automático"): no comparte ni un
  término con el CV correcto, así que no devuelve nada. Es exactamente la debilidad de la §5.
- **La híbrida empata con la semántica, no la supera.** Con 8 documentos, el top-3 ya es casi la mitad de la
  colección: es un examen fácil para la semántica. Y donde la híbrida debía ganar ("ISO 27001"), se produjo un
  **empate simétrico** que RRF no puede romper (§7).
- **Nadie encuentra a Diego con "AWS"** (su CV dice "Amazon Web Services"): BM25 no puede por diseño, y el modelo
  pequeño no conoce la equivalencia. La híbrida no puede rescatar lo que ningún buscador trajo. Un modelo de
  embeddings mejor, o un sinónimo en el tokenizador (`aws -> amazon web services`), sí.

La moraleja no es "la híbrida no sirve": es que **el beneficio aparece con colecciones grandes y consultas difíciles**,
y que solo lo sabrás midiendo sobre tus datos. Con miles de CVs, el top-3 es una fracción mínima y los errores de cada
buscador por separado cuestan mucho más.

---

<a name="13-proyecto"></a>
## 13. Proyecto del módulo

Entregable: **el buscador de CVs híbrido.**

1. **Tokenizador** en español con minúsculas, sin tildes, *stopwords* y excepciones técnicas (`c++`, `c#`, `.net`,
   `node.js`).
2. **Colección** con dos vectores por chunk de CV (los chunks del Módulo 3): `denso` (embedding) y `bm25` (disperso,
   con `Modifier.IDF`).
3. **`buscar(consulta, modo)`** con `modo` en `{"bm25", "semantica", "hibrida"}`, donde la híbrida usa RRF.
4. **Filtro de metadata** opcional en la híbrida ("solo seniors").
5. **Evaluación:** un set de 10-15 consultas etiquetadas con al menos tres tipos: siglas o códigos exactos, paráfrasis
   y mixtas. Tabla de `recall@3` y `MRR` para los tres modos, con tu lectura de dónde gana cada uno.

Criterios de la rúbrica:

- La consulta y los documentos pasan por **el mismo tokenizador**.
- Los índices del vector disperso son **estables** entre ejecuciones (hash determinista).
- La fusión es **RRF** y puedes explicar qué hace `k`.
- Tienes la **tabla de los tres modos** y la interpretas con honestidad, incluidas las consultas donde la híbrida no
  gana.

En el **Módulo 5** dejamos de tratar la búsqueda como una llamada aislada: la convertimos en una **herramienta** dentro
de un *workflow* o de un agente que decide cuándo buscar, con qué filtros y qué hacer con lo que encuentra.

---

## Resumen del módulo (lo que no puedes olvidar)

- La semántica pierde lo **exacto**: siglas, códigos, nombres raros, versiones. BM25 lo conserva.
- **BM25 = IDF** (los términos raros pesan) **+ saturación** (repetir rinde poco) **+ normalización por longitud**.
- En búsqueda léxica, **el tokenizador es la mitad del resultado**, y consulta y documento deben compartirlo.
- Sumar puntajes de escalas distintas no funciona; **RRF combina por puesto** y no necesita calibración.
- BM25 es un **vector disperso**: Qdrant aplica el IDF y fusiona con la Query API (`prefetch` + RRF).
- La híbrida no gana siempre: **mide los tres modos** y lee el desglose por consulta.

Sigue con [`ejercicios.md`](ejercicios.md).
