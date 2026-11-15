# Módulo 3 · Ejercicios

---

### Ejercicio 1 — ¿Qué pasa si podas también `verificar_elegibilidad`?
En `podar_observaciones_antiguas` (`code/01_podar_observaciones.py`), cuando se poda una respuesta antigua de `consultar_ficha_candidato` se conserva `{"id": c["id"], "nombre": c["nombre"], "resumen_podado": True}`, pero las respuestas de `verificar_elegibilidad` mantienen su campo `"elegible": True/False`. ¿Qué ocurriría en el último paso (`entregar_terna`) si la poda borrara el booleano `"elegible"` de las verificaciones antiguas?

<details>
<summary>Ver solución</summary>

Al llegar al paso 11 (`entregar_terna`), el modelo necesita saber cuáles de los 4 candidatos verificados en los pasos 4, 6, 8 y 10 resultaron `elegible: True`. Si borras ese veredicto de las observaciones antiguas y no lo mantienes en un resumen de estado (*scratchpad*), el modelo perderá la evidencia de los primeros candidatos o volverá a llamar a `verificar_elegibilidad` en bucle. Regla de oro: **poda la evidencia cruda pesada (el texto del CV), pero conserva siempre el veredicto compacto (`elegible: true/false`)**.
</details>

---

### Ejercicio 2 — Memoria episódica con fecha de caducidad y autor
Extiende `MemoriaEpisodica.registrar_aprendizaje` en `code/02_memoria_episodica.py` para que guarde un campo `vigente: bool = True` y añade un método `revocar_aprendizajes(vacante_id)` que desactive las reglas cuando cambie el perfil de la vacante.

<details>
<summary>Ver solución</summary>

```python
def listar(self, vacante_id: str) -> list[dict]:
    if not self.ruta.exists():
        return []
    todas = json.loads(self.ruta.read_text(encoding="utf-8"))
    return [r for r in todas if r.get("vacante_id") == vacante_id and r.get("vigente", True)]
```
</details>
