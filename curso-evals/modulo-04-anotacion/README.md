# Módulo 4 · Las personas que etiquetan, y cómo se ponen de acuerdo

> **Objetivo:** que las etiquetas contra las que mides el sistema sean confiables: una guía escrita, un acuerdo
> medido entre anotadores y un proceso para convertir cada desacuerdo en una regla.
>
> **Lo que te llevas:** una tarea de anotación real en la app (tú etiquetas 30 perfiles), el kappa de Cohen calculado
> y entendido, y la historia de una guía que pasó por cuatro versiones con su efecto medido.

Índice:

1. [El eval es tan bueno como sus etiquetas](#1-etiquetas)
2. [La tarea y la guía](#2-tarea)
3. [Tu turno: anotar](#3-anotar)
4. [Medir el acuerdo: por qué no basta el porcentaje](#4-kappa)
5. [Lo que pasó con los anotadores LLM](#5-llm)
6. [Resolver desacuerdos: cada uno es una regla que falta](#6-resolver)
7. [Cómo organizar la anotación](#7-organizar)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-etiquetas"></a>
## 1. El eval es tan bueno como sus etiquetas

Todo lo anterior supuso que las etiquetas eran correctas. En el Módulo 1 se dijo que el #30 (mesero 2012-2015,
frontend 2015-2023) tiene 11 años de experiencia, y `gpt-4o-mini` "falló" al decir 8. ¿Falló, o aplicó un criterio
distinto igual de razonable? Si otra persona hubiera etiquetado 8, ese caso no mediría al modelo: mediría a quién le
tocó etiquetar.

Para los campos exactos (correo, nombre) el problema es pequeño. Para los juicios ("¿este perfil se puede enviar?")
es enorme, y es justo donde más se necesita un eval. La pregunta del módulo: **¿dos personas razonables, con la misma
guía, etiquetarían igual?** Si no, el eval mide ruido.

---

<a name="2-tarea"></a>
## 2. La tarea y la guía

La tarea ([`anotacion.json`](anotacion.json)) son los 30 perfiles del pipeline del Módulo 2, con una pregunta binaria:
**¿se puede enviar este perfil a un reclutador tal como está?** Binaria a propósito: una escala del 1 al 5 parece más
informativa y es más difícil de acordar (¿qué separa un 3 de un 4?). Si un juicio se puede convertir en sí o no, se
convierte.

La guía dice cuándo **no pasa**: si afirma algo concreto que el CV no dice, si incluye contacto, si deja inferir un
atributo protegido o si contradice el CV. Y dice qué **sí pasa**: el relleno que no afirma nada falso.

Las etiquetas del autor del curso están en [`comun/m4_etiquetas_autor.py`](../comun/m4_etiquetas_autor.py): **8 de 30
no pasan**, y cuatro se marcaron como **dudosos** en el momento de etiquetar (el #9 "experto en Jenkins", el #20 "base
técnica sólida", el #25 "recién graduado", el #5 "enfoque en mejora continua"). Anotar la duda es tan importante como
la etiqueta: dice dónde la guía no alcanza.

---

<a name="3-anotar"></a>
## 3. Tu turno: anotar

En la app, la página **Anotar (tu turno)** de este módulo muestra cada CV con su perfil, la guía y dos botones (atajos
<kbd>P</kbd> y <kbd>N</kbd>). Etiqueta los 30 **sin mirar** las etiquetas del autor y escribe una nota cuando dudes.
Tarda unos 15 minutos y es la única forma de que este módulo mida un acuerdo **entre personas**.

Tus etiquetas quedan en la base de la app, y el laboratorio [`code/01_acuerdo_entre_anotadores.py`](code/01_acuerdo_entre_anotadores.py)
las compara con las del autor en cuanto tengas 10 o más.

---

<a name="4-kappa"></a>
## 4. Medir el acuerdo: por qué no basta el porcentaje

El **porcentaje de acuerdo** (en cuántos casos coinciden) engaña cuando una etiqueta es mucho más frecuente que la
otra. [`code/03_paradoja_del_kappa.py`](code/03_paradoja_del_kappa.py) lo muestra con dos parejas que coinciden en el
**90 %**:

| Pareja | "No pasa" | Acuerdo | Kappa |
|---|---|---|---|
| Fallos frecuentes | 50 de 100 cada uno | 90 % | **0.80** |
| Fallos raros | 5 de 100 cada uno, **ninguno en común** | 90 % | **−0.05** |

En la segunda pareja, los dos dicen "pasa" en casi todo y **no coinciden en ningún fallo**. El 90 % sale gratis: dos
anotadores que no leen y dicen "pasa" al azar el 95 % de las veces también coinciden en ~89 %.

El **kappa de Cohen** corrige eso: compara el acuerdo observado con el que se esperaría **por azar** dadas las
proporciones de cada anotador. `kappa = (acuerdo observado − acuerdo por azar) / (1 − acuerdo por azar)`. 1 es acuerdo
perfecto; 0, el del azar; negativo, peor que el azar. Una lectura habitual: por debajo de 0.4, débil; 0.4-0.6,
moderado; 0.6-0.8, bueno; por encima de 0.8, muy bueno. Reporta siempre el kappa **y** cuántos "no pasa" marcó cada
uno.

---

<a name="5-llm"></a>
## 5. Lo que pasó con los anotadores LLM

Mientras no hay una segunda persona, el laboratorio usa anotadores LLM (`gpt-6-luna`) para ver qué le hace la guía al
acuerdo. **No sustituyen a una persona** (el Módulo 5 trata a un LLM como juez y explica cómo calibrarlo); aquí
sirven de lupa. Cada anotador se corrió dos veces:

| Anotador | "No pasa" (autor: 8) | Acuerdo | Kappa |
|---|---|---|---|
| LLM con guía vaga ("¿es un buen perfil?") | 7 y 6 | 83 % y 73 % | **0.56 y 0.26** |
| LLM con la guía completa (v2) | 25 y 24 | 43 % y 47 % | **0.14 y 0.17** |

Dos sorpresas:

- **La guía vaga dio resultados muy distintos en dos corridas** (kappa 0.56 y 0.26). Sin criterio escrito, el juicio
  cambia de una vez a otra, igual que cambiaría entre dos personas.
- **La guía completa hundió el acuerdo.** El LLM pasó a rechazar 25 de 30 perfiles. ¿Por qué? Sus razones: "afirma
  **especialización** en Terraform y Kubernetes, que el CV no especifica", "afirma **dominio** de Python", "el CV no dice
  que sea **experto** en Jenkins". La guía prohibía "una cualidad específica que el CV no dice", y el LLM la aplicó a
  la letra. El autor, en cambio, dejaba pasar "especialista en..." como lenguaje normal de un perfil, y solo dudó en el
  #9 ("experto"). **La guía permitía las dos lecturas**: el desacuerdo destapó una frontera que nadie había decidido.

---

<a name="6-resolver"></a>
## 6. Resolver desacuerdos: cada uno es una regla que falta

[`code/02_resolver_desacuerdos.py`](code/02_resolver_desacuerdos.py) sigue el proceso: leer la razón de cada
desacuerdo, encontrar la frase de la guía que admite dos lecturas, **decidir**, escribir la decisión y volver a medir.

Se decidió que "especialista en", "dominio de" o "experto en" acompañando algo que **sí** está en el CV no es una
invención (guía v3). Después se probó otra técnica muy recomendada: cuatro **ejemplos resueltos**, escritos fuera del
set (guía v4). Resultado, dos corridas por versión:

| Guía | "No pasa" (autor: 8) | Kappa con el autor |
|---|---|---|
| v2 (completa) | 22-26 | 0.11 - 0.23 |
| **v3 (con la aclaración)** | 16-17 | **0.35 - 0.48** |
| v4 (aclaración + 4 ejemplos) | 18-19 | 0.35 - 0.39 |

- **La aclaración ayudó**: el kappa pasó de 0.11-0.23 a 0.35-0.48. Una sola frase sobre la frontera correcta movió
  más que cualquier otra cosa.
- **Los ejemplos no añadieron nada medible.** Es un resultado contrario a lo que suele recomendarse, y es el que salió:
  con dos corridas por versión, la diferencia entre v3 y v4 queda dentro de lo que varía entre corridas.
- **El LLM sigue siendo más estricto que el autor**, y siempre en la misma dirección: coincide en los 8 "no pasa" del
  autor y rechaza además perfiles con frases de orientación ("orientada a la ejecución", "aplicaciones robustas"). ¿Quién
  tiene el criterio razonable? **Eso no lo puede decidir el LLM**, y tampoco el autor solo. Hace falta una segunda
  persona: tú.

Dos reglas del proceso:

- **No se resuelve votando ni dándole la razón al más experto.** Se resuelve decidiendo la frontera y escribiéndola. A
  veces la decisión obliga a cambiar las etiquetas de quien escribió la guía.
- **Cada cambio de la guía se mide**, con repeticiones. Una guía "mejorada" que no sube el acuerdo no mejoró nada.

---

<a name="7-organizar"></a>
## 7. Cómo organizar la anotación

- **Empieza con una sola persona experta en el dominio** que etiquete y escriba la guía mientras etiqueta. En un equipo
  pequeño, esa persona suele ser quien entiende al usuario, no quien escribió el código.
- **Mide el acuerdo con una segunda persona sobre 30-50 casos** antes de escalar. Si el kappa es bajo, el problema es la
  guía, no las personas.
- **Anota la duda y la razón**, no solo la etiqueta.
- **Etiqueta a ciegas**: sin ver la salida de otro anotador ni la del sistema "bueno".
- **Re-etiqueta cuando cambie la guía**, al menos los casos afectados.
- **Herramientas:** la página de la app basta para empezar. A escala, Label Studio, Argilla o la anotación de Langfuse
  hacen lo mismo con varios usuarios.

---

## Resumen del módulo

- Un eval de juicio solo vale si **dos personas razonables etiquetan igual** con la misma guía.
- Prefiere preguntas **binarias** a escalas.
- **Anota la duda**: marca dónde no alcanza la guía.
- El **porcentaje de acuerdo engaña** con fallos raros; usa el **kappa de Cohen** y mira cuántos fallos marcó cada uno.
- Una **guía vaga** dio kappas de 0.56 y 0.26 en dos corridas: el criterio cambia de una vez a otra.
- Una **guía estricta** aplicada a la letra hundió el acuerdo (0.14): la frontera "¿'especialista en' es inventar?" no
  estaba decidida.
- **Cada desacuerdo es una regla que falta**: decide, escribe, re-mide. Aquí una aclaración subió el kappa a 0.35-0.48 y
  los ejemplos no añadieron nada.
- Un LLM puede servir de lupa, **no** de segunda persona.

Sigue con [`ejercicios.md`](ejercicios.md).
