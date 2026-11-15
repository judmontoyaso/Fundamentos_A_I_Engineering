# Ejercicios · Módulo 1

## Ejercicio 1: Refactorizar una herramienta frágil

Tienes esta herramienta expuesta al agente:

```python
def query_ats(table: str, col: str, val: str, limit: int = 1000) -> list[dict]:
    ...
```

¿Qué tres problemas graves tiene para un agente y cómo la rediseñarías con Pydantic?

<details>
<summary>Solución comentada</summary>

1. **Problemas**:
   - Expone nombres físicos de tablas y columnas (`table`, `col`) que el modelo inventará con frecuencia.
   - `limit=1000` puede volcar cientos de kilobytes en la ventana de contexto de una sola llamada.
   - No expresa la intención del negocio ni restringe los filtros válidos.
2. **Rediseño poka-yoke**:
   Crear `buscar_candidatos_ats(habilidades: list[str], anos_minimos: int = 0, max_aspiracion_usd: int | None = None, top_k: int = Field(default=5, le=15))` que devuelve únicamente campos legibles y un resumen de cuántos candidatos adicionales quedaron fuera.

</details>

---

## Ejercicio 2: Mensajes de error que ahorran pasos

Cuando el agente busca una habilidad mal escrita (`"Postgressql"` en lugar de `"Postgres"`), la búsqueda exacta devuelve `[]`. Modifica la respuesta de la herramienta para que sugiera las habilidades canónicas más cercanas del catálogo.

<details>
<summary>Solución comentada</summary>

Usando `difflib.get_close_matches(hab, CATALOGO_HABILIDADES, n=3, cutoff=0.6)`, cuando una habilidad solicitada no existe en el catálogo devolvemos `"advertencia": "La habilidad 'Postgressql' no figura en el catálogo. ¿Quisiste decir ['Postgres']?"`. Así el agente corrige su llamada en el siguiente turno con certeza.

</details>
