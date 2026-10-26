# Módulo 1 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Se hacen en el **Laboratorio** de la app; para
cambiar el modelo candidato, pon `MODELO_BARATO` en `app/backend/.env` y reinicia la API, o asigna
`ev.MODELO_BARATO = "..."` en la celda libre.

---

### Ejercicio 1 — Tus cinco casos
Añade a `CVS` de [`comun/ev_datos.py`](../comun/ev_datos.py) cinco CVs que creas que van a fallar (por ejemplo:
experiencia en "año y medio", dos trabajos simultáneos a tiempo parcial, un nombre con partícula como "de la Torre",
un CV en portugués, skills escritas como "ML/IA"). **Escribe lo esperado antes de ejecutar** y aplica las reglas del
principio del archivo. Corre `01` con el modelo barato. ¿Cuántos fallan? ¿Alguno te obligó a inventar una regla nueva?

### Ejercicio 2 — Un chequeo más estricto
Cambia en `comparar_ficha()` el chequeo de skills para exigir que la lista extraída sea **igual** a la esperada
(mismo conjunto). Corre `01` con `gpt-6-luna`. ¿Cuántos "fallos" aparecen? ¿Cuántos son errores reales del sistema?

### Ejercicio 3 — ¿Se confirma la rotura?
Con `gpt-5.4-nano`, sube `REPETICIONES` a 4 en `02`. ¿El #18 sigue "roto" o pasa a "inestable"? ¿Qué pasa con el #21?
Antes de ejecutar, escribe qué esperas.

### Ejercicio 4 — Decírselo de otra forma
`gpt-4o-mini` ignoró "suma todo trabajo, aunque no sea del área" en el #30. Crea un prompt `v3` sin esa frase y, en
su lugar, cambia la **descripción del campo** en `FichaCV`:
`Field(description="años de experiencia laboral total, sumando TODOS los trabajos, también los de otras áreas")`.
¿Arregla el #30? ¿Rompe algo?

### Ejercicio 5 — ¿Cuánto cuesta cada opción?
Las trazas guardan los tokens de cada llamada. Escribe una celda que, para la última corrida de cada modelo, sume
tokens de entrada, de salida y de razonamiento (`ev.tz.spans(trace_id)`, atributos `tokens_*`). Con los precios de tu
cuenta, calcula el costo de 100.000 extracciones con `gpt-6-luna` y con el candidato. ¿Qué parte del costo del modelo
grande es razonamiento?

### Ejercicio 6 — Un v3 que no rompa a nano
Escribe un prompt `v3` que arregle el #19 y el #23 en `gpt-5.4-nano` **sin** romper el #18. Pista: el #18 iba bien con
`v1`. ¿Qué parte de `v2` lo empeoró? Pruébalo con `02` (cambia las versiones que compara).

---

<details>
<summary><b>Soluciones</b></summary>

**1.** No hay una única respuesta: el entregable son tus casos, lo esperado y lo obtenido. Lo más valioso suele ser el
caso que te obligó a decidir una regla nueva ("¿dos trabajos simultáneos suman?"). Escríbela al principio de
`ev_datos.py` y revisa si alguna etiqueta anterior la contradice. Así crece un set de evaluación: cada caso nuevo
puede afinar la especificación.

**2.** Con igualdad exacta aparecen muchos "fallos" que no lo son: el modelo extrae skills de más ("auditorías
internas", "pentesting") o con otra forma ("python 3.12"). El informe se llena de ruido, y un informe con ruido se deja
de leer. Por eso el chequeo de skills es "cada esperada está dentro de alguna extraída". Si te importara no extraer
de más (por ejemplo, para no inventar skills), eso merece **su propio** chequeo, con su propio nombre.

**3.** Lo más probable es que el #18 pase a "inestable": al escribir el curso, midiendo solo ese caso, `v2` acertó 3
de cada 10 llamadas y `v1`, 9 de 10. Con cuatro pasadas casi seguro sale bien alguna vez. Sigue siendo mucho peor que
`v1`, pero la etiqueta "roto" (siempre mal) ya no le corresponde. La lección: las clases del laboratorio son una
primera lectura; para un caso que importa, la medida buena es **la tasa de acierto con muchas repeticiones**, y
compararla entre versiones.

**4.** Mover la regla a la descripción del campo suele ayudar, porque la descripción viaja pegada al campo en el
esquema (AI Engineering, Módulo 1: "el schema es el prompt"). Puede no bastar con un modelo pequeño, y puede cambiar
otros casos: mira la clasificación completa, no solo el #30.

**5.** Esqueleto:
```python
filas = [s for s in ev.tz.spans() if s["nombre"].startswith("eval extractor")]
ultima = filas[-1]["trace_id"]
llm = [s["atributos"] for s in ev.tz.spans(ultima) if s["atributos"].get("tipo") == "llm"]
print(sum(a.get("tokens_entrada", 0) for a in llm), sum(a.get("tokens_salida", 0) for a in llm),
      sum(a.get("tokens_razonamiento", 0) for a in llm))
```
En el Módulo 7 de AI Engineering, el razonamiento era cerca de un tercio de la salida de `gpt-6-luna`. Ese costo no
aparece en ninguna respuesta, y en tareas simples como esta puede ser el grueso de lo que pagas.

**6.** Una hipótesis razonable: la línea de reglas de conteo, larga y con varias condiciones, es la que desestabiliza
al modelo pequeño en el #18. Un `v3` con solo la fecha de hoy y la regla de skills puede arreglar el #19 y el #23 sin
tocar el #18. Compruébalo con `02` comparando `v1` contra `v3`. Si funciona, aprendiste algo general: **cada
instrucción tiene un costo**, y en modelos pequeños ese costo se nota antes.

</details>
