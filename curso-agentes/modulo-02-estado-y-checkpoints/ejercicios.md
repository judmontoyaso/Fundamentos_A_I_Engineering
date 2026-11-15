# Ejercicios · Módulo 2

## Ejercicio 1: Transiciones ilegales en una máquina de estados

¿Por qué es peligroso permitir que el modelo llame a `agendar_entrevista(candidato_id)` en cualquier momento del bucle, y cómo lo impide una máquina de estados?

<details>
<summary>Solución comentada</summary>

En un bucle libre con todas las herramientas visibles desde el turno 1, el modelo puede saltarse la verificación de enfriamiento o de presupuesto y llamar directamente a `agendar_entrevista`. En una máquina de estados explícita, cada etapa habilita únicamente el subconjunto de herramientas permitidas en ese nodo, y la transición a `listo_para_revision` exige que `verificaciones_ats[candidato_id]["elegible"] == True`.

</details>

---

## Ejercicio 2: Reanudación tras fallo de red

Simula un fallo en la tercera llamada de un flujo de 4 pasos y verifica que al reanudar desde el checkpoint:
1. No se vuelven a ejecutar los pasos 1 y 2.
2. Ninguna nota en el ATS queda duplicada.

<details>
<summary>Solución comentada</summary>

Revisa `code/02_checkpoints_e_idempotencia.py`: el almacén de checkpoints persiste `etapa` y `efectos_ejecutados` después de cada nodo. En el segundo intento, el grafo salta directamente a la etapa pendiente y cualquier mutación ya registrada por su clave de idempotencia devuelve su recibo previo.

</details>
