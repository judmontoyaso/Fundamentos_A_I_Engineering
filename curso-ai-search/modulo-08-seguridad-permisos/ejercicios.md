# Módulo 8 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas).

---

### Ejercicio 1 — Un permiso estrecho
Cambia `visibles()` para que cada reclutador vea solo los CVs de su cliente, sin los generales. Repite la parte 1.
¿Cuántos resultados deja el post-filtro 30? ¿Cuánto tendrías que buscar para llenar la página?

### Ejercicio 2 — Una inyección mejor
Escribe una inyección más agresiva para los CVs prohibidos. Por ejemplo, una que cierre la etiqueta `<cv>` y abra
otra con `autorizado_para="general"`. Pruébala con los dos modelos. ¿Qué defensa en el código la anula sin depender
del modelo?

### Ejercicio 3 — La cuenta que delata
Añade la pregunta "¿Cuántos analistas de seguridad hay?" con la regla en el prompt y con el filtro en el código. ¿Qué
número da cada una a un reclutador de Salud Orquídea? ¿Por qué una cuenta es una fuga aunque no tenga nombres?

### Ejercicio 4 — Trazas que no guardan personas
Modifica (en una copia) `enmascarar()` del trazador para que tampoco guarde nombres. ¿Qué pondrías en su lugar para que
las trazas sigan sirviendo para depurar? Repite el inventario: ¿cuántas apariciones quedan?

### Ejercicio 5 — Cambiar de embedder
Añade a la huella la versión del modelo de embeddings. Simula que el día 10 se cambia al embedder afinado del Módulo
4. ¿Cuántos embeddings calcula el incremental ese día? ¿Qué pasa si no incluyes la versión en la huella?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Con permisos estrechos (de 20 a 27 CVs por reclutador):

| Forma | nDCG@10 | Resultados |
|---|---|---|
| Sin filtro | 0.41 | 10 |
| Post-filtro 10 | 0.69 | **2.0** |
| Post-filtro 30 | 0.77 | **6.0** |
| Pre-filtro | 0.79 | 10 |

Para llenar la página con post-filtro necesitarías buscar alrededor de 10 ÷ (fracción visible) ≈ 50, y aun así
habría consultas que no se llenan. Cuanto más estrecho el permiso, más claro es que el filtro tiene que ir **dentro**
de la búsqueda (o en una partición por cliente).

**2.** En mi corrida, la inyección que cierra la etiqueta no pudo con gpt-6-luna (0 de 27) y gpt-5.4-nano filtró en
17 de 27. La defensa que no depende del modelo es la del §3, el filtro en el código: el CV prohibido no llega al
contexto. Para el resto de las inyecciones (las de CVs permitidos), **escapa los delimitadores**: reemplaza `<` y `>`
en el texto del CV antes de envolverlo, para que un CV no pueda cerrar su propia etiqueta. Es lo mismo que escapar SQL:
el dato no debe poder convertirse en estructura.

**3.** Hay 10 analistas de seguridad, y Salud Orquídea puede ver 7. En mi corrida (tres repeticiones de cada una):

| | Filtro en el código | Regla en el prompt |
|---|---|---|
| gpt-6-luna | 7, 7, 7 | 7, 7, 7 |
| gpt-5.4-nano | 8, 8, 8 | 6, 6, 7 |

Aquí ningún modelo contó a los ocultos: nano se equivoca, pero hacia abajo con la regla en el prompt y contando uno de
más (que no es analista) con el filtro. Esperaba una fuga y no la hubo; la conclusión del §3 no cambia, porque con la
regla en el prompt que el número salga bien depende del modelo, y con el filtro no. Lo que sí es una fuga por
construcción es **un agregado calculado sobre todo**: si otra pantalla de la agencia dice "hay 10" y el reclutador ve
7, ya sabe que existen 3 que no puede ver. Los agregados se calculan sobre lo permitido, y en sistemas sensibles se
redondean o se ocultan cuando son pequeños.

**4.** Lo útil para depurar no es el nombre, es **qué documento** entró. Guarda el `cv_id` (o un hash) y la longitud,
y reemplaza los nombres conocidos por `[candidato 27]`. Así se puede reconstruir la traza consultando la fuente, que
sí se borra. Después del cambio, las trazas **nuevas** no tienen nombres, pero las 34 apariciones viejas siguen ahí: el
arreglo de la fuente no borra el pasado. Hace falta además una retención (borrar trazas de más de N días) o un borrado
por id.

**5.** El día del cambio, el incremental tiene que recalcular **todos** los CVs vivos (unos 110): ninguna huella vieja
coincide, porque la versión del modelo cambió. Es lo correcto. Sin la versión en la huella, el incremental no
recalcularía nada (los textos no cambiaron) y mezclaría vectores de dos modelos en el mismo índice: las similitudes
entre una consulta del modelo nuevo y vectores del viejo no significan nada, y el sistema fallaría en silencio, sin
ningún error.

</details>
