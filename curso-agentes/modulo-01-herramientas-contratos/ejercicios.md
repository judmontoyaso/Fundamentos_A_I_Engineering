# Módulo 1 · Ejercicios

---

### Ejercicio 1. Normalización silenciosa vs. rechazo con sugerencia
En `ejecutar_herramienta_ats` (`comun/ag_comun.py`), cuando el modelo envía `"Evaluacion de LLM"`, la herramienta devuelve `{"ok": False, "sugerencias": ...}` y el modelo gasta 1 paso extra en reintentar. ¿Cuándo conviene **normalizar silenciosamente** la entrada dentro de la herramienta (sin devolver error) y cuándo conviene **rechazar y pedir confirmación**?

<details>
<summary>Ver solución</summary>

- **Normalizar silenciosamente** cuando la transformación es **unívoca y sin ambigüedad semántica**: quitar espacios al inicio/final (`.strip()`), pasar códigos de vacante a mayúsculas (`"vac-101" -> "VAC-101"`) o ignorar tildes cuando solo existe una coincidencia exacta en el catálogo (`"Evaluacion de LLMs" -> "Evaluación de LLMs"`). Así ahorras 1 turno completo de latencia y tokens.
- **Rechazar con sugerencias** cuando hay **ambigüedad real** (por ejemplo, el modelo pide `"SQL Server"` y en el catálogo existen tanto `"SQL"` como `"Postgres"`) o en herramientas con efectos secundarios donde adivinar un parámetro podría modificar el registro equivocado.
</details>

---

### Ejercicio 2. Añadir filtro `modalidad` con validación Poka-Yoke
Modifica una copia local de `buscar_candidatos` para que acepte un parámetro opcional `solo_remoto: bool = False`. Si es `True`, debe filtrar únicamente candidatos con `c["remoto"] == True`. Comprueba cuántos candidatos devuelve para `["Python", "SQL", "RAG", "Evaluación de LLMs"]` con `max_aspiracion_usd=8000` cuando `solo_remoto=True` frente a `False`.

<details>
<summary>Ver solución</summary>

Con `max_aspiracion_usd=8000` y `solo_remoto=False` entran 5 candidatos (`CAND-01`, `CAND-03`, `CAND-04`, `CAND-06`, `CAND-07`). Al activar `solo_remoto=True`, queda excluida `CAND-06` (*Daniela Pardo*, que tiene `remoto: False`), devolviendo 4 candidatos.
</details>

---

### Ejercicio 3. Modo estricto del proveedor
Activa el modo estricto de OpenAI en los esquemas (`"strict": true` dentro de `function`). ¿Qué tienes que cambiar en
los esquemas del ATS para que la API los acepte? ¿Qué validaciones sigues necesitando en tu código?

<details>
<summary>Ver solución</summary>

En modo estricto todas las propiedades deben estar en `required` y cada objeto debe tener `additionalProperties:
false`; los parámetros opcionales se expresan como unión con `null`. Algunas palabras clave de JSON Schema no están
soportadas en ese modo; revisa la documentación vigente. Aunque los argumentos lleguen con la forma correcta, sigues
validando en código lo que el schema no sabe: que la habilidad esté en el catálogo, que el candidato exista, que la
vacante esté abierta.
</details>

---

### Ejercicio 4. Paginación en la búsqueda
`buscar_candidatos` devuelve todos los resultados. Con 300 candidatos sería un volcado. Añade `limite` (por defecto 5,
máximo 15) y `pagina`, y devuelve `total`, `mostrando` y `hay_mas`. ¿Cómo debería decidir el modelo si pide otra
página o afina los filtros?

<details>
<summary>Ver solución</summary>

Ordena los resultados de forma estable (por ejemplo, por cobertura de requisitos y luego aspiración) y corta con
`limite` y `pagina`. En la descripción de la herramienta di: "si `total` es mayor que 15, afina los filtros en lugar de
paginar". Así la observación nunca pasa de un tamaño conocido y el modelo recibe la señal para refinar. Ojo con la
interacción con el módulo 2: la guarda que exige verificar "a todos los encontrados" debe referirse a los mostrados, o
a todos los de la búsqueda si se paginan todos.
</details>
