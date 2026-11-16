# Módulo 2 · Ejercicios

---

### Ejercicio 1. Bloquear `agendar_entrevista` para candidatos no verificados
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

### Ejercicio 2. ¿Qué debe formar parte de la clave de idempotencia?
Si dos ejecuciones distintas (una en enero y otra en junio para otro proceso de selección) llaman a `consultar_ficha_candidato("CAND-01")`, ¿deberían compartir la misma clave de idempotencia? ¿Por qué `EjecutorConCheckpoint` guarda `cache_idempotencia` **dentro** del checkpoint de la ejecución actual?

<details>
<summary>Ver solución</summary>

Porque la idempotencia protege contra **reintentos involuntarios dentro de una misma operación o flujo** (`ejecucion_id`), no es una caché perpetua. Si en junio el candidato actualizó su aspiración salarial o cumplió los 90 días de enfriamiento, una ejecución nueva debe leer el estado fresco del ATS. Al ligar `cache_idempotencia` al estado de la corrida (`m2_checkpoint.json`), garantizas que si esa corrida se reanuda tras una caída no duplique llamadas, pero una corrida nueva verá los datos actualizados.
</details>

---

### Ejercicio 3. Caída entre el efecto y el guardado
En `02_checkpoints_e_idempotencia.py`, el checkpoint se guarda al final de cada paso. Simula una caída justo después
de ejecutar `agendar_entrevista` y antes de guardar. ¿Qué pasa al reanudar? ¿Cómo lo evitarías?

<details>
<summary>Ver solución</summary>

La caché de idempotencia estaba en memoria y no llegó al disco, así que al reanudar el modelo vuelve a pedir la
entrevista y se crea otra. Dos soluciones complementarias: guardar en el checkpoint la intención **antes** de ejecutar
el efecto (estado `en_curso` con su clave) y, al reanudar, consultar al sistema externo si esa clave ya existe; o que el
sistema externo acepte la clave de idempotencia y descarte duplicados. Esta es la razón por la que las pasarelas de
pago exigen una clave de idempotencia al crear cobros.
</details>

---

### Ejercicio 4. Devolver el bloqueo al modelo en lugar de corregirlo
Cambia la guarda de `01_maquina_de_estados.py` para que, al bloquear la entrega, devuelva el error al modelo en vez de
verificar en código. Corre con `p_descuido=1.0` y con `p_descuido=0.3`. Compara pasos y resultado.

<details>
<summary>Ver solución</summary>

Con el modelo simulado, el bloqueo hace que en el siguiente turno verifique a los pendientes, porque su política
mira qué candidatos no tienen veredicto. Cuesta unos pasos más que corregir en código, y con un modelo real depende de
que entienda el mensaje. Corregir en código es preferible cuando lo que falta es mecánico; devolver el error es
necesario cuando corregir requiere criterio (por ejemplo, elegir qué filtro relajar).
</details>
