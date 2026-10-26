# Módulo 0 · Qué vamos a mejorar, y con qué datos

> **Objetivo:** conocer el proyecto del curso y, sobre todo, los datos con los que se va a medir cada cambio: un
> corpus con la verdad conocida y unas consultas con la relevancia calculada.

Índice:

1. [Qué es este curso y qué no es](#1-que-es)
2. [El buscador, ahora con usuarios](#2-usuarios)
3. [El corpus: 119 CVs desde los hechos](#3-corpus)
4. [Las consultas: relevancia calculada, no opinada](#4-consultas)
5. [Antes de seguir: lo que deberías saber](#5-saber)

Código en [`code/`](code/).

---

<a name="1-que-es"></a>
## 1. Qué es este curso y qué no es

Es un curso sobre **mejorar** una búsqueda que ya funciona. No enseña a construir un RAG (eso fue el curso de AI
Engineering) ni a evaluar en general (el de Evals): usa los dos. Cada módulo tiene la misma forma: una pregunta sobre
el buscador, una medición, una técnica, otra medición, y una decisión: la técnica se queda o se quita.

No es un catálogo de técnicas. *Rerankers*, *late interaction*, *learning to rank* o contexto largo aparecen cuando una
medición dice que hacen falta, y se miden contra la alternativa simple.

---

<a name="2-usuarios"></a>
## 2. El buscador, ahora con usuarios

El buscador del curso de AI Engineering tenía 10 CVs y lo probaba quien lo escribió. Con usuarios reales cambian dos
cosas:

- **El corpus crece.** Con 10 CVs casi cualquier búsqueda acierta (el Módulo 2 de AI Engineering vio cinco modelos de
  embeddings empatados). Con 119, de 12 roles parecidos entre sí (ingeniero de datos, científico de datos, analista de
  datos), la búsqueda tiene que distinguir de verdad.
- **Las consultas se vuelven de personas.** No "Kubernetes", sino "alguien que automatice despliegues y administre
  contenedores", "k8s", "pyhton django", "más de 8 años en backend", "backend que no use Java", "senior data engineer".

---

<a name="3-corpus"></a>
## 3. El corpus: 119 CVs desde los hechos

[`comun/as_generar.py`](../comun/as_generar.py) aplica el método del Módulo 3 de Evals: primero los **hechos** en
código (rol, tecnologías, trabajos con empresa y años, ciudad, si acepta remoto, nivel de inglés, certificación), y
después un LLM que **redacta** el CV en prosa, viñetas o tabla, uno de cada siete en inglés. Cada CV se **valida** con
código (nombre, tecnologías, años de cada trabajo, ciudad y certificación deben estar en el texto). De 120, uno se
rechazó tras tres intentos: un CV en inglés al que el generador le tradujo las tecnologías. Quedan **119**.

Dos decisiones que importan para el resto del curso:

- **El nivel no está escrito en el CV.** Sale de los años (menos de 3, junior; de 3 a 6, semi-senior; 7 o más, senior).
  Una búsqueda "senior" tiene que inferirlo de las fechas: es un problema de entender la consulta (Módulo 2), no de
  parecido de textos.
- **Los hechos son la verdad, el texto es lo que ve el sistema.** Si un CV dice "2017–2019 y 2019–2021" en una tabla, el
  sistema tiene que leerlo de la tabla. El Módulo 3 mide cuánto se pierde ahí.

[`code/00_los_datos.py`](code/00_los_datos.py) muestra la distribución: 10 CVs por rol (9 en backend), 54 senior, 45
semi-senior y 20 junior, cinco ciudades, 35 que aceptan remoto y 15 con certificación.

---

<a name="4-consultas"></a>
## 4. Las consultas: relevancia calculada, no opinada

Las 41 consultas ([`comun/as_consultas.py`](../comun/as_consultas.py)) son de 12 tipos, elegidos por cómo pueden
fallar:

| Tipo | Ejemplo | Qué exige |
|---|---|---|
| Tecnología | "Kubernetes", "dbt" | La palabra exacta |
| Rol | "científico de datos" | El cargo |
| Paráfrasis | "alguien que automatice despliegues y administre contenedores" | El significado, sin palabras en común |
| Rol + nivel | "ingeniero de datos senior" | Inferir el nivel de los años |
| Rol + ciudad | "desarrollador backend en Medellín" | Un filtro |
| Rol + idioma | "analista de datos con inglés avanzado" | Un filtro con niveles (C1 o nativo) |
| Numérica | "más de 8 años de experiencia en desarrollo backend" | Contar años |
| Certificación | "ISO 27001 Lead Auditor" | Un dato concreto |
| Abreviatura | "k8s", "pyhton django" | Vocabulario y erratas |
| En inglés | "senior data engineer" | Cruzar idiomas |
| Liderazgo | "líder técnico de un equipo de datos" | Un cargo de liderazgo |
| Exclusión | "desarrollador backend que no use Java" | Excluir |

La relevancia de cada CV para cada consulta no la decide una persona leyendo: **la calcula una función sobre los
hechos**. Para "ingeniero de datos senior": 2 si el rol es ingeniero de datos y el nivel es senior; 1 si el rol coincide
pero el nivel no; 0 si no. Así se pueden medir métricas graduadas (nDCG, Módulo 1) sin que nadie lea 119 CVs por
consulta, y las reglas se pueden cambiar y recalcular.

Tiene un costo, y conviene decirlo: la relevancia calculada es tan buena como las reglas. "¿Un arquitecto cloud sirve
para 'alguien que automatice despliegues'?" se decidió que sí, con relevancia 1. Otra persona podría decir 0. Lo que
enseñó el Módulo 4 de Evals vale aquí: las reglas están escritas y se pueden discutir.

---

<a name="5-saber"></a>
## 5. Antes de seguir: lo que deberías saber

Este curso da por sabidos:

- **Del curso de AI Engineering:** búsqueda densa y BM25, RRF, chunking, RAG, reranking con LLM, agentes y
  observabilidad.
- **Del curso de Evals:** recall@k y MRR, repeticiones y ruido, desarrollo frente a holdout, la prueba de McNemar y que
  las mejoras del tamaño del ruido no cuentan.

Si alguno te suena lejano, repasa el módulo correspondiente antes de seguir.

---

## Resumen del módulo

- Este curso **mejora** una búsqueda que ya funciona, midiendo cada cambio.
- **119 CVs desde los hechos**, validados; el nivel **no** está escrito, sale de los años.
- **41 consultas de 12 tipos**, con relevancia graduada **calculada en código** desde los hechos.
- La relevancia calculada es tan buena como sus reglas, y las reglas están escritas.

Sigue con el [Módulo 1](../modulo-01-medir-antes/README.md).
