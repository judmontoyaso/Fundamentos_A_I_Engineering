# Módulo 3 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Corre los laboratorios en orden: `02` genera, `03`
valida y `04` evalúa sobre `salida/sinteticos_validos.jsonl`.

---

### Ejercicio 1 — Una dimensión nueva
Añade a `DIMENSIONES` una dimensión que creas que puede romper el extractor (por ejemplo "fechas": `2018-2021` /
`ene 2018 - mar 2021` / `03/2018 - 06/2021`). Haz que `hechos()` y las instrucciones de `02` la usen, y que `03` la
valide. ¿Qué valor falla más?

### Ejercicio 2 — Interacciones
El muestreo cubre cada valor, no cada combinación. Toma los dos valores que más fallaron con `nano` (rangos solapados y
portugués) y genera 12 CVs que los combinen. ¿Falla más la combinación que cada valor por separado?

### Ejercicio 3 — Otro generador
Genera los CVs con `gpt-4.1-mini` en vez de `gpt-6-luna` (pasa `modelo=` a `llm_trazado` en `generar()`). Valida y
evalúa `gpt-6-luna` sobre ellos. ¿Sigue sacando 35/35? ¿Cambia la diversidad?

### Ejercicio 4 — Una regla de código para valores absurdos
Algunos fallos fueron absurdos: 14 años para "14 meses", 15 años para dos trabajos entre 2011 y 2016. Escribe una
comprobación en código que, a partir de los años que aparecen en el texto, marque como sospechoso un
`anios_experiencia` imposible (más años que los que hay entre el primer y el último año mencionados, o más que hoy menos
el primer año). ¿Cuántos fallos de `nano` habría atrapado?

### Ejercicio 5 — ¿Cuántos sintéticos hacen falta?
Con `nano` v1, los rangos solapados fallaron 4 de 6. Calcula, con la regla del tres o con un intervalo, qué puedes decir
de la tasa real de fallo en ese valor con 6 casos. ¿Cuántos casos necesitarías para distinguir "falla la mitad de las
veces" de "falla 2 de cada 3"?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Las fechas con meses abreviados y las numéricas (`03/2018`) suelen fallar más en modelos pequeños, porque el
cálculo de años se complica (¿de marzo de 2018 a junio de 2021 son 3 años?). Antes de generar, decide la regla de la
etiqueta (por ejemplo, "años completos") y escríbela en `anios_de()`. Si no, generas casos con etiqueta ambigua.

**2.** Es frecuente que la combinación falle más que cada valor por separado: dos dificultades a la vez (leer portugués
y calcular solapes) suman. Si es así, esa interacción merece su propio grupo de casos en el set. Si no, el muestreo por
valor bastaba.

**3.** Con otro generador, `gpt-6-luna` puede seguir sacando todo perfecto, y entonces el set es simplemente fácil para
él; o puede fallar algún caso, y has encontrado su primer fallo real. La diversidad suele cambiar poco entre
generadores de la misma familia. Para el modelo grande, la vía más efectiva sigue siendo buscar CVs reales difíciles.

**4.** Esqueleto:
```python
anios = [int(x) for x in re.findall(r"\b(19|20)\d{2}\b", texto)]   # usa re.finditer para el año completo
if anios and ficha.anios_experiencia > (max(max(anios), HOY.year if vigente else 0) - min(anios)):
    sospechoso = True
```
Habría atrapado los absurdos (14 o 15 años en un rango de 4 o 5), no los errores de uno o dos años. Es el tipo de
regla barata que se pone como **guardrail** en producción (Módulo 10): no hace falta saber la respuesta correcta para
saber que una respuesta es imposible.

**5.** Con 4 de 6, un intervalo de confianza del 95 % para la tasa va aproximadamente de 22 % a 96 %: casi no dice nada.
Para distinguir 50 % de 67 % con un 95 % de confianza y un 80 % de potencia hacen falta unos 70 casos por valor. Por eso los
sintéticos sirven para **encontrar** dónde falla (este valor falla mucho más que "años explícitos", 0 de 6), no para
**medir** con precisión cuánto.

</details>
