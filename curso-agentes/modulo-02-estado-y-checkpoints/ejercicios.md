# Módulo 2 · Ejercicios

---

### Ejercicio 1 — Bloquear `agendar_entrevista` para candidatos no verificados
En `code/01_maquina_de_estados.py`, `validar_transicion` protege `entregar_terna`. Extiende `validar_transicion` para que también bloquee cualquier llamada a `agendar_entrevista(vacante_id, candidato_id, fecha)` si `candidato_id` no figura en `self.verificados` con valor `True`.

<details>
<summary>Ver solución</summary>

```python
if herramienta == "agendar_entrevista":
    cid = str(args.get("candidato_id", ""))
    if cid not in self.verificados:
        return f"Transición bloqueada: debes verificar_elegibilidad de {cid} antes de agendar."
    if not self.verificados[cid]:
        return f"Transición bloqueada: {cid} no es elegible para la vacante; no se puede agendar entrevista."
```
</details>

---

### Ejercicio 2 — ¿Qué debe formar parte de la clave de idempotencia?
Si dos ejecuciones distintas (una en enero y otra en junio para otro proceso de selección) llaman a `consultar_ficha_candidato("CAND-01")`, ¿deberían compartir la misma clave de idempotencia? ¿Por qué `EjecutorConCheckpoint` guarda `cache_idempotencia` **dentro** del checkpoint de la ejecución actual?

<details>
<summary>Ver solución</summary>

Porque la idempotencia protege contra **reintentos involuntarios dentro de una misma operación o flujo** (`ejecucion_id`), no es una caché perpetua. Si en junio el candidato actualizó su aspiración salarial o cumplió los 90 días de enfriamiento, una ejecución nueva debe leer el estado fresco del ATS. Al ligar `cache_idempotencia` al estado de la corrida (`m2_checkpoint.json`), garantizas que si esa corrida se reanuda tras una caída no duplique llamadas, pero una corrida nueva verá los datos actualizados.
</details>
