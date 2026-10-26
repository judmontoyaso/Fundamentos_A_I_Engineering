# Módulo 2 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Se hacen en el **Laboratorio** de la app.

---

### Ejercicio 1 — Tu propia revisión
Corre `01` con el modelo barato y lee las 30 fichas. Escribe tus notas en una copia de `NOTAS` **sin mirar** las de
`m2_notas.py`. Después compáralas: ¿qué viste que el curso no vio? ¿Qué vio el curso que tú no?

### Ejercicio 2 — Hasta la saturación
Añade 20 CVs nuevos a `ev_datos.py` (sin etiqueta si no la necesitas: para leer no hace falta), corre `01` solo sobre
ellos y anota. Actualiza `NOTAS` y `NOTA_A_CATEGORIA` y corre `02`. ¿Aparecen categorías nuevas? ¿En qué caso apareció
la última?

### Ejercicio 3 — La regla del nivel declarado
El #22 dice "analista junior" con 3 años: el sistema dijo junior y la regla dice semi-senior. Decide qué debe pasar
cuando el CV declara su nivel, escríbelo en `RUBRICA_NIVEL` y en `nivel_esperado()` de `04`, y vuelve a correr el
paso 1. ¿Desaparece la diferencia? ¿Aparece otra?

### Ejercicio 4 — Un chequeo para el dato sensible
Escribe un chequeo por código para "dato sensible en el perfil" (año de graduación, edad, estado civil). Valídalo contra
las salidas revisadas: ¿encuentra el #26? ¿Marca algo que no debería, como "2016-2024", que es un rango de experiencia?

### Ejercicio 5 — El juez puede esperar, la lectura no
Lee 10 perfiles v2 de `salida/pipeline_v2_<modelo>.jsonl` y cuenta cuántos inventan algo. Compara con los 4 de 30 de
v1. ¿Puedes afirmar que v2 inventa menos? ¿Con cuántos casos?

### Ejercicio 6 — Agrupar con otro prompt
En `03`, pide "agrupa por PASO del pipeline donde nace el fallo" en vez de "por tipo de fallo". ¿Cómo cambia el índice
de Rand? ¿Qué agrupación te sirve más para decidir qué arreglar?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Es normal que dos lecturas difieran en los fallos leves (relleno, estilo) y coincidan en los graves. Si viste
algo grave que el curso no vio, has encontrado una categoría nueva: añádela. Si el curso vio algo grave que tú no,
pregúntate qué te hizo pasarlo por alto (¿leías rápido el perfil?). Es la base del Módulo 4: dos personas no anotan
igual, y hay que medirlo.

**2.** Lo esperable es que aparezcan una o dos categorías nuevas en los primeros casos y que después las notas caigan
en categorías conocidas. Si sigue apareciendo una nueva cada pocos casos, aún no has terminado. Los CVs nuevos más
útiles son los de formatos que el set no tiene (portugués, CVs larguísimos, tablas reales).

**3.** Una regla razonable: "si el CV declara su nivel (junior, senior), se respeta; si no, se aplica la regla de años".
Con ella, el #22 pasa. Pero mira si otro caso declara un nivel que contradice sus años: has movido la frontera, no la
has eliminado. Cada cambio de la regla obliga a re-validar el chequeo con el paso 1.

**4.** Esqueleto:
```python
SENSIBLE = re.compile(r"gradu\w* (en )?\d{4}|\b\d{2} años de edad|\bcasad|\bsolter|\bhijos", re.IGNORECASE)
```
Debe encontrar el #26 ("graduada 2010"). Cuidado con los rangos de fechas de experiencia: por eso la expresión exige
la palabra "gradu..." junto al año, y no un año suelto. Valídalo igual que en el paso 1 de `04`.

**5.** Con 10 perfiles no puedes afirmar mucho: si v1 inventaba en ~4 de 30 (13 %) y en tus 10 de v2 no ves ninguno,
la regla del tres dice que la tasa de v2 está por debajo de ~30 % con 95 % de confianza. No alcanza para decir "menos
que v1". Necesitas más casos o un juez que los revise todos (Módulo 5).

**6.** Agrupar por paso da menos grupos y más grandes ("perfil": 9 casos), y el índice de Rand con la agrupación manual
baja, porque mezcla causas distintas. Sirve para saber **dónde** está el trabajo, pero no **qué** cambiar: "arreglar el
perfil" no es una acción; "prohibir el contacto en el perfil" sí. Por eso la agrupación útil es por causa.

</details>
