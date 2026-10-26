# Módulo 7 · Ejercicios

Intenta cada uno antes de ver la solución (al final, colapsadas). Los dos laboratorios corren sin llamadas nuevas al
LLM si ya corriste el Módulo 2 (los parseos están en caché). Para repetir un experimento varias veces, importa el
laboratorio y llama a `correr(semilla, ...)`: tiene parámetros para la θ de IPS y para cambiar los clics sin cambiar
la partición.

---

### Ejercicio 1 — Quita la feature de posición
Entrena los modelos sin `1/posicion_produccion`. Antes de correrlo, apuesta: ¿el ingenuo mejora o empeora? Después
mira sus pesos. ¿Dónde se fue el sesgo?

### Ejercicio 2 — Usuarios más o menos exigentes
Cambia la atracción de los no relevantes de 0.08 a 0.0 (nadie abre lo que no sirve) y después a 0.3 (un reclutador que
abre casi todo). ¿Cómo cambian el ingenuo y IPS?

### Ejercicio 3 — La varianza de IPS
Fija la partición 0 y cambia solo la semilla de los clics (`semilla_clics`), 20 veces, con 5 y con 60 sesiones por
consulta. Compara la desviación estándar del nDCG de IPS con la del ingenuo. ¿Por qué el rango entre **particiones**
no mostraba esta diferencia?

### Ejercicio 4 — Explorar al azar
Supón que en el 10% de las sesiones reemplazas el resultado 10 por un CV elegido al azar entre los puestos 11 y 40 de
producción. Sin correr nada, calcula: con 60 sesiones por consulta, ¿qué fracción de los CVs relevantes invisibles
recibe al menos un clic? Después impleméntalo y compruébalo.

### Ejercicio 5 — Recortar el peso
Un clic en la posición 10 pesa ~8 veces uno en la 1. Recorta la propensión: usa `max(θ_k, τ)` con τ = 0.2, 0.4 y 0.6.
¿Qué pasa con el nDCG de IPS? ¿Hacia qué modelo tiende cuando τ crece?

---

<details>
<summary><b>Soluciones</b></summary>

**1.** Contra lo que esperarías, **el ingenuo mejora mucho**: de 0.82 a **0.92**, por encima de IPS (0.87) y del oráculo
de los mostrados (0.90). El sesgo no desaparece: se va a las features **correlacionadas** con la posición, y BM25,
densa y MaxSim pasan a pesos positivos (0.026, 0.012, 0.026). El modelo ahora **imita a producción**, y eso es justo
lo que les falta a los modelos entrenados solo con los mostrados para ordenar a los ~109 CVs que nunca vieron (§6).
Con la feature de posición, en cambio, el sesgo se quedaba en una feature que no generaliza: fuera del top 10 la
posición en producción vale casi lo mismo para todos.

La lección no es "no corrijas el sesgo". Es que aquí el sesgo de **selección** pesa más que el de posición, y que un
modelo puede salir mejor por una razón accidental: si producción fuera mala, imitarla sería malo. Solo lo descubres
evaluando contra tu conjunto etiquetado.

**2.** Con 0.0, el ingenuo apenas cambia (0.82 → 0.83) y **IPS mejora** (0.875 → 0.888): menos clics en lo malo de
abajo, que IPS multiplicaba. Con 0.3 los dos empeoran y **IPS pierde más** (0.875 → 0.833, el ingenuo 0.824 → 0.801):
los clics en lo irrelevante de las posiciones bajas, pesados por 1/θ, son ruido amplificado. El sesgo está en **cuánto
se mira**; el ruido, en **cuánto se abre lo malo**, e IPS es sensible al segundo.

**3.** Con la partición fija:

| Sesiones | Ingenuo (desv.) | IPS (desv.) |
|---|---|---|
| 5 | 0.018 | **0.044** |
| 60 | 0.004 | **0.017** |

IPS tiene entre 2.5 y 4 veces la varianza del ingenuo. Entre particiones no se veía porque el rango lo domina **qué
consultas caen en la prueba** (de 0.58 a 0.76 ya en producción), no los clics. Para medir una fuente de varianza,
deja fijas las demás.

**4.** Cálculo: 10% de 60 sesiones son 6 sesiones de exploración por consulta, cada una con un CV de 30, así que cada
candidato aparece en promedio 0.2 veces. Con θ_10 ≈ 0.12 y atracción 0.8, la probabilidad de clic por aparición es
≈ 0.10. Resultado: alrededor del **2%** de los CVs relevantes invisibles recibe algún clic. Explorar al azar es casi
gratis para el reclutador (una posición baja en una de cada diez sesiones) y casi no compra nada. Se explora con
candidatos **prometedores** (los puestos 11 a 20, o aquellos en los que el modelo duda) y en posiciones donde se miran.

**5.**

| τ | nDCG@10 de IPS |
|---|---|
| sin recorte | 0.875 |
| **0.2** | **0.899** |
| 0.4 | 0.859 |
| 0.6 | 0.845 |

Un recorte suave **mejora** a IPS: con τ = 0.2, las posiciones 6 a 10 pesan como mucho unas 5 veces la 1 (en vez de hasta 8), y se pierde algo
de corrección a cambio de mucha menos varianza. Al subir τ, la θ se vuelve plana y el modelo tiende al **ingenuo**
(0.824). Es el compromiso sesgo-varianza en una sola perilla, y τ se elige igual que cualquier hiperparámetro: con
validación, nunca con la prueba.

</details>
