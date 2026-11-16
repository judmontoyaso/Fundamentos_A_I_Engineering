# Módulo 2 · Embeddings y búsqueda semántica

> **Objetivo:** entender qué es un embedding y cómo representa el significado de un texto, cómo se mide la
> similitud entre dos textos, cómo se guardan y consultan millones de vectores en una *vector database*, y montar tu
> primera búsqueda semántica sobre los CVs que estructuraste en el Módulo 1.
>
> **Pieza del proyecto:** indexar los CVs por *significado* para poder preguntar "quién sabe de pipelines de datos
> en tiempo real" y recuperar los candidatos correctos aunque esas palabras exactas no estén en el CV.

Índice:

1. [El problema: por qué la búsqueda por palabras falla](#1-el-problema)
2. [Qué es un embedding (la intuición geométrica)](#2-que-es)
3. [De dónde sale el significado: cómo se entrenan](#3-entrenamiento)
4. [Medir similitud: coseno, producto punto y distancia](#4-similitud)
5. [Propiedades y trampas de los embeddings](#5-trampas)
6. [Elegir el modelo de embeddings](#6-elegir-modelo)
7. [Qué hace una vector database (ANN y HNSW)](#7-vector-db)
8. [Elegir la base de datos](#8-elegir-db)
9. [Qdrant en la práctica](#9-qdrant)
10. [Indexar los CVs del Módulo 1](#10-indexar)
11. [¿Y esto qué tan bien recupera? (eval de retrieval)](#11-eval)
12. [Economía y operación](#12-economia)
13. [Proyecto del módulo](#13-proyecto)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-el-problema"></a>
## 1. El problema: por qué la búsqueda por palabras falla

Tu buscador de CVs recibe la consulta: **"experiencia en procesamiento de datos en streaming"**. Un candidato
perfecto escribió en su CV: *"4 años construyendo pipelines con Apache Kafka y Flink en tiempo real"*. No comparte
**ni una sola palabra** con la consulta, aparte de las preposiciones. Una búsqueda léxica, ya sea con
`LIKE '%streaming%'` o con BM25, no lo encuentra, aunque sea justo el candidato que se necesita.

Ese es el límite de cualquier búsqueda que compara la *forma de las palabras*: el lenguaje tiene **sinónimos**
("streaming" ≈ "tiempo real"), **hiperónimos** ("Kafka" es un "sistema de mensajería"), **paráfrasis** y **otros
idiomas**, y las personas buscan por lo que quieren decir, sin saber qué palabras exactas usó el documento.

La búsqueda semántica cambia la pregunta: en lugar de comprobar si dos textos comparten caracteres, compara si
significan lo mismo. Para que una máquina pueda hacer esa comparación, primero hay que convertir el significado en
algo medible, que es un **vector**, y para eso sirven los embeddings.

> En resumen, **la búsqueda léxica compara cadenas y la búsqueda semántica compara significados.** El resto del
> módulo explica cómo se construye y se opera la segunda. En el Módulo 4 las combinamos, porque cada una funciona
> mejor en situaciones distintas.

---

<a name="2-que-es"></a>
## 2. Qué es un embedding (la intuición geométrica)

Un **embedding** es una lista de números —un vector— que representa un trozo de texto (una palabra, una frase, un
CV entero) como un **punto en un espacio de muchas dimensiones** (típicamente 384, 768, 1536, 3072…).

Los números por separado no dicen mucho; lo que importa es **cómo quedan colocados los puntos**: el modelo de embeddings se
entrena para que **textos con significado parecido queden cerca** en ese espacio, y textos con significado distinto
queden lejos. "Perro" y "cachorro" caen casi en el mismo lugar; "perro" y "ecuación diferencial" caen en extremos
opuestos.

Una forma útil de imaginarlo es un mapa. En un mapa 2D, Bogotá y Medellín están cerca, y ambas lejos de Tokio.
Un embedding es ese mismo mapa, pero del **significado**, y con cientos de dimensiones en vez de dos (latitud/longitud).
Cada dimensión captura, de forma difusa, algún "eje" de significado que el modelo aprendió (formalidad, tema, tono,
dominio técnico…). No son interpretables una por una, pero *en conjunto* ubican el texto.

Una propiedad conocida de los embeddings clásicos, aunque hoy tiene menos peso práctico, es que la **aritmética de
vectores** captura relaciones:

```
vector("rey") - vector("hombre") + vector("mujer") ≈ vector("reina")
```

Esto muestra que las *direcciones* del espacio tienen significado. Para la búsqueda, lo que nos interesa es la
consecuencia práctica:

> **Si dos textos significan algo parecido, sus vectores apuntan en direcciones parecidas. Buscar = encontrar los
> vectores más cercanos al vector de la consulta.**

---

<a name="3-entrenamiento"></a>
## 3. De dónde sale el significado: cómo se entrenan

No necesitas entrenar embeddings, pero entender *cómo* se hace explica sus límites (sección 5). La técnica dominante
es el **aprendizaje contrastivo**:

1. Al modelo se le muestran **pares positivos** (textos que *deberían* estar cerca: una pregunta y su respuesta
   correcta, una frase y su traducción, un título y su párrafo) y **pares negativos** (textos que no tienen que ver).
2. Se ajustan los pesos para **acercar** los positivos y **alejar** los negativos en el espacio vectorial.
3. Repetido sobre cientos de millones de pares, el modelo aprende una geometría donde "cercanía = similitud de
   significado" para el *tipo de datos y tareas* con los que se entrenó.

De aquí salen dos consecuencias importantes:

- **Un embedding es tan bueno como sus datos de entrenamiento.** Un modelo entrenado sobre inglés general será
  mediocre en CVs técnicos en español o en jerga médica. El *dominio* importa.
- **"Similar" lo define la tarea de entrenamiento**, no una verdad universal. Algunos modelos tratan pregunta↔respuesta
  como "similares" (bueno para QA); otros tratan solo paráfrasis como similares. Por eso muchos modelos distinguen
  entre embedear una **query** y embedear un **documento** (ver §6).

---

<a name="4-similitud"></a>
## 4. Medir similitud: coseno, producto punto y distancia

Dados dos vectores, hay tres formas habituales de medir qué tan parecidos son, y elegir la correcta evita errores
que no producen ningún mensaje.

**Similitud coseno**: mide el **ángulo** entre los vectores, ignora su longitud. Es la más usada en NLP:

```
cos(a, b) = (a · b) / (|a| · |b|)      ∈ [-1, 1]   (1 = misma dirección)
```

Se usa el ángulo porque, en texto, la *longitud* del vector suele estar relacionada con la frecuencia de las
palabras o con el largo del texto, y no queremos que eso domine la similitud. El significado está en la
**dirección**: dos CVs sobre lo mismo, uno de una página y otro de tres, deben salir parecidos, y el coseno lo
consigue.

**Producto punto (dot product)**: como el coseno pero **sin normalizar**: tiene en cuenta la magnitud.

```
dot(a, b) = a · b
```

En la práctica, **si tus vectores ya están normalizados** (longitud 1), entonces `dot == coseno`, y el producto
punto es más barato de calcular. Muchos modelos devuelven vectores ya normalizados; en ese caso usa `dot` en la DB.

**Distancia euclidiana (L2)**: la distancia "en línea recta" entre los puntos:

```
L2(a, b) = sqrt( Σ (aᵢ - bᵢ)² )       (0 = idénticos; mayor = más lejos)
```

Es *distancia* (menor = más parecido), al revés de las similitudes (mayor = más parecido). Sobre vectores
normalizados, L2 y coseno dan el **mismo ranking** (orden de vecinos), así que da igual para buscar; cambia la escala.

> **Un error frecuente al empezar** es configurar en la vector DB una métrica distinta a la que espera el modelo de
> embeddings. Si el modelo se entrenó para coseno y la colección usa L2 sin normalizar, nada falla de forma visible:
> simplemente recupera peor, y cuesta horas encontrar la causa. **Usa la métrica que indica la tarjeta del modelo**,
> que casi siempre es coseno o producto punto sobre vectores normalizados. Ver
> [`code/04_similitud.py`](code/04_similitud.py).

---

<a name="5-trampas"></a>
## 5. Propiedades y trampas de los embeddings

Estas son las limitaciones que más problemas causan en producción:

- **Dominio e idioma.** Un modelo general en inglés rinde pobre en CVs en español. Usa un modelo **multilingüe** o
  específico de dominio si tu texto lo es. Mídelo, no lo asumas (§11).
- **Dimensionalidad ≠ calidad.** Un modelo de 3072 dims no es "el doble de bueno" que uno de 1536. Más dimensiones =
  más memoria y cómputo por vector (a millones de vectores, eso es dinero y RAM). Elige por **calidad medida**, no por
  tamaño.
- **Ventana de contexto del embedder.** Cada modelo embedea hasta N tokens; lo que pase de ahí se **trunca en silencio**.
  Un CV largo puede perder su segunda mitad. Esto motiva el **chunking** (Módulo 3): no embedees documentos gigantes
  de un solo golpe.
- **Un solo vector promedia todo.** Embedear un CV entero en un vector mezcla "experto en Python" con "hobby:
  cocina". Para preguntas específicas, chunks separados recuperan mejor (Módulo 3).
- **Simetría query/documento.** Algunos modelos piden un **prefijo o instrucción** distinta para queries vs. documentos
  (p. ej. `"query: ..."` / `"passage: ..."`). Ignorarlo degrada el recall. Lee la tarjeta del modelo.
- **No son determinismo absoluto entre versiones.** Si cambias de modelo de embeddings, **debes re-embedear todo**:
  los vectores de dos modelos distintos no viven en el mismo espacio y no son comparables. Versiona tu índice.

---

<a name="6-elegir-modelo"></a>
## 6. Elegir el modelo de embeddings

Ejes de decisión, en orden de impacto:

1. **Calidad en tu tarea y tu idioma.** El benchmark **MTEB** sirve como punto de partida, siempre que filtres por
   tarea (retrieval) e idioma (español o multilingüe) en lugar de mirar el ranking global. La decisión final la da tu
   propia evaluación (§11) sobre una muestra de tus CVs y consultas reales.
2. **API vs. local.**
   - *API* (OpenAI `text-embedding-3-*`, Voyage, Cohere, Gemini): cero infraestructura, siempre al día, pero pagas por
     token y tus textos salen de tu red.
   - *Local / open-source* (familia **BGE**, **E5**, **GTE**, `sentence-transformers`): gratis por uso, privado,
     corre en tu máquina/GPU, pero tú lo operas. Para datos sensibles (¡CVs tienen datos personales!), local es a
     menudo la respuesta correcta por privacidad.
3. **Dimensión y costo de almacenamiento.** A millones de vectores, 1536 vs 768 dims es el doble de RAM en el índice.
4. **Longitud de contexto** del embedder (cuántos tokens admite por texto).
5. **Matryoshka (MRL).** Varios modelos modernos (p. ej. `text-embedding-3-*`, `bge-m3`) permiten **truncar** el
   vector a menos dimensiones perdiendo poca calidad: embedeas a 1536 y, si te sobra, usas los primeros 512 para
   ahorrar memoria. Es una palanca costo/calidad muy práctica. Ver [`code/06_embeddings_reales.py`](code/06_embeddings_reales.py),
y para elegir modelo midiendo, [`code/12_elegir_modelo.py`](code/12_elegir_modelo.py).

### Lo que dio la medición, y por qué no alcanza para decidir

`12_elegir_modelo.py` compara cinco configuraciones sobre los 10 CVs del Módulo 9 con 10 consultas de paráfrasis.
Dos pasadas dieron exactamente lo mismo (un embedding es determinista; la variación que viste en el Módulo 7 era del
LLM):

| Modelo | recall@1 | recall@3 | MRR | Dim. | Consulta que falla en el primer puesto |
|---|---|---|---|---|---|
| MiniLM multilingüe (local) | 0.90 | 1.00 | 0.95 | 384 | "orquestación de contenedores…" → Laura |
| E5-small sin prefijos | 0.90 | 0.95 | 0.93 | 384 | "líder de ingeniería de datos con inglés fluido" → Laura |
| E5-small con prefijos | 0.90 | 0.95 | 0.95 | 384 | la misma |
| `text-embedding-3-small` (API) | 0.90 | 1.00 | 0.93 | 1536 | la misma → Valentina |
| `text-embedding-3-large` (API) | 0.90 | 1.00 | 0.95 | 3072 | la misma → Laura |

El resultado es un **empate**: cada modelo falla una sola consulta y las diferencias de MRR equivalen a un puesto en
una consulta. Los prefijos de E5 ayudaron poco (de 0.93 a 0.95) y un vector ocho veces más grande no mejoró nada. Eso
no quiere decir que el modelo sea indiferente, sino que **este conjunto es demasiado fácil para elegir**: con 10 CVs
muy distintos entre sí, casi cualquier modelo acierta. El Módulo 9 encontró justo el caso que este set no tiene: **consultas largas con varios
requisitos**, donde MiniLM sí se quedaba atrás (Módulo 9 §4, arreglo 5). Para elegir de verdad, el set tiene que
parecerse a lo que buscan tus usuarios y tener candidatos parecidos entre sí.

**Para el proyecto**, empieza con un modelo multilingüe sólido: por API, `text-embedding-3-small` por simplicidad,
o en local, `BAAI/bge-m3` para que los CVs no salgan de tu máquina. Cuando funcione, mide, y cambia de modelo solo si
la evaluación lo justifica.

---

<a name="7-vector-db"></a>
## 7. Qué hace una vector database (ANN y HNSW)

Con lo anterior ya puedes convertir texto en vectores y medir su similitud. Guardar los vectores en una lista y
comparar cada consulta contra todos funciona con pocos documentos, pero **no escala**: comparar la query contra 10 millones de CVs vector-a-vector
(**k-NN exacto**, fuerza bruta) es O(n) por consulta y se vuelve lentísimo.

Una **vector database** resuelve esto con búsqueda de **vecinos aproximados** (**ANN**, *Approximate Nearest
Neighbors*): sacrifica un poco de exactitud (a veces no te da el vecino más cercano exacto; cuánto depende de los parámetros del índice) a cambio
de ser **órdenes de magnitud más rápida**. El algoritmo dominante es **HNSW** (*Hierarchical Navigable Small World*):

- Construye un **grafo de varios niveles**. Los niveles altos tienen pocos nodos muy conectados, como una red de
  autopistas, y el nivel más bajo tiene todos los nodos, como las calles de un barrio.
- Para buscar, **entra por el nivel más alto** y avanza hacia vecinos cada vez más cercanos a la consulta mientras
  baja de nivel. Así llega a la zona correcta visitando una fracción muy pequeña de los nodos.
- Parámetros que verás: `m` (conexiones por nodo), `ef_construct` (esfuerzo al construir) y `ef`/`hnsw_ef` (esfuerzo
  al buscar). Más alto = mejor recall, más lento/más memoria. Es la perilla **velocidad ↔ exactitud**.

Además de buscar vectores, una vector DB completa ofrece: **payload** (metadata adjunta a cada vector: nivel, área,
años), **filtrado** por ese payload combinado con la búsqueda vectorial (clave para el Módulo 3), persistencia,
actualización, sharding y cuantización (comprimir vectores para que quepan más en RAM).

---

<a name="8-elegir-db"></a>
## 8. Elegir la base de datos

Las opciones más comunes, en una frase cada una:

- **Qdrant**: open source, escrito en Rust, rápido, con muy buen filtrado por payload y fácil de correr en local
  (Docker) o en la nube. Es la que usamos, porque sirve tanto para aprender como para producción.
- **pgvector**: extensión de PostgreSQL. Si **ya** tienes Postgres y volúmenes moderados, es lo más simple: tus
  vectores viven junto a tus datos relacionales, una sola base que operar.
- **Milvus / Weaviate**: pensadas para colecciones muy grandes, con más componentes que operar.
- **FAISS / hnswlib**: son librerías y no bases de datos. Buscan muy rápido en memoria, pero no traen persistencia,
  filtrado ni servidor. Sirven para prototipos o como motor dentro de otra aplicación.
- **Pinecone**: servicio gestionado; no operas ninguna infraestructura y a cambio pagas por el servicio.

Para decidir, conviene preguntarse si necesitas **filtrar** por metadata (con CVs, sí), si prefieres un servicio
**gestionado o alojado por ti**, qué exige la **privacidad** de los datos (con datos personales suele convenir
alojarlo tú) y cuál es la escala, si miles o miles de millones de vectores. Para el proyecto usamos **Qdrant en local
con Docker**, que es gratuito, mantiene los datos en tu máquina y tiene todo lo que necesitamos.

---

<a name="9-qdrant"></a>
## 9. Qdrant en la práctica

Para levantar Qdrant en local con Docker basta un comando:

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

¿Sin Docker? `qdrant-client` trae un **modo embebido**: `QdrantClient(location=":memory:")` corre la base dentro
de tu proceso (o `QdrantClient(path="./qdrant_data")` para que persista en disco). Es cómodo para aprender y
para pruebas; en producción conviene usar el servidor. Los scripts de este curso leen `QDRANT_URL`, así que basta con
`QDRANT_URL=:memory:`.

Los tres verbos que necesitas: **crear colección**, **upsert** (insertar/actualizar puntos) y **search**.

```python
# code/09_qdrant_basico.py (resumen)
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(url="http://localhost:6333")

# 1. Crear colección: dimensión = la del modelo, métrica = la que el modelo espera
if client.collection_exists("cvs"):
    client.delete_collection("cvs")
client.create_collection(
    collection_name="cvs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# 2. Upsert: cada punto = id + vector + payload (metadata para filtrar)
client.upsert("cvs", points=[
    PointStruct(id=1, vector=emb1, payload={"nombre": "Laura", "nivel": "senior", "areas": ["datos"]}),
    PointStruct(id=2, vector=emb2, payload={"nombre": "Juan",  "nivel": "junior", "areas": ["ingenieria"]}),
])

# 3. Search: vector de la query -> k vecinos más cercanos
hits = client.query_points("cvs", query=emb_query, limit=5).points
for h in hits:
    print(h.score, h.payload["nombre"])
```

Tres puntos a tener en cuenta:

- **`size` y `distance` deben casar con tu modelo** de embeddings (§4, §5). Cambiar de modelo = recrear colección.
- El **payload** es lo que convierte "busco algo parecido" en "busco algo parecido **y** que sea senior **y** del área
  de datos". Ese filtrado combinado es el puente al Módulo 3.
- `score` es la similitud (coseno aquí): mayor = más relevante.

El ejemplo completo y ejecutable está en [`code/09_qdrant_basico.py`](code/09_qdrant_basico.py).

---

<a name="10-indexar"></a>
## 10. Indexar los CVs del Módulo 1

Ahora conectamos los dos módulos. En el Módulo 1 convertiste cada PDF en un objeto `CV` estructurado. Aquí:

1. Construyes un **texto representativo** del CV para embedear (no el PDF crudo: un resumen de los campos que importan
   para buscar: skills, cargos, áreas). *Qué* texto embedeas decide *qué* se puede encontrar.
2. Lo embedeas con tu modelo.
3. Lo subes a Qdrant con **payload = los campos estructurados del `CV`** (nivel, áreas, años), para poder filtrar.

```python
# code/10_indexar_cvs.py (idea)
def texto_para_embedding(cv: CV) -> str:
    # El "documento" que se busca: concatena lo semánticamente relevante.
    return (
        f"{cv.nombre_completo}. Nivel {cv.nivel}. "
        f"Áreas: {', '.join(a.value for a in cv.areas)}. "
        f"Skills: {', '.join(cv.skills)}. "
        + " ".join(f"{e.cargo} en {e.empresa}." for e in cv.experiencia)
    )
```

Este es un patrón central de RAG: **el embedding indexa un texto que tú diseñas**, que no tiene por qué ser el
documento literal. Decidir qué incluir y qué dejar fuera de ese texto pesa tanto como elegir el modelo. Lo formalizamos como
*chunking* en el Módulo 3.

Luego una consulta en lenguaje natural ("alguien senior que sepa de streaming de datos") se embedea y Qdrant devuelve
los CVs cuyo texto-índice está más cerca: recuperando a la persona de Kafka/Flink de la §1, que la búsqueda léxica
no veía.

---

<a name="11-eval"></a>
## 11. ¿Y esto qué tan bien recupera? (eval de retrieval)

Que la búsqueda se vea bien en tres ejemplos no dice mucho, así que hay que **medirla**. Estas son las métricas
básicas de retrieval:

- **Recall@k**: de los documentos realmente relevantes, ¿qué fracción apareció en el top-k? (¿Está el candidato bueno
  entre los primeros 5?) Es la métrica más importante para un buscador, porque si el documento relevante no está en
  el top-k, el usuario nunca lo ve.
- **Precision@k**: de los k que devolviste, ¿qué fracción es relevante? (¿Cuánta basura hay arriba?)
- **MRR** (*Mean Reciprocal Rank*): ¿qué tan arriba sale el primer relevante? Premia poner lo bueno de primero.
- **nDCG**: como precision pero pondera la posición (relevante en #1 vale más que en #10).

Para medir necesitas un pequeño **conjunto etiquetado**: entre 20 y 50 consultas con sus CVs relevantes marcados a
mano. Armarlo es tedioso, pero es de lo que más rinde en todo el proyecto, porque sin él no hay forma de saber si un
cambio mejoró la búsqueda. Volvemos a evals en serio en el Módulo 7. Ejemplo de `recall@k` en
[`code/11_eval_retrieval.py`](code/11_eval_retrieval.py).

---

<a name="12-economia"></a>
## 12. Economía y operación

- **Costo de embedear** ≈ tokens × precio del modelo de embeddings (mucho más barato que generación). El gasto
  grande es **la primera indexación** de todo el corpus; luego solo embedeas lo nuevo.
- **Cachea los embeddings** igual que cacheaste extracciones (Módulo 1 §13): embedear es determinista por (texto,
  modelo), así que guarda `hash(texto+modelo) -> vector` y no vuelvas a pagar al reindexar.
- **Memoria del índice** ≈ n_vectores × dim × 4 bytes (float32), más el grafo HNSW. 1M de CVs a 1536 dims ≈ ~6 GB
  solo en vectores. Palancas: menos dims (Matryoshka, §6) o **cuantización** (Qdrant comprime a int8/binario con poca
  pérdida de recall y gran ahorro de RAM).
- **Re-embedear al cambiar de modelo** es costoso: planifícalo y versiona la colección (`cvs_v2`).

---

<a name="13-proyecto"></a>
## 13. Proyecto del módulo

Entregable: **el índice semántico de los CVs** del buscador.

1. Toma los objetos `CV` del Módulo 1 (usa 10–20 CVs de ejemplo; invéntalos o usa PDFs tuyos).
2. Genera `texto_para_embedding(cv)` para cada uno, embedéalos (con caché) y súbelos a una colección Qdrant con
   `payload` = campos del `CV`.
3. Implementa `buscar(consulta: str, k=5)` que embedea la consulta y devuelve los k CVs más cercanos, mostrando
   `score`, nombre y áreas.
4. Prueba con 3 consultas en las que **la palabra exacta no esté en el CV** y verifica que aun así recupera al
   candidato correcto, que es justamente lo que la búsqueda léxica no lograba.
5. **Mide** `recall@5` con un mini set etiquetado de ~10 consultas.

Criterios de la rúbrica:

- La métrica de la colección **casa** con el modelo de embeddings.
- Embedeas un **texto diseñado**, no el PDF crudo, y puedes explicar qué incluiste y por qué.
- Los embeddings están **cacheados**.
- Tienes un número de `recall@k`, no una impresión.

En el **Módulo 3** verás que embedear el CV entero en un vector es tosco: lo partiremos en **chunks** y añadiremos
**metadata filtering** para subir el recall y poder responder preguntas más finas.

---

## Resumen del módulo

- La búsqueda léxica compara cadenas; la **semántica compara significados** vía vectores.
- Un **embedding** coloca textos en un espacio donde *cerca = significa parecido*; buscar = hallar los vectores más
  cercanos a la query.
- **Coseno** (ángulo) es el default; sobre vectores normalizados, `dot == coseno`. **Usa la métrica que pide el modelo.**
- Los embeddings heredan los **sesgos de su entrenamiento**: dominio, idioma y longitud de contexto importan; mídelo.
- Una **vector DB** usa ANN/HNSW para buscar entre millones en milisegundos, y **payload + filtrado** para combinar
  significado con reglas.
- **Mide el retrieval** con recall@k; sin una evaluación no hay forma de saber si un cambio ayudó.
- Cachea los embeddings. Con muchos vectores, la dimensión y la cuantización determinan cuánta memoria necesitas.

Sigue con [`ejercicios.md`](ejercicios.md).
