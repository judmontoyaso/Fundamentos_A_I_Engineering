# Módulo 4 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas).

---

### Ejercicio 1 — BM25 a mano
Con [`code/01_bm25_desde_cero.py`](code/01_bm25_desde_cero.py), calcula a mano (con calculadora) el puntaje de la
consulta "kafka" para el primer CV. Necesitas `N`, `n("kafka")`, `f`, `|D|` y `avgdl`; imprímelos desde el objeto
`BM25`. Comprueba que tu número coincide con el que devuelve `puntaje()`.

### Ejercicio 2 — Los hiperparámetros
En el mismo script, prueba `k1 = 0.5, 1.2, 3.0` y `b = 0, 0.75, 1`. ¿Qué pasa con la consulta "python" (un CV la
repite cinco veces) en cada caso? Explica qué controla cada parámetro con tus palabras.

### Ejercicio 3 — El tokenizador decide
Quita la normalización de tildes de `tokenizar()` y busca "programacion" (sin tilde) en un CV que dice "programación".
Luego quita las excepciones técnicas y busca "C#". ¿Qué se rompe en cada caso? Añade una regla de sinónimos
`aws -> amazon web services` y comprueba si Diego aparece en la consulta "AWS" del laboratorio.

### Ejercicio 4 — RRF y el parámetro k
Con [`code/03_rrf.py`](code/03_rrf.py), construye dos rankings donde un documento sea 1º en una lista y no aparezca
en la otra, y otro documento sea 3º en ambas. ¿Cuál gana con `k = 1`? ¿Y con `k = 60`? ¿Qué preferencia expresa cada
valor de `k`?

### Ejercicio 5 — Suma normalizada vs. RRF
En `03_rrf.py`, cambia los puntajes de coseno para que haya un valor atípico (por ejemplo `{"C": 0.95, "A": 0.41,
"D": 0.40}`). ¿Cómo cambia el orden de la suma normalizada con `α = 0.5`? ¿Y el de RRF? ¿Por qué?

### Ejercicio 6 — El empate simétrico
En el laboratorio, la consulta "ISO 27001" empata en RRF. Rómpelo de dos maneras: (a) con un RRF ponderado hecho por
ti (usa `rrf(..., pesos=[...])` de `03_rrf.py` sobre los ids de cada búsqueda), y (b) cambiando la consulta a "ISO
27001 auditor". ¿Cuál de las dos soluciones es más honesta para un buscador real?

### Ejercicio 7 — Prefetch y candidatos
En [`code/04_hibrida_qdrant.py`](code/04_hibrida_qdrant.py), baja `candidatos` a 1 y vuelve a correr
[`code/05_comparar_busquedas.py`](code/05_comparar_busquedas.py). ¿Qué le pasa al recall de la híbrida? Explica por
qué un `limit` de *prefetch* demasiado bajo perjudica a la fusión.

### Ejercicio 8 — Proyecto
Monta la búsqueda híbrida del §13 sobre tus chunks de CV del Módulo 3. Arma 12 consultas etiquetadas (4 exactas, 4
paráfrasis, 4 mixtas), corre los tres modos y escribe tres párrafos: dónde gana BM25, dónde gana la semántica y si la
híbrida compensa en **tu** colección. Si no compensa, di por qué.

---

<details>
<summary><b>Soluciones</b></summary>

**1.** `IDF = ln((N − n + 0.5)/(n + 0.5) + 1)`; con `N = 5` y `n = 1`: `ln(4.5/1.5 + 1) = ln 4 ≈ 1.386`. El factor de
frecuencia es `f·(k1+1)/(f + k1·(1 − b + b·|D|/avgdl))` con `f = 1`. Multiplica los dos: debe coincidir con
`puntaje()` hasta el tercer decimal. Si no coincide, casi siempre es porque contaste `|D|` con otro tokenizador
(stopwords incluidas).

**2.** `k1` controla la **saturación**: con `k1` bajo, repetir un término apenas suma (el aporte llega al techo
enseguida); con `k1` alto, cada repetición sigue sumando, y el CV que repite "python" cinco veces se aleja del resto.
`b` controla la **normalización por longitud**: con `b = 0` un CV largo no se penaliza; con `b = 1` se penaliza del
todo. El CV con cinco "python" es más largo, así que `b` alto le resta parte de lo que gana por repetición.

**3.** Sin quitar tildes, "programacion" y "programación" son términos distintos y no hay coincidencia. Sin
excepciones, "C#" se queda en "c" (o desaparece), que coincide con cualquier cosa o con nada. Con el sinónimo
`aws -> amazon web services` aplicado en el tokenizador (a documentos **y** consultas), la consulta "AWS" comparte
términos con el CV de Diego y BM25 lo encuentra: es la forma más barata de arreglar lo que el modelo pequeño no sabe.

**4.** Con `k = 1`: el 1º de una sola lista suma `1/2 = 0.5` y el 3º de ambas `2·1/4 = 0.5`: empate. Con `k = 60`: el
1º de una lista suma `1/61 ≈ 0.0164` y el 3º de ambas `2/63 ≈ 0.0317`, que gana con claridad. `k` pequeño premia
ser **primero** en algún sitio; `k` grande premia el **consenso** entre buscadores.

**5.** Con el atípico, min-max pone C en 1.0 y aplasta a A y D casi en 0, así que la suma pasa a depender casi solo
del coseno de C y de BM25. RRF no cambia en absoluto, porque los **puestos** son los mismos: ignora cuánto separa un
puntaje de otro. Esa es su robustez.

**6.** (a) Con más peso a BM25 (por ejemplo `pesos = [1.5, 1.0]` si la primera lista es la de BM25), Andrés pasa
primero. (b) Al añadir "auditor", BM25 y la semántica coinciden en Andrés y el empate desaparece. La (a) es una
decisión de diseño válida si tu evaluación dice que BM25 es más fiable en tus consultas de códigos; la (b) no es una
solución, porque no controlas lo que escribe el usuario. Lo honesto es (a) respaldado por la evaluación, o un
re-ranker (§11).

**7.** Con `candidatos = 1`, cada búsqueda aporta un solo documento a la fusión. Si el relevante es el 2º de una
lista, ni siquiera llega a fusionarse, y el recall de la híbrida cae por debajo del de la semántica sola. La fusión
solo puede reordenar lo que recibe: el *prefetch* debe traer bastantes candidatos (20-100 es lo habitual).

**8.** No hay una única respuesta. El entregable es la tabla y tu lectura. Si la híbrida no compensa en tu colección,
las causas típicas son: colección demasiado pequeña (el top-k ya cubre casi todo), consultas casi todas de un mismo
tipo, o un tokenizador débil que hace de BM25 un mal compañero de fusión.

</details>
