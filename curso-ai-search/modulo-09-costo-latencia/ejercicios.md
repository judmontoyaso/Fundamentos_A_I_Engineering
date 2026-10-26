# Módulo 9 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). El laboratorio 02 no llama al LLM: puedes cambiar
sus parámetros y correrlo cuantas veces quieras.

---

### Ejercicio 1 — ¿Cuánto ahorra una caché de parseos?
Supón 1.000 pedidos: la mitad son las 41 consultas del curso, repartidas al azar, y la otra mitad son consultas que no
se repiten nunca. ¿Qué fracción de los pedidos sale de la caché? ¿Cuánto baja el costo del parser? ¿Qué cambia si
normalizas la consulta (minúsculas, sin tildes, espacios) antes de buscarla en la caché?

### Ejercicio 2 — Calibrar el presupuesto
Con el modelo principal, prueba presupuestos de 3, 4, 5.6 (su p95) y 8 s en la estrategia de respaldo. ¿Dónde deja de
mejorar el nDCG, y por qué?

### Ejercicio 3 — La política del reranker, en producción
La política del §4 usa la salida del parser. ¿Qué pasa con ella si el parser falla y el sistema cae al respaldo? ¿Y
si el parser se equivoca y no detecta una exclusión?

### Ejercicio 4 — Probar antes de servir
51 de los 84 errores fueron "falta la clave". Escribe una comprobación de arranque para el backend de la app: qué
verifica, qué hace si falla y cuánto cuesta correrla.

### Ejercicio 5 — Tu factura
Define en `.env` los precios de tu cuenta para los dos modelos y corre el laboratorio 01. ¿Cuánto cuestan 1.000
consultas con cada configuración? ¿Cuánto cuesta la política del §4 comparada con el reranker siempre?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** De los 500 pedidos de consultas frecuentes, solo la primera aparición de cada una falla (41); los otros 459 salen
de la caché. Los 500 únicos fallan siempre. Tasa de aciertos: 459 / 1.000 ≈ **46%**, y el costo del parser baja en la
misma proporción. La cifra la decide el tráfico, no la caché: con 90% de consultas únicas, la caché casi no sirve.
Normalizar convierte en aciertos las variantes triviales ("Kafka" y "kafka "), y es gratis. Normalizar más (sinónimos,
orden de palabras) ya es otro parser, y puede juntar consultas que no significan lo mismo.

**2.**

| Presupuesto | nDCG@10 | p95 |
|---|---|---|
| 3 s | 0.728 | 3.0 s |
| 4 s | 0.803 | 4.0 s |
| 5.6 s | 0.832 | 5.0 s |
| 8 s | 0.832 | 5.0 s |

Deja de mejorar en 5 s porque ahí manda el **tiempo límite por intento** (5 s): un presupuesto mayor que el límite no
hace nada. Entre 3 y 5 s, cada segundo de espera compra calidad; la decisión es cuánto vale un segundo para el
reclutador. Con el modelo barato no hay decisión: cabe entero en 3 s.

**3.** Si el parser falla, no hay salida del parser y tampoco política: el respaldo es la híbrida sola, y llamar al
reranker sería pagar 20 llamadas a un proveedor que acaba de fallar. Lo sensato es que el respaldo no tenga LLM. Si el
parser no detecta la exclusión, el reranker no se llama y esa consulta queda con la calidad de los filtros suaves: la
política hereda los errores del parser. Se vigila midiendo la política entera en el eval (como en el §4), no cada
pieza por separado.

**4.** Al arrancar: que existan las variables necesarias (sin imprimir sus valores), y **una llamada mínima** con cada
modelo configurado (un esquema de un campo, unos pocos tokens) que confirme credenciales, que el modelo existe y que
la red llega. Si falla, el servicio no se declara listo (el *health check* responde error) y el despliegue no recibe
tráfico. Cuesta dos llamadas mínimas por arranque. Habría atrapado los 51 errores de credenciales y los 30 del modelo
retirado antes de que un pedido real los viera.

**5.** Depende de tu cuenta. Con los tokens de la tabla del §2 la cuenta es directa:
`costo por consulta = tokens_entrada × precio_entrada + tokens_salida × precio_salida` (los de razonamiento ya vienen
dentro de los de salida y se cobran como tales). La política del §4 cuesta el parser más el 22% del reranker: unos
1.800 tokens de entrada y 530 de salida del modelo barato por consulta, contra 5.000 y 1.950 del barato **más** el
parser con el principal en "principal + rerank siempre". Unas 3 a 4 veces menos tokens, ninguno del modelo caro, y la
misma calidad.

</details>
