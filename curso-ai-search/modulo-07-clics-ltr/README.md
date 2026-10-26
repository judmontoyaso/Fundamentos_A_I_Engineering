# Módulo 7 · Lo que enseñan los clics, y learning to rank

> **Objetivo:** aprender a ordenar de lo que hacen los usuarios sin aprender también sus sesgos, y saber qué parte del
> problema ningún clic puede resolver.
>
> **Lo que te llevas:** un simulador de clics con sesgo de posición, un modelo de learning to rank entrenado con clics
> crudos, con clics corregidos (IPS) y con la relevancia verdadera, la propensión estimada con intercambios, y la
> medida de un sesgo que IPS no corrige: el de selección.

Índice:

1. [Los clics son datos, y están torcidos](#1-clics)
2. [Un usuario simulado](#2-simular)
3. [Learning to rank, cuatro veces](#3-ltr)
4. [Lo que pasó](#4-resultados)
5. [IPS necesita θ: estimarla](#5-theta)
6. [Lo que ningún clic arregla: la selección](#6-seleccion)
7. [Antes de usar clics reales](#7-reales)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-clics"></a>
## 1. Los clics son datos, y están torcidos

Hasta aquí, cada mejora se midió contra relevancias **calculadas desde los hechos**. En producción nadie te las da. Lo
que sí hay, gratis y a montones, son los **clics** de los reclutadores: a quién abrieron, a quién guardaron. Es la
señal más barata que existe y la más tentadora para entrenar un ranker.

El problema: **un clic no dice "esto es relevante", dice "lo vi y me gustó"**. Y lo que está arriba se ve mucho más
que lo que está abajo. Si entrenas con clics crudos, el modelo aprende que lo bueno es "lo que ya estaba arriba", y el
buscador se convierte en un espejo de sí mismo. Es el **sesgo de posición**. Hay otro peor, el de **selección**: de lo
que no se mostró no hay clics, ni buenos ni malos (§6).

---

<a name="2-simular"></a>
## 2. Un usuario simulado

[`code/01_clics_y_learning_to_rank.py`](code/01_clics_y_learning_to_rank.py) simula reclutadores con el **modelo basado
en la posición** (PBM), el más usado para razonar sobre clics:

    P(clic en el resultado de la posición k) = P(lo mira) × P(le atrae)  =  θ_k × γ(relevancia)

- **θ_k**, la propensión de mirar: 0.95 en la posición 1 y cae como 1/k^0.9 (0.13 en la 10).
- **γ**, la atracción: 0.8 si el CV es muy relevante, 0.35 si es relevante y 0.08 si no lo es (también se hace clic
  en lo que no sirve).

Producción es el top 10 de la búsqueda híbrida del Módulo 1. Cada una de 26 consultas recibe 60 sesiones: unos 2.500
clics. La tasa de clic por posición sale 57% · 28% · 20% · 14% · 11% · 9% · 7% · 4% · 6% · 3%. La caída es mucho más
fuerte que la diferencia de calidad entre posiciones: casi toda es θ.

Con una simulación conoces la verdad (θ y la relevancia), y por eso puedes medir si un método la recupera. Con clics
reales no se puede, y por eso conviene empezar así.

> Un error que cometí al escribir el laboratorio, y que vale la pena contar: "producción" en la simulación era la
> fusión de los top 10 de cada buscador (hasta 20 CVs), y la feature de posición y la evaluación usaban el top 10 de
> la fusión completa. Los números salían razonables y estaban mal. Ahora una sola función, `produccion()`, define lo que
> ve el reclutador. **Cuando dos partes de un experimento calculan "lo mismo", que sea con el mismo código.**

---

<a name="3-ltr"></a>
## 3. Learning to rank, cuatro veces

Un modelo lineal (Ridge) puntúa pares (consulta, CV) con seis features: BM25, similitud densa, MaxSim (Módulo 4), la
inversa de la posición en producción, la fracción de requisitos del parser que el CV cumple y si el rol coincide
(Módulo 2). Es **pointwise**: aprende a predecir un número por par y ordena por él. Se entrena con cuatro objetivos:

| Modelo | Con qué se entrena | Qué aprende |
|---|---|---|
| **Ingenuo** | tasa de clics de los CVs mostrados | relevancia **y** posición, mezcladas |
| **IPS** | cada clic pesado por 1/θ_k | relevancia de los mostrados: un clic en la posición 8 vale casi 7 veces uno en la 1 |
| **Oráculo** | relevancia verdadera de los CVs mostrados | lo mejor que se puede sacar de esos mismos pares |
| **Oráculo (todos)** | relevancia verdadera de **todos** los CVs | lo que ningún log te da |

**IPS** (*inverse propensity scoring*) es la corrección estándar. Si un CV en la posición k recibe clics con
probabilidad θ_k·γ, dividir cada clic por θ_k deja γ en esperanza: lo que el clic decía del CV, sin lo que decía del
lugar. El precio es varianza: los clics de abajo son pocos y pesan mucho.

Los dos oráculos no son un sistema que puedas construir: son **reglas de medir**. La distancia entre el ingenuo y el
oráculo es lo que cuesta el sesgo de posición; la distancia entre los dos oráculos, lo que cuesta el de selección.

Se evalúa en las 15 consultas que **no** estaban en los logs, con la relevancia verdadera, y se repite con **10
particiones** distintas de entrenamiento y prueba. Con 15 consultas de prueba, una sola partición engaña: la primera
que corrí le daba 0.94 a IPS, y la media es 0.88.

---

<a name="4-resultados"></a>
## 4. Lo que pasó

Pesos aprendidos (features estandarizadas, partición 0):

| Feature | Ingenuo | IPS | Oráculo | Oráculo (todos) |
|---|---|---|---|---|
| 1 / posición en producción | **0.138** | 0.019 | 0.041 | 0.097 |
| fracción de requisitos | 0.084 | **0.293** | **0.727** | 0.296 |
| rol coincide | -0.006 | 0.035 | 0.165 | **0.469** |
| BM25 | 0.011 | 0.028 | 0.087 | 0.152 |
| densa | -0.002 | -0.027 | **-0.141** | -0.066 |

**El modelo ingenuo aprendió el sesgo**: su feature más importante es dónde estaba el CV en producción. IPS se lo
quita (0.138 → 0.019) y pasa el peso a los requisitos, como el oráculo.

nDCG@10 en prueba, media de 10 particiones:

| Ranker | nDCG@10 | Rango |
|---|---|---|
| Producción (híbrida) | 0.69 | 0.58 – 0.76 |
| LTR ingenuo | 0.82 | 0.77 – 0.89 |
| **LTR IPS** | **0.88** | 0.78 – 0.95 |
| LTR oráculo | 0.90 | 0.81 – 0.98 |
| Filtros suaves (Módulo 2, escritos a mano) | 0.90 | 0.81 – 0.98 |
| LTR oráculo (todos) | 0.92 | 0.87 – 0.97 |

Tres lecturas:

- **IPS supera al ingenuo** (0.88 contra 0.82, en 8 de las 10 particiones) y se acerca al oráculo que usa los mismos
  pares. Corregir la posición vale 6 puntos.
- **El ingenuo también mejora a producción** (0.69 → 0.82): los clics traen información aunque estén torcidos.
- **Más clics no ayudan.** Con 5, 60 o 300 sesiones por consulta, IPS da 0.873, 0.875 y 0.881. El límite no es la
  cantidad de datos sino **qué** datos hay: solo de los 10 CVs que se mostraron.

---

<a name="5-theta"></a>
## 5. IPS necesita θ: estimarla

IPS necesita la propensión θ_k, y en producción no la conoces. La forma limpia de estimarla es **intervenir**:
[`code/02_estimar_el_sesgo.py`](code/02_estimar_el_sesgo.py) intercambia el resultado 1 con el k en la mitad de las
sesiones. Con tantas sesiones normales como intercambiadas, los dos CVs pasan el mismo tiempo en cada posición, así que

    clics en la posición k / clics en la posición 1  =  θ_k / θ_1

sin saber nada de la relevancia. IPS solo necesita la θ relativa: multiplicar todos los objetivos por una constante no
cambia el orden.

| Posición | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| θ verdadera (relativa) | 1.00 | 0.54 | 0.37 | 0.29 | 0.23 | 0.20 | 0.17 | 0.15 | 0.14 | 0.13 |
| θ estimada | 1.00 | 0.52 | 0.36 | 0.28 | 0.24 | 0.19 | 0.17 | 0.16 | 0.15 | 0.13 |

**El costo de intervenir** es bajo: las listas con el intercambio tienen nDCG@10 0.66 contra 0.69 de producción. Si
se interviene en el 5% de las sesiones, el reclutador medio pierde 0.001 de nDCG.

Y lo que importa, el ranker resultante, según la θ que use IPS (media de 10 particiones):

| θ que usa IPS | nDCG@10 |
|---|---|
| verdadera | 0.875 |
| **estimada con intercambios** | **0.879** |
| equivocada (1/k, más empinada que la real) | 0.858 |
| plana (= no corregir, el ingenuo) | 0.824 |

La estimada rinde como la verdadera (la diferencia es ruido de la simulación). Una θ equivocada corrige a medias.
**Medirla es barato.**

---

<a name="6-seleccion"></a>
## 6. Lo que ningún clic arregla: la selección

De los 308 pares (consulta, CV muy relevante), **121 (39%) nunca aparecen en el top 10 de producción**. Ningún clic
habla de ellos: IPS corrige que lo de abajo se mire poco, no lo que no se mostró nunca (θ = 0).

Los pesos de la tabla del §4 muestran el daño. El oráculo entrenado con los mostrados le da a la similitud densa un
peso **negativo** (-0.141) y poco al rol (0.165). Tiene sentido **entre los mostrados**: todos llegaron al top 10 por
parecerse a la consulta, y los que llegaron solo por parecerse, sin cumplir los requisitos, son justo los irrelevantes.
Pero el modelo ordena a los 119, y entre los 119 la mayoría ni siquiera tiene el rol: el oráculo con todos los CVs le
da al rol 0.469. **Un modelo entrenado con lo que se mostró aprende reglas que solo valen para lo que se mostró.**

Eso es el sesgo de selección, y cuesta (0.90 → 0.92) lo que ningún volumen de clics recupera. Las salidas cuestan:

- **Explorar**: mostrar de vez en cuando, en una posición baja, un candidato que el ranker no habría puesto. Cuesta un
  poco de calidad (como los intercambios del §5) y compra datos de lo que hoy es invisible. Al azar compra poco
  (ejercicio 4); se explora con candidatos **prometedores**.
- **Entrenar con lo que sí sabes de todos**: un conjunto de evaluación etiquetado (Módulos 0 y 1) cubre CVs que nadie
  mostró. Unos cientos de etiquetas buenas valen más que miles de clics de lo mismo.
- **Buenas features**: lo que el parser y las fichas de los Módulos 2 y 3 ya extraen. Los filtros suaves, escritos a
  mano con esas features, empatan con el oráculo de los mostrados sin un solo clic.

Y el ciclo: si el ranker se reentrena siempre con los clics del anterior, lo que nunca se mostró **nunca** se mostrará.

---

<a name="7-reales"></a>
## 7. Antes de usar clics reales

La simulación tiene un sesgo de posición limpio y un usuario que no se cansa. Los logs reales traen más:

- **Sesgo de confianza**: el usuario hace más clic arriba no solo porque mira más, sino porque cree que el buscador
  sabe. La θ estimada con intercambios lo absorbe en parte.
- **El clic no es la meta**: en reclutamiento, la señal valiosa es "lo entrevisté" o "lo contraté", rara y tardía. Los
  clics son un sustituto barato y ruidoso. Usa la señal más cercana a la meta de la que tengas suficiente cantidad.
- **Presentación**: un CV con foto o con un titular llamativo atrae más clics sin ser más relevante (la γ depende de
  cosas que no son relevancia).
- **Bots, pruebas internas y usuarios que repiten la consulta**: límpialos antes de contar.
- **Evalúa fuera de línea con tu conjunto etiquetado**, no solo con clics. Un ranker entrenado y evaluado con clics
  puede mejorar en su propia medida y empeorar en la tuya, y la selección es invisible si solo miras clics.

---

## Resumen del módulo

- Un clic dice **"lo vi y me gustó"**: mezcla relevancia y posición.
- El LTR entrenado con clics crudos **aprende el sesgo**: su mayor peso fue la posición en producción.
- **IPS** pesa cada clic por 1/θ_k: 0.82 → **0.88** de nDCG@10.
- θ se **estima con intercambios**, a un costo mínimo, y rinde como la verdadera.
- **IPS corrige la posición, no la selección**: el 39% de los CVs muy relevantes nunca se muestra, y un modelo
  entrenado con lo mostrado aprende reglas que solo valen ahí (oráculo 0.90 contra 0.92 con todos los CVs).
- Más clics no mueven el resultado; **otros datos** sí: explorar, o etiquetas de lo que nadie mostró.
- Evalúa siempre también **contra tu conjunto etiquetado**, no solo contra clics.

Sigue con [`ejercicios.md`](ejercicios.md).
