# Proyecto final · Evaluar desde cero un sistema que no construiste

> **Objetivo:** aplicar todo el curso a un sistema ajeno: un **extractor de vacantes** (ofertas de empleo → datos
> estructurados). No sabes cómo está hecho ni dónde falla. Al final tienes que poder decir, con evidencia, **qué
> falla, con qué frecuencia, por qué y qué arreglarías primero**.

Índice:

1. [El sistema](#1-sistema)
2. [Las reglas del juego](#2-reglas)
3. [Las fases](#3-fases)
4. [Entregables y rúbrica](#4-entregables)

Código en [`code/`](code/). Entregables y solución de referencia en [`ejercicios.md`](ejercicios.md).

---

<a name="1-sistema"></a>
## 1. El sistema

`extraer_vacante(texto)` (en [`comun/m12_vacantes.py`](../comun/m12_vacantes.py)) recibe el texto de una oferta de
empleo y devuelve:

| Campo | Qué es |
|---|---|
| `cargo` | El puesto |
| `nivel` | junior · semi-senior · senior · no indicado |
| `anios_minimos` | Los años de experiencia que pide |
| `skills_requeridas`, `skills_deseables` | Las tecnologías obligatorias y las que son un plus |
| `modalidad` | remoto · presencial · híbrido · no indicada |
| `ciudad` | La ciudad, si aplica |
| `salario_mensual_cop` | El salario mensual en pesos, si aparece |

El área de selección lo quiere usar para filtrar vacantes ("remotas, senior, más de 10 millones"). Te piden evaluarlo
antes de ponerlo en producción. Tienes 10 ofertas reales de ejemplo (`OFERTAS`) y nada más: ni etiquetas, ni set de
evaluación, ni documentación.

---

<a name="2-reglas"></a>
## 2. Las reglas del juego

- **No leas `comun/m12_vacantes.py` hasta la fase 4.** En un sistema ajeno de verdad no sabrías dónde mirar, y leer
  el código antes te haría buscar solo lo que ves en él.
- **No leas la solución de referencia** (al final de `ejercicios.md` y en `solucion/`) hasta tener tu informe.
- **Todo número que des, con su tamaño de muestra y su repetición.** "Falla el 40 %" no vale; "falla en 4 de 10
  ofertas, en las 2 corridas" sí.

---

<a name="3-fases"></a>
## 3. Las fases

Cada fase es un módulo del curso, en el mismo orden:

| Fase | Qué haces | Módulo |
|---|---|---|
| 1. Conocer | Corre [`code/01_conocer_el_sistema.py`](code/01_conocer_el_sistema.py) y lee las 10 salidas. Notas abiertas, una por problema | 0, 2 |
| 2. Error analysis | Agrupa tus notas en categorías con paso y gravedad. ¿Qué fallos le importan a quien va a filtrar vacantes? | 2 |
| 3. Etiquetas y eval | Escribe **las reglas antes** de etiquetar (¿un rango de años? ¿un nivel que no se dice?). Etiqueta las 10 en [`code/02_tu_eval.py`](code/02_tu_eval.py) y córrelo con repeticiones | 1, 4 |
| 4. Atribuir | Ahora sí: lee `comun/m12_vacantes.py`. Para cada fallo, ¿nace en el **prompt**, en el **modelo** o en el **código** de posprocesado? Confírmalo midiendo (por ejemplo, la salida del modelo antes del posprocesado) | 6, 7 |
| 5. Más casos | Diez ofertas no bastan. Genera más desde los hechos (Módulo 3) para los tipos que más fallaron, y valida que el generador hizo lo que pediste | 3 |
| 6. Juez, si hace falta | ¿Algún criterio exige leer (por ejemplo, separar requeridas de deseables)? Si sí, un juez calibrado; si no, código | 5 |
| 7. Arreglar y confirmar | Arregla lo más importante y mide en un holdout. Deja casos críticos y umbrales en una suite (Módulo 9) | 9, 11 |
| 8. Producción | ¿Qué chequeos sin referencia pondrías? (un salario de 12 billones no necesita etiqueta para ser imposible) | 10 |

---

<a name="4-entregables"></a>
## 4. Entregables y rúbrica

Un **informe de una página** para quien decide si se usa el sistema, más el código de tu eval. El informe tiene:

1. Qué hace el sistema y con qué datos lo evaluaste.
2. Los fallos, ordenados por prioridad, **cada uno con su frecuencia medida, su origen (prompt, modelo o código) y su
   gravedad para el usuario**.
3. Qué arreglarías primero y por qué, y qué arreglaste (con el antes y el después).
4. Qué no sabes todavía (qué no midió tu eval).
5. Tu recomendación: ¿se usa, con qué condiciones?

La rúbrica, en [`ejercicios.md`](ejercicios.md), junto con la solución de referencia.

---

## Lo que se practica

Todo el curso en un sistema que no conoces: **leer antes de medir**, **reglas antes que etiquetas**, **chequeos por
código antes que jueces**, **separar dónde nace cada fallo**, **repetir**, **más casos desde los hechos**, **holdout
para decidir**, **suite para no retroceder** y **chequeos sin referencia para producción**.
