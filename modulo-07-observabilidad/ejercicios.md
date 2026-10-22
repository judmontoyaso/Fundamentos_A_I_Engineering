# Módulo 7 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Se hacen en el **Laboratorio** de la app; ejecuta
primero `00_trazador.py`. Las trazas se acumulan en `app/backend/data/trazas.db`: `tz.borrar_trazas()` las vacía.

---

### Ejercicio 1 — Traza tu propio flujo
En la celda libre, envuelve el agente del Módulo 5 en una traza: abre `tz.nueva_traza("agente")` y, dentro, un
`tz.span(...)` por cada paso del bucle. Imprime el árbol con `tz.arbol(...)`. ¿Qué paso es el más lento? ¿Cuántos
tokens de entrada reenvía el último paso en comparación con el primero?

### Ejercicio 2 — Enmascarado
Llama a `tz.enmascarar()` con un CV que tenga un correo, un teléfono colombiano con espacios (`+57 300 123 4567`), uno
con guiones (`300-123-4567`) y un número que **no** es teléfono (`ISO 27001`, `2016-2020`). ¿Cuál enmascara de más o
de menos? Ajusta las expresiones regulares y vuelve a probar.

### Ejercicio 3 — Precios y proyección
Busca los precios actuales de tu modelo en la página de tu proveedor y ponlos en `app/backend/.env`
(`PRECIO_ENTRADA_USD_1M`, `PRECIO_SALIDA_USD_1M`, `PRECIO_CACHE_USD_1M`). Reinicia la API, ejecuta `01` y `02`.
¿Cuánto cuestan 1000 pedidos? ¿Qué parte de ese costo es razonamiento?

### Ejercicio 4 — Casos más difíciles
El dataset de `03` salió perfecto. Añade 5 casos que creas que van a fallar (por ejemplo: dos correos, años de
experiencia contradictorios, experiencia en meses, un CV desordenado en una sola línea, un nombre en mayúsculas).
Define lo esperado **antes** de ejecutar. ¿Cuántos fallan? ¿Algún fallo es en realidad una etiqueta discutible?

### Ejercicio 5 — Comparar dos prompts de extracción
`evaluar_extraccion()` acepta otro prompt. Prueba uno más corto ("Extrae los datos.") con
`evaluar_extraccion("Extrae los datos.", "extraccion-v0")` y compara la exactitud por campo con la del prompt v1.
¿Qué campo se resiente primero?

### Ejercicio 6 — Calibra tú el juez
Añade a `CASOS` de `04` seis casos tuyos (tres fieles y tres no fieles, con al menos uno sutil). Etiquétalos **antes**
de ejecutar el juez. ¿Coincide contigo? En cada desacuerdo, lee la razón del juez y decide: ¿estaba mal el juez o tu
etiqueta?

### Ejercicio 7 — Más poder en la regresión
En `05`, sube `EJECUCIONES` a 8. ¿Aparece algún fallo de la versión v1? Calcula cuántas ejecuciones harían falta para
que la probabilidad de no ver ningún fallo de un problema que ocurre 1 de cada 3 veces sea menor que 1 %.

### Ejercicio 8 — Proyecto
Instrumenta el grafo de selección del Módulo 6 (`04_humano_en_el_bucle.py`): un span por nodo, tokens en cada llamada
al LLM y el `thread_id` del grafo como atributo de la traza. Genera el informe de `02` sobre 5 vacantes y escribe tres
conclusiones accionables (qué optimizarías primero y por qué, con números).

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Esqueleto:
```python
import importlib; a = importlib.import_module("05_agente_desde_cero")
with tz.nueva_traza("agente") as raiz:
    historial = [{"role": "user", "content": "Pedido: alguien senior para datos en tiempo real"}]
    for paso in range(a.MAX_PASOS):
        with tz.span(f"paso {paso + 1}") as s:
            d = tz.llm_trazado(a.Decision, a.SYSTEM, str(historial), nombre="decidir")
            s.atributos["herramienta"] = d.herramienta
            if d.herramienta == "terminar":
                break
            obs = a.ejecutar(d)
            historial += [d.model_dump_json(), obs]
print(tz.arbol(raiz.trace_id))
```
Lo típico es que los pasos de `decidir` dominen el tiempo, y que los tokens de entrada crezcan paso a paso porque
cada uno reenvía el historial completo (manual §4).

**2.** Medido con el trazador tal como viene: enmascara bien `laura@mail.com`, `+57 300 123 4567` y `300-123-4567`,
y deja intacto `ISO 27001`. Pero enmascara **de más** `2016-2020` (lo toma por un teléfono: pierdes un dato útil para
depurar) y **de menos** un fijo de 7 dígitos como `3001234` (se filtra un dato personal). No hay una expresión
perfecta: decide qué error prefieres. En trazas, enmascarar de más suele ser aceptable; de menos, no. Una mejora:
exigir al menos 7 dígitos en total y excluir el patrón `AAAA-AAAA` de años.

**3.** El resultado depende de tus precios. Para la parte de razonamiento: multiplica los tokens de razonamiento por el
precio de salida. Con el 50 % de la salida en razonamiento que midió el laboratorio, una parte importante del costo
de salida es "pensar", y no aparece en ninguna respuesta.

**4.** Lo habitual es que fallen experiencia en meses (¿18 meses son 1 o 2 años?) y años contradictorios. Y que al
menos un "fallo" sea una etiqueta discutible: si dudaste al escribir lo esperado, el modelo también duda. Esos casos
se aclaran en el schema (por ejemplo, "redondea hacia abajo") o se quitan del dataset.

**5.** Con un prompt mínimo suele resentirse primero `correo` (inventa o normaliza correos ausentes) o `anios` (los
casos de inyección y de años en palabras). Precisamente lo que el prompt v1 pedía explícitamente ("No inventes", CV
delimitado).

**6.** No hay una única solución: el entregable es la tabla de acuerdo y tu decisión en cada desacuerdo. Si más de la
mitad de los desacuerdos resultan ser etiquetas tuyas mal puestas, el juez está mejor calibrado de lo que creías; si
el juez aprueba invenciones sutiles, endurece la rúbrica.

**7.** La probabilidad de no ver ningún fallo en `n` ejecuciones es (2/3)ⁿ. Para que sea menor que 1 %:
n > ln(0.01) / ln(2/3) ≈ 11.4, es decir, **12 ejecuciones**. Con 8, la probabilidad es ≈ 4 %.

**8.** Patrón: `with tz.span(nombre_del_nodo, thread_id=...)` dentro de cada función nodo, y `tz.llm_trazado` en lugar
de `c.llm`. Las conclusiones típicas: el arranque en frío de la búsqueda domina el primer pedido (precalentar el
índice al arrancar la API); la evaluación de candidatos es la mayor parte del costo (evaluar menos candidatos o usar
un modelo más barato para el primer filtro); el razonamiento es una fracción grande de la salida (probar un modelo
sin razonamiento para las tareas simples, y medir si la calidad se mantiene).

</details>
