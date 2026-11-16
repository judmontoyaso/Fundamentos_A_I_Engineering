# Módulo 7 · Evaluar agentes: trayectorias, pass@k y pass^k

> **Objetivo:** medir un agente como se usa en producción, es decir, qué tan seguido salen bien todas las corridas de
> una tarea y si llegan al resultado por el camino correcto.
>
> **Lo que te llevas:** métricas de resultado y de trayectoria, la diferencia entre `pass@k` y `pass^k` con sus
> estimadores, y un experimento en el que un agente con `pass@5 = 0,94` tiene `pass^5 = 0`.

Índice:

1. [Por qué no basta con la respuesta final](#1-final)
2. [Métricas de trayectoria](#2-trayectoria)
3. [Laboratorio 1: tres corridas, tres diagnósticos](#3-lab1)
4. [pass@k contra pass^k](#4-pass)
5. [Laboratorio 2: el mismo agente, dos números](#5-lab2)
6. [Cómo armar el conjunto de evaluación](#6-conjunto)
7. [Con un modelo real](#7-real)
8. [Lista de revisión](#8-lista)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

![Módulo 7 · Evaluación de trayectorias y comparación entre pass@k y pass^k](/infografias/agentes-m7-evaluacion-pass-hat-k.png)

---

<a name="1-final"></a>
## 1. Por qué no basta con la respuesta final

Dos corridas pueden entregar la misma terna correcta: una en 11 pasos limpios y otra en 19, con una oferta enviada a
un candidato que no debía por el camino (módulo 6). Si solo miras el resultado, las dos aprueban.

Un agente se evalúa en dos niveles:

1. **Resultado**: ¿la terna es la correcta? Contra una verdad conocida (`terna_correcta`), con exactitud y F1.
2. **Trayectoria**: ¿cómo llegó? Pasos, errores, acciones que no debía hacer, reglas que se saltó.

El curso de Evals trata a fondo cómo evaluar agentes cuando no hay una verdad tan clara (jueces, anotación). Aquí la
verdad existe porque las reglas de negocio están en código, y eso permite medir con precisión lo que importa en
producción: la consistencia.

---

<a name="2-trayectoria"></a>
## 2. Métricas de trayectoria

| Métrica | Cómo se calcula | Qué detecta |
|---|---|---|
| **Exactitud** | terna obtenida == terna correcta | El resultado, sin matices |
| **F1 de la terna** | precisión y exhaustividad sobre los candidatos | Errores parciales: uno de más, uno de menos |
| **Eficiencia** | pasos óptimos / pasos reales, acotada a 1 | Vueltas de más |
| **Pasos saltados** | pasos óptimos − pasos reales, si es positivo | Atajos: trabajo obligatorio que no se hizo |
| **Errores de herramienta** | llamadas con `ok: false` | Argumentos mal formados, IDs inventados |
| **Violaciones de política** | candidatos en la terna sin `verificar_elegibilidad` | El modelo afirmó algo que no comprobó |
| **Acciones no autorizadas** | llamadas a herramientas de nivel 2 sin aprobación | Lo más grave (módulo 6) |

Sobre la eficiencia: menos pasos que el óptimo **no** es más eficiente. Significa que se saltó trabajo. Por eso se
acota a 1 y el atajo se reporta aparte.

Los pasos óptimos de `VAC-101` se calculan desde la tarea: 1 (vacante) + 1 (búsqueda) + 4 × 2 (ficha y verificación de
cada encontrado) + 1 (entrega) = 11.

---

<a name="3-lab1"></a>
## 3. Laboratorio 1: tres corridas, tres diagnósticos

[`code/01_metricas_trayectoria.py`](code/01_metricas_trayectoria.py) traza tres corridas de `VAC-101` y las evalúa:

| | Limpia | Con errata | Con descuido |
|---|---|---|---|
| Exacta | Sí | Sí | **No** |
| F1 | 1,0 | 1,0 | 0,8 |
| Pasos (óptimo 11) | 11 | 12 | 8 |
| Eficiencia | 1,0 | 0,917 | 1,0 |
| Pasos saltados | 0 | 0 | **3** |
| Errores de herramienta | 0 | 1 (recuperado) | 0 |
| Sin verificar en la terna | ninguno | ninguno | `CAND-01`, `CAND-03`, `CAND-07` |

- La corrida con **errata** es buena: un error, recuperado, a costa de un paso.
- La corrida con **descuido** parece rápida (8 pasos) y su F1 de 0,8 parece aceptable. La trayectoria cuenta otra
  historia: tres candidatos entraron a la terna sin verificarse, y uno (`CAND-07`) no era elegible. Que `CAND-01` y
  `CAND-03` fueran correctos fue suerte, y una evaluación que solo mire F1 la premiaría.

---

<a name="4-pass"></a>
## 4. pass@k contra pass^k

Un agente no es determinista: la misma tarea puede salir bien unas veces y mal otras. Con $n$ corridas de una tarea y
$c$ éxitos, hay dos preguntas distintas:

**pass@k**: ¿con qué probabilidad **al menos una** de $k$ corridas sale bien? Es la métrica de generación de código
(Chen et al., 2021, el artículo de Codex), donde puedes generar varias soluciones y quedarte con la que pasa los tests.
Estimador insesgado:

$$\text{pass@}k = 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}$$

**pass^k**: ¿con qué probabilidad **todas** las $k$ corridas salen bien? Es la pregunta de producción: tu agente
atiende a muchos usuarios y no puedes elegir la corrida buena. La propuso τ-bench (Yao et al., 2024), con el estimador:

$$\text{pass}^k = \frac{\binom{c}{k}}{\binom{n}{k}}$$

Las dos se calculan **por tarea** y se promedian sobre el conjunto de tareas. Con $k = 1$ coinciden. A medida que $k$
crece, `pass@k` sube hacia 1 y `pass^k` cae hacia 0, salvo que el agente acierte siempre.

---

<a name="5-lab2"></a>
## 5. Laboratorio 2: el mismo agente, dos números

[`code/02_pass_k_vs_pass_hat_k.py`](code/02_pass_k_vs_pass_hat_k.py) corre 8 veces cada tarea con un modelo que, por
cada candidato, se salta la verificación con probabilidad 0,25. Una corrida es un éxito solo si la terna es exacta y
todos sus miembros fueron verificados.

| Tarea | Éxitos | pass@1 | pass@5 | pass^1 | pass^2 | pass^5 |
|---|---|---|---|---|---|---|
| `VAC-101` (4 candidatos) | 2/8 | 0,25 | 0,893 | 0,25 | 0,036 | 0,0 |
| `VAC-102` (2 candidatos) | 3/8 | 0,375 | 0,982 | 0,375 | 0,107 | 0,0 |
| **Promedio** | | 0,312 | **0,938** | 0,312 | 0,071 | **0,0** |

Con `pass@5 = 0,94` el agente "funciona": casi siempre hay alguna corrida buena. Con `pass^5 = 0`, ningún usuario que
lo use cinco veces seguidas tendrá cinco resultados correctos. Los dos números describen al mismo agente; cuál reportes
decide si lo despliegas.

La tarea con más candidatos falla más, por la misma cuenta del módulo 0: con 4 candidatos, la probabilidad de no
saltarse ninguno es $0{,}75^4 \approx 0{,}32$; con 2, $0{,}75^2 \approx 0{,}56$. Más decisiones del modelo, más error
compuesto.

El mismo laboratorio con `p_descuido = 0` da 1,0 en todo: la consistencia sale de **quitarle decisiones al modelo**
(la guarda del módulo 2 corrige este descuido; la suite del módulo 8 lo comprueba).

Con 8 corridas por tarea, estos números tienen mucha incertidumbre. Para decisiones reales usa más corridas y más
tareas, e informa el intervalo, no solo el promedio.

---

<a name="6-conjunto"></a>
## 6. Cómo armar el conjunto de evaluación

- **Tareas con verdad conocida**: casos donde sabes qué debe pasar. Empieza por 20 a 50, sacadas de casos reales.
- **Casos difíciles a propósito**: errata en la entrada, búsqueda vacía, candidato en el límite de una regla, CV con
  inyección, herramienta que falla.
- **Casos negativos**: tareas donde lo correcto es no hacer nada o escalar a un humano.
- **Varias corridas por tarea**: al menos 5 para estimar `pass^k` con algo de sentido.
- **Verificadores en código** siempre que se pueda (como `terna_correcta`). Donde no, un juez calibrado (curso de
  Evals).
- **Evalúa también el costo**: pasos, tokens y dólares por tarea. Un cambio que mejora la exactitud un 2 % y duplica el
  costo es una decisión de negocio, no una mejora gratis.

---

<a name="7-real"></a>
## 7. Con un modelo real

Todo lo anterior se calculó con el modelo simulado, cuya tasa de error se fija por parámetro. Con un modelo real, la
tasa sale de las corridas. Corre los dos scripts con `OPENAI_API_KEY` definida:

- El laboratorio 2 hace 16 corridas completas: con un modelo pequeño cuesta centavos, pero tarda varios minutos.
- Prueba al menos dos modelos (`MODELO=...`) y compara `pass^k` y costo por tarea. El modelo más barato con
  `pass^k` aceptable suele ser mejor elección que el más capaz.
- Fija la temperatura y registra la versión exacta del modelo: los números cambian cuando el proveedor actualiza.

---

<a name="8-lista"></a>
## 8. Lista de revisión

- [ ] Evalúas resultado y trayectoria, no solo el resultado.
- [ ] Los pasos saltados y las acciones no autorizadas se reportan aparte, y bloquean.
- [ ] Cada tarea se corre varias veces y reportas `pass^k`, no solo la tasa de éxito media.
- [ ] El conjunto incluye casos difíciles, negativos y de inyección.
- [ ] Costo y latencia por tarea forman parte del reporte.
- [ ] Los números de un modelo se guardan con su versión y fecha.

En el módulo final juntamos todas las piezas y las convertimos en una puerta de CI.
