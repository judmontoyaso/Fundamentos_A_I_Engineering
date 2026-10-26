# Módulo 5 · LLM como juez, y cómo saber si el juez acierta

> **Objetivo:** escribir un juez con LLM para el fallo que el código no puede comprobar (el perfil que inventa),
> medir con qué frecuencia se equivoca, y usar esos errores para estimar **la tasa real** de fallos del sistema.
>
> **Lo que te llevas:** un set de calibración con la respuesta conocida, separado en desarrollo y prueba; un juez que
> pasó por tres versiones con su efecto medido; y la corrección de Rogan-Gladen con su intervalo.

Índice:

1. [Cuándo hace falta un juez](#1-cuando)
2. [Un set con la respuesta conocida](#2-set)
3. [TPR y TNR, no exactitud](#3-metricas)
4. [Mejorar el juez en desarrollo](#4-desarrollo)
5. [Medirlo una vez en prueba](#5-prueba)
6. [La tasa real cuando el juez se equivoca](#6-corregida)
7. [Sesgos y cuidados](#7-sesgos)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-cuando"></a>
## 1. Cuándo hace falta un juez

El Módulo 2 dejó tres fallos graves del pipeline. Dos se comprueban con código (el contacto, con una expresión
regular; el nivel, con una regla). El tercero no: **saber si un perfil inventa algo exige leer el CV y el perfil y
compararlos**. Para eso, un LLM como juez.

Tres decisiones antes de escribirlo:

- **Un juez por fallo, no un juez de "calidad".** "¿Inventa algo que el CV no dice?" es una pregunta que se puede
  calibrar; "¿es un buen perfil?" no (Módulo 4: la guía vaga dio kappas de 0.56 y 0.26 en dos corridas).
- **Respuesta binaria.** Por las mismas razones que en la anotación.
- **El juez se trata como un clasificador**, con sus errores medidos. Un juez sin calibrar es una opinión con formato
  JSON.

---

<a name="2-set"></a>
## 2. Un set con la respuesta conocida

Para medir al juez hace falta saber la respuesta correcta en muchos casos. Con los 30 perfiles reales solo hay 4 que
inventan (las etiquetas del autor, Módulo 4): demasiado pocos para medir cuántas invenciones detecta. La solución
viene del Módulo 3, **construir desde los hechos** ([`code/01_set_del_juez.py`](code/01_set_del_juez.py)):

- Los **30 perfiles reales**, con la etiqueta del autor.
- **26 copias** de los perfiles que no inventan, a las que el código les **inserta una invención**: obvia ("Certificado
  como AWS Solutions Architect"), sutil ("Lideró un equipo de cinco personas", "Con experiencia adicional en
  Snowflake", "Con nivel de inglés C1") o numérica (los años del perfil más tres). Su etiqueta es "inventa" por
  construcción.

Son 56 ítems: 30 inventan y 26 no. Y se separan **por CV** en dos mitades: **desarrollo** (29 ítems, para mejorar el
prompt del juez) y **prueba** (27 ítems, para medirlo una sola vez al final). Separar por CV importa: si un perfil está
en desarrollo y su copia con la invención está en prueba, el prompt se ajusta a ese CV y la prueba deja de ser
independiente.

---

<a name="3-metricas"></a>
## 3. TPR y TNR, no exactitud

Un juez se equivoca de dos formas, y cuestan distinto:

- **Falso "no inventa"**: deja pasar una invención. El reclutador recibe un perfil falso.
- **Falso "inventa"**: rechaza un perfil correcto. Se pierde trabajo y, si es frecuente, el juez se desactiva.

Por eso se miden por separado:

- **TPR** (sensibilidad): de los perfiles que inventan, cuántos detecta.
- **TNR** (especificidad): de los que no inventan, cuántos deja pasar.

La exactitud mezcla las dos y depende de la proporción de cada clase en el set: con un 5 % de invenciones, un juez que
dice siempre "no inventa" tiene un 95 % de exactitud y no sirve para nada.

---

<a name="4-desarrollo"></a>
## 4. Mejorar el juez en desarrollo

[`code/02_juez_en_desarrollo.py`](code/02_juez_en_desarrollo.py) prueba tres versiones sobre el set de desarrollo
(15 ítems que inventan y 14 que no), varias veces cada una:

| Versión | Qué cambia | TPR | TNR |
|---|---|---|---|
| v1 | La pregunta tal cual, veredicto primero | 100 % · 100 % | **0 % · 7 %** |
| v2 | La definición de la guía del Módulo 4 y la lista de afirmaciones **antes** del veredicto | 100 % · 100 % | 50 % · 50 % |
| v3 | v2 + "lo que se deduce del cargo o de una tecnología no es inventar" | 100 % · 100 % · 100 % | **86 % · 64 % · 93 %** |

- **El juez nunca deja pasar una invención** (TPR del 100 % en todas las corridas). Su problema es el contrario: es un
  **paranoico**. v1 rechazó casi todos los perfiles correctos ("el perfil afirma que está orientada a construir
  soluciones end-to-end, algo que el CV no especifica").
- **v2 sale de la guía del Módulo 4**, ya trabajada con los desacuerdos, y de pedir la lista de afirmaciones antes del
  veredicto. La mitad de los falsos "inventa" desaparecieron.
- **v3 sale de leer los errores de v2**, y todos eran del mismo tipo: **para qué se usa una tecnología o qué hace un
  cargo** ("usa Tableau para análisis de datos", "un DBA da soporte y operación"). Una frase sobre eso llevó el TNR al
  64-93 %.
- **La variación entre corridas es grande**: 64 % y 93 % con el mismo prompt. Con 14 ítems negativos, cada uno vale 7
  puntos. Una sola corrida no basta para comparar versiones de un juez.

---

<a name="5-prueba"></a>
## 5. Medirlo una vez en prueba

Se elige v3 y se mide en el set de **prueba**, que no se usó para nada
([`code/03_medir_en_prueba.py`](code/03_medir_en_prueba.py)). Tres corridas sobre los mismos 27 ítems:

| | Resultado | Intervalo de confianza del 95 % (Wilson) |
|---|---|---|
| TPR | **98 %** | 88 % - 100 % |
| TNR | **81 %** | 65 % - 90 % |

Los errores se repiten en los mismos ítems (el #4 y el #25, perfiles reales correctos, en las tres corridas; la
invención real del #15, solo en una). El TNR de prueba queda dentro de lo que se vio en desarrollo (64-93 %): no hay
señal clara de que el prompt se haya ajustado a los casos de desarrollo. Si hubiera salido muy por debajo, la conclusión
sería esa, y el arreglo no es "seguir mejorando el prompt con el set de prueba", porque entonces ya no tienes set de
prueba.

El intervalo es optimista: las tres corridas repiten los mismos ítems y no son independientes. El tamaño que de verdad
manda son los 15 ítems que inventan y los 12 que no.

---

<a name="6-corregida"></a>
## 6. La tasa real cuando el juez se equivoca

El juez se usa para lo que se construyó: estimar cuántos perfiles del pipeline inventan. Si el juez marca un 23 %,
**¿la tasa real es 23 %?** No: parte de esas marcas son falsas alarmas (el TNR es 81 %, así que se equivoca en ~1 de
cada 5 perfiles correctos) y alguna invención se le escapa.

Si se conocen el TPR y el TNR, la **estimación de Rogan-Gladen** corrige la tasa observada `p`:

```
tasa real ≈ (p + TNR − 1) / (TPR + TNR − 1)
```

Y el intervalo sale de un bootstrap que remuestrea, a la vez, los perfiles juzgados **y** los juicios de calibración, de
modo que incluye la incertidumbre de los dos ([`code/04_tasa_corregida.py`](code/04_tasa_corregida.py)). Aplicado a los
perfiles del pipeline del Módulo 2:

| Perfiles | El juez marca | Tasa corregida | IC 95 % |
|---|---|---|---|
| v1 | 7 / 30 (23 %) | **5 %** | 0 % - 30 % |
| v2 | 4 / 30 (13 %) | **0 %** | 0 % - 14 % |

Tres lecturas:

- **La mayoría de las marcas eran falsas alarmas.** Con un TNR del 81 %, un juez paranoico produce un ~19 % de marcas
  aunque ningún perfil invente. Reportar "el 23 % de los perfiles inventan" habría sido falso.
- **No se puede afirmar que v2 invente menos que v1.** Los intervalos se solapan casi por completo. El juez es útil
  para **encontrar** perfiles que revisar, no para medir con precisión una diferencia así con 30 perfiles.
- **Para estrechar el intervalo** hacen falta más perfiles juzgados y, sobre todo, un juez con mejor TNR: el término
  `TPR + TNR − 1` del denominador amplifica cualquier incertidumbre cuando el juez es flojo.

---

<a name="7-sesgos"></a>
## 7. Sesgos y cuidados

- **El razonamiento antes del veredicto.** v2 pide la lista de afirmaciones antes de decidir, y el veredicto sale de
  ella. Pedir el veredicto primero y la razón después produce una justificación del veredicto, no un juicio.
- **Un juez juzgando a su propio modelo.** Un modelo tiende a aprobar el texto que él mismo escribiría (en el Módulo 3,
  `gpt-6-luna` entendió perfecto los CVs que había escrito). Si puedes, usa como juez un modelo distinto del que generó.
- **En comparaciones por pares** (¿A o B es mejor?), los jueces prefieren la primera posición o la respuesta más
  larga. Se mitiga juzgando las dos órdenes y con criterios concretos en vez de "¿cuál es mejor?".
- **Fija versión y prompt del juez**, y re-calibra cuando cambien. Un juez nuevo es un instrumento nuevo.
- **El juez nunca ve la etiqueta** ni el tipo de ítem. En el set de calibración, `origen` es solo para ti.
- **No uses un juez para lo que hace el código.** El contacto se comprueba con una expresión regular, gratis y sin
  errores.

---

## Resumen del módulo

- Un juez es un **clasificador**: se calibra, o es solo una opinión con formato JSON.
- **Un juez por fallo**, con respuesta binaria.
- Construye el set de calibración **desde los hechos** (invenciones insertadas por código) y sepáralo **por CV** en
  desarrollo y prueba.
- Mide **TPR y TNR**, no exactitud.
- Mejora el prompt **leyendo sus errores en desarrollo**; mídelo **una sola vez** en prueba.
- Aquí el juez no dejaba pasar invenciones y era **paranoico**: TNR de 0-7 % (v1) a 64-93 % (v3) en desarrollo y 81 %
  en prueba.
- Con un juez imperfecto, **corrige la tasa** (Rogan-Gladen) e informa el intervalo: un 23 % observado era un 5 %
  estimado [0-30 %].

Sigue con [`ejercicios.md`](ejercicios.md).
