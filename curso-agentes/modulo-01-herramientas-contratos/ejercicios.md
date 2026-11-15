# Módulo 1 · Ejercicios

---

### Ejercicio 1 — Normalización silenciosa vs. rechazo con sugerencia
En `ejecutar_herramienta_ats` (`comun/ag_comun.py`), cuando el modelo envía `"Evaluacion de LLM"`, la herramienta devuelve `{"ok": False, "sugerencias": ...}` y el modelo gasta 1 paso extra en reintentar. ¿Cuándo conviene **normalizar silenciosamente** la entrada dentro de la herramienta (sin devolver error) y cuándo conviene **rechazar y pedir confirmación**?

<details>
<summary>Ver solución</summary>

- **Normalizar silenciosamente** cuando la transformación es **unívoca y sin ambigüedad semántica**: quitar espacios al inicio/final (`.strip()`), pasar códigos de vacante a mayúsculas (`"vac-101" -> "VAC-101"`) o ignorar tildes cuando solo existe una coincidencia exacta en el catálogo (`"Evaluacion de LLMs" -> "Evaluación de LLMs"`). Así ahorras 1 turno completo de latencia y tokens.
- **Rechazar con sugerencias** cuando hay **ambigüedad real** (por ejemplo, el modelo pide `"SQL Server"` y en el catálogo existen tanto `"SQL"` como `"Postgres"`) o en herramientas con efectos secundarios donde adivinar un parámetro podría modificar el registro equivocado.
</details>

---

### Ejercicio 2 — Añadir filtro `modalidad` con validación Poka-Yoke
Modifica una copia local de `buscar_candidatos` para que acepte un parámetro opcional `solo_remoto: bool = False`. Si es `True`, debe filtrar únicamente candidatos con `c["remoto"] == True`. Comprueba cuántos candidatos devuelve para `["Python", "SQL", "RAG", "Evaluación de LLMs"]` con `max_aspiracion_usd=8000` cuando `solo_remoto=True` frente a `False`.

<details>
<summary>Ver solución</summary>

Con `max_aspiracion_usd=8000` y `solo_remoto=False` entran 5 candidatos (`CAND-01`, `CAND-03`, `CAND-04`, `CAND-06`, `CAND-07`). Al activar `solo_remoto=True`, queda excluida `CAND-06` (*Daniela Pardo*, que tiene `remoto: False`), devolviendo 4 candidatos.
</details>
