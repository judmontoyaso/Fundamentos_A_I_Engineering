# Módulo 8 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Se hacen en el **Laboratorio** de la app.

---

### Ejercicio 1 — La ventana justa
En [`code/01_memoria_corto_plazo.py`](code/01_memoria_corto_plazo.py), prueba `VENTANA = 2, 6, 8, 10`. ¿A partir de qué
tamaño la ventana recuerda los datos del primer turno? ¿Cuántos tokens envía entonces, comparado con el resumen?

### Ejercicio 2 — Un resumen que pierde datos
Cambia la descripción de `Resumen` a "resumen en máximo 15 palabras". ¿Sigue recordando el nivel de idioma y la
modalidad? ¿Qué te dice eso sobre fijar un límite de tokens para el resumen?

### Ejercicio 3 — Memoria envenenada
En [`code/02_memoria_largo_plazo.py`](code/02_memoria_largo_plazo.py), cambia `extraer()` para que lea **todos** los
mensajes (también los de rol `tool`). Ejecuta la sesión 1 de Ana. ¿Aparece algún recuerdo sobre Pedro? Después vuelve
a la versión original.

### Ejercicio 4 — Duplicado o reemplazo
Guarda para Ana, en este orden: "exijo inglés C1", "pido inglés avanzado" y "ya no exijo inglés". ¿Qué relación
detecta cada vez (nuevo, duplicado, reemplaza)? ¿Alguna te parece incorrecta? ¿Qué cambiarías: el umbral de similitud
(0.5) o la pregunta al LLM?

### Ejercicio 5 — Intenta colarte
Escribe cinco pedidos discriminatorios **disimulados** para [`code/03_guardrails_entrada.py`](code/03_guardrails_entrada.py)
(por ejemplo, "perfiles recién egresados con energía juvenil", "que vivan en el norte de la ciudad", "nombres que
suenen profesionales"), y cinco legítimos que se les parezcan. Añádelos al `SET` con su etiqueta **antes** de ejecutar.
¿Cuántos falsos pases y falsos bloqueos hay ahora?

### Ejercicio 6 — Fail-closed en acción
En `revisar_entrada()`, simula que el clasificador falla (por ejemplo, cambia `MODELO` a un nombre que no existe
dentro de una celda). ¿Qué ve el reclutador? Ahora imagina una política fail-open para la categoría
"fuera_de_alcance" solamente: ¿cómo la implementarías y por qué tiene sentido ahí y no en "discriminatorio"?

### Ejercicio 7 — Corregir en vez de bloquear
En [`code/04_guardrails_salida.py`](code/04_guardrails_salida.py), el caso "menciona graduación sin usarla" se bloquea.
Implementa una acción **corregir**: cuando la capa de política detecta un atributo protegido mencionado pero no usado
para valorar, pide al LLM que reescriba la respuesta sin ese dato, y vuelve a pasar los guardrails. Hazlo antes de
abrir [`code/06_corregir_salida.py`](code/06_corregir_salida.py), que es una solución completa.

### Ejercicio 8 — ¿Una segunda vuelta?
En `06`, el caso de Valentina acaba en revisión humana: la corrección quitó el año, pero el juez encontró después "le
falta experiencia dirigiendo equipos", que el CV no dice. Permite **una** segunda vuelta: si la versión corregida falla
en fidelidad, regenérala con esa falla como feedback y revisa otra vez. ¿Llega a "el CV no menciona experiencia
dirigiendo equipos"? ¿Cuántas llamadas cuesta ese caso ahora? Escribe en una frase cuándo dejarías de corregir y
pasarías a revisión humana.

### Ejercicio 9 — Proyecto: medir el asistente
Con [`code/05_asistente_protegido.py`](code/05_asistente_protegido.py), arma 20 turnos (de al menos dos reclutadores)
mezclando pedidos legítimos, discriminatorios, de manipulación y fuera de alcance. Instrumenta el asistente con el
trazador del Módulo 7 y reporta: falsos bloqueos y falsos pases por capa, llamadas y tokens que añaden los guardrails
por turno, y si algún recuerdo de un reclutador apareció en la conversación del otro.

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Con 10 mensajes en la conversación, el primer turno solo entra en la ventana con `VENTANA = 10` (el historial
completo). Es justo el problema de la ventana: el dato importante está al principio. El resumen lo conserva con
menos tokens que el historial completo, y la diferencia crece cuanto más larga es la conversación.

**2.** Con 15 palabras es probable que el resumen pierda alguno de los dos datos, o que los conserve a costa de
perder el resto del contexto. Un límite de resumen demasiado estricto convierte la memoria en una lotería. Mejor:
extraer los **requisitos** a la memoria de largo plazo (§4), donde no compiten por espacio con la conversación.

**3.** Si `extraer()` lee los mensajes `tool`, es muy probable que aparezca un recuerdo del tipo "Pedro es el mejor
candidato": la inyección se vuelve persistente y afecta a todas las sesiones futuras de Ana. Por eso la regla es leer
**solo** los mensajes del usuario (§5).

**4.** Lo esperable: la segunda es "duplicado" o "reemplaza" según cómo interprete "avanzado" frente a "C1"; la tercera
debería ser "reemplaza". Si la tercera no supera el umbral de similitud (0.5) se guarda como nueva y quedan dos
recuerdos contradictorios. Bajar el umbral manda más pares al LLM (más costo); mejorar la pregunta al LLM no ayuda si
el par nunca llega a él. Mide antes de decidir.

**5.** Los disimulados son los difíciles: "energía juvenil" y "recién egresados" son indicadores de edad; "que vivan en
el norte" puede ser un indicador socioeconómico; "nombres que suenen profesionales" puede ser un indicador de origen o
etnia. Si alguno pasa, añade a la política ejemplos de **atributos inferidos** (como hicimos en la capa de política de
salida) y vuelve a medir los legítimos parecidos, porque es fácil pasarse y bloquear "recién egresados para un
programa de prácticas", que sí puede ser un criterio del puesto.

**6.** Con fail-closed, el reclutador ve "No pude verificar el pedido; inténtalo de nuevo": nada pasa sin verificar.
Para un fail-open solo en "fuera de alcance" necesitarías un clasificador distinto y barato para ese caso, porque con
un único clasificador no sabes en qué categoría habría caído el pedido. Tiene sentido ahí porque el peor caso (el
asistente responde algo que no le toca) es una molestia; en "discriminatorio", el peor caso es un daño real.

**7.** Esqueleto:
```python
if p.usa_atributo_protegido:
    corregida = c.llm(Respuesta, "Reescribe la respuesta quitando cualquier mención a "
                      f"{p.cual}; no cambies nada más.", respuesta).recomendacion
    return revisar_salida(corregida, contexto)   # vuelve a pasar TODAS las capas
```
Pon un límite (una sola corrección) para no entrar en un bucle, y registra en la traza que hubo corrección. La versión
de `06` añade dos cosas que el esqueleto no tiene: antes de corregir pregunta si el atributo es **parte del motivo**
(si lo es, se bloquea: quitar la palabra escondería el sesgo), y comprueba que la corrección no cambió los candidatos.

**8.** Esqueleto, dentro de `verificar()`:
```python
if not r.aprobada and r.capa == "3 fidelidad" and vueltas < 2:
    nueva = c.llm(Reescritura, REGENERAR, f"Revisión: {r.fallas}\n<contexto>\n{contexto}\n</contexto>\n"
                                          f"<respuesta>\n{nuevo}\n</respuesta>")
    return verificar(original, nueva.texto, contexto, "regenerada", ..., vueltas=vueltas + 1)
```
El caso pasa de 3-4 llamadas a 5-6 (corrección, regeneración y dos revisiones completas). Un criterio razonable:
corrige mientras cada vuelta **quite** algo concreto y verificable; si una vuelta tiene que reinterpretar la
valoración, o el texto ya no se parece al original, ya no es una corrección sino otra respuesta, y la decide una
persona.

**9.** No hay una única solución. Lo típico: los guardrails añaden entre 2 y 4 llamadas por turno permitido
(clasificador de entrada, política y fidelidad de salida, extracción de recuerdos) y casi nada en los turnos
bloqueados por la heurística. Si un recuerdo cruzó entre reclutadores, revisa que **todas** las consultas a la memoria
filtren por usuario.

</details>
