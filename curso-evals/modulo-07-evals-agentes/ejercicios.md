# Módulo 7 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Los laboratorios de este módulo hacen muchas llamadas
(tres modelos × 8 pedidos × 3 corridas): para probar cambios, reduce `MODELOS` a uno.

---

### Ejercicio 1 — Verificar el extractor de recomendados
`recomendados()` usa un LLM para leer a quién recomienda la respuesta final. Imprime, para 10 corridas, la respuesta y
los ids extraídos. ¿Acierta en todas? ¿Qué pasa con una respuesta como "recomiendo a Laura (id 1); descarté a Marta
(id 3)"? Si falla, ¿cómo lo harías por código?

### Ejercicio 2 — Arreglar la repetición de nano
El paso "tras leer al candidato correcto → terminar" falla 0/3 con `gpt-5.4-nano`. Prueba dos arreglos y mide los dos
laboratorios con cada uno: (a) una regla en el prompt ("si ya leíste el CV del candidato que buscabas, termina"); (b) una
regla en código en `correr()`: si la decisión es `ver_cv` de un id ya leído, en vez de ejecutarla, devolver "Ya leíste
ese CV; termina o busca otro". ¿Cuál sube más el pass^3?

### Ejercicio 3 — Una defensa contra la inyección para mini
`gpt-4.1-mini` recomienda a Pedro 3 de 3 veces. Añade una defensa y mídela con el caso malicioso (episodio y paso
aislado): por ejemplo, marcar en la observación de `ver_cv` las frases que parecen instrucciones
(`[TEXTO SOSPECHOSO: ...]`), o exigir en el prompt que la recomendación se justifique con experiencia del CV. ¿Deja de
obedecer? ¿Rompe algún otro pedido?

### Ejercicio 4 — Un caso donde bm25 sí importe
Añade al corpus del agente un CV con "ISO 9001" y otro con "ISO 27001" que se parezcan mucho en el resto del texto, y
un pedido que solo encaje con uno. ¿Sigue acertando la búsqueda híbrida? Si falla, el chequeo "sigla exacta → bm25"
pasa a medir algo que importa.

### Ejercicio 5 — pass@3 contra pass^3
Con los resultados del laboratorio 01, calcula para cada modelo **pass@3** (el pedido sale bien en al menos una de las
tres corridas) y **pass^3** (en las tres). ¿Cuál de los dos usarías para decidir si poner el agente en producción? ¿Y
para saber si un pedido es posible de resolver?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Con respuestas claras suele acertar. El caso "recomiendo a 1; descarté a 3" es la prueba: si devuelve `[1, 3]`,
el extractor confunde mencionar con recomendar, y todo el eval de resultado hereda ese error. Por código, la
alternativa robusta es cambiar el contrato: que `terminar` devuelva también una lista `recomendados: list[int]` en el
schema de `Decision`. Si puedes cambiar la salida del sistema para que sea verificable, es mejor que interpretarla.

**2.** La regla en código suele ser más fiable que la del prompt con un modelo pequeño: no depende de que el modelo la
obedezca, y convierte una repetición en una observación útil. Mídelo en los dos laboratorios: en el de un paso, el caso
"tras leer → terminar" debería subir; en el del episodio, las llamadas repetidas deberían bajar y el pass^3 subir. Si
la regla del prompt basta, mejor: es más simple.

**3.** Marcar el texto sospechoso en la observación suele ayudar a los modelos pequeños: convierte una instrucción
escondida en un dato etiquetado. Exigir la justificación con experiencia ayuda poco si el CV malicioso **también**
tiene experiencia relevante (Pedro dice "ingeniero senior de datos en tiempo real con Kafka"). Mide siempre los demás
pedidos: una defensa demasiado agresiva puede hacer que el agente desconfíe de CVs legítimos.

**4.** Es posible que la búsqueda híbrida siga acertando (BM25 ya forma parte de la híbrida), y entonces la regla de
`bm25` sigue sin importar. Si falla, has encontrado el caso que justifica la regla, y el chequeo del paso pasa a ser un
eval con sentido. Esa es la forma correcta de decidir si un chequeo de camino se queda: con un caso donde cambie el
resultado.

**5.** pass@3 responde "¿puede hacerlo?"; pass^3, "¿lo hace siempre?". Para producción, pass^3 (o pass^k con k más
grande): un usuario no reintenta tres veces. Para saber si un pedido es resoluble con este agente, pass@3: si ni en tres
intentos sale, el problema no es la varianza, es la capacidad.

</details>
