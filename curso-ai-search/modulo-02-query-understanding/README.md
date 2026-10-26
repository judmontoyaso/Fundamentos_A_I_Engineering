# Módulo 2 · Query understanding y routing: qué busca de verdad el usuario

> **Objetivo:** convertir la consulta de un reclutador en lo que de verdad pide (un rol, un nivel, una ciudad, una
> exclusión) y usarlo para buscar: reescribir, filtrar duro o filtrar suave. Medido por tipo de consulta.
>
> **Lo que te llevas:** un parser de consultas con salida estructurada, cuatro estrategias comparadas contra la línea
> base (de 0.69 a 0.89 de nDCG@10) y la medida de lo que cuesta entender cada consulta.

Índice:

1. [Lo que el Módulo 1 dejó claro](#1-claro)
2. [El parser de consultas](#2-parser)
3. [Los metadatos del índice](#3-metadatos)
4. [Cuatro estrategias](#4-estrategias)
5. [Lo que pasó](#5-resultados)
6. [El precio de entender](#6-precio)
7. [Routing: ¿hace falta?](#7-routing)

Código en [`code/`](code/). Ejercicios en [`ejercicios.md`](ejercicios.md).

---

<a name="1-claro"></a>
## 1. Lo que el Módulo 1 dejó claro

Los peores fallos de la línea base no eran de similitud. "Desarrollador backend que no use Java" ponía primero a
quienes usan Java; "ingeniero de datos senior" traía analistas de datos; "alguien que automatice despliegues" traía
QA automation. Las consultas contienen **estructura** (un rol, un nivel, una negación, una ciudad) que un ranking por
parecido de textos no ve. Este módulo la extrae.

---

<a name="2-parser"></a>
## 2. El parser de consultas

[`comun/as_entender.py`](../comun/as_entender.py) convierte cada consulta en una `ConsultaEntendida` con salida
estructurada (el Módulo 1 de AI Engineering, aplicado a la consulta en vez de al documento):

| Campo | Ejemplo |
|---|---|
| `roles` | **todos** los roles del catálogo que encajan |
| `skills_requeridas`, `skills_excluidas` | "k8s" → `kubernetes`; "que no use Java" → excluida `java` |
| `nivel`, `anios_minimos`, `anios_maximos` | "senior" → senior, 7+; "recién egresado" → máximo 0 |
| `ciudad`, `remoto`, `ingles_minimo` | "avanzado" → C1 |
| `certificacion`, `lidera` | |
| `texto_busqueda` | la consulta reescrita para un buscador: en español, con el rol y las tecnologías, **sin negaciones** |

Algunas consultas, tal como las entendió:

- "alguien que automatice despliegues y administre contenedores" → `roles: [ingeniero devops]`, texto "Ingeniero DevOps
  que automatice despliegues…". El falso amigo "automat" desaparece.
- "senior data engineer" → `roles: [ingeniero de datos]`, `nivel: senior`, `anios_minimos: 7`, texto "ingeniero de
  datos". Traducido y con el nivel convertido en un filtro.
- "desarrollador backend que no use Java" → `skills_excluidas: [java]`, texto "desarrollador backend": la negación sale
  del texto, que es donde hacía daño, y pasa a un filtro.

---

<a name="3-metadatos"></a>
## 3. Los metadatos del índice

Para filtrar por rol, nivel o ciudad, el índice necesita esos datos **por CV**. No se copian de los hechos (en
producción nadie te los da): se **extraen del texto** una vez ([`comun/as_fichas.py`](../comun/as_fichas.py)), con la
técnica del Módulo 11 de Evals: el modelo copia trabajos y fechas, y los años y el nivel se calculan en código. Con
`gpt-6-luna` sobre estos CVs limpios, la extracción coincidió con los hechos en 119 de 119 en rol, años, nivel, ciudad,
remoto, inglés y skills, y en 118 de 119 en liderazgo. Con documentos reales no será así: el Módulo 3 lo mide.

---

<a name="4-estrategias"></a>
## 4. Cuatro estrategias

| Estrategia | Qué hace |
|---|---|
| **base** | La híbrida con el texto original (la línea base del Módulo 1) |
| **reescrita** | La híbrida con `texto_busqueda` |
| **filtros duros** | Solo los CVs que cumplen **todos** los filtros, ordenados por la híbrida reescrita. Si ninguno cumple, sin filtros |
| **filtros suaves** | Todos los CVs, ordenados primero por **cuántos** filtros cumplen y después por la híbrida reescrita |

La diferencia entre duros y suaves es la decisión central del módulo. Un filtro duro es exacto cuando acierta y
catastrófico cuando falla: si el parser o el índice se equivocan en un dato, el candidato correcto **desaparece**. Uno
suave deja a los que cumplen arriba y a los demás después, donde todavía se pueden encontrar.

---

<a name="5-resultados"></a>
## 5. Lo que pasó

[`code/01_entender_y_filtrar.py`](code/01_entender_y_filtrar.py), con el parser en `gpt-6-luna`:

| Tipo | base | reescrita | duros | **suaves** |
|---|---|---|---|---|
| Tecnología | 0.94 | 0.99 | 1.00 | 1.00 |
| Rol | 0.90 | 0.90 | 1.00 | 1.00 |
| Paráfrasis | 0.38 | 0.92 | 0.96 | **1.00** |
| Rol + nivel | 0.54 | 0.53 | 0.66 | 0.72 |
| Rol + ciudad | 0.56 | 0.72 | **0.54** | 0.86 |
| Rol + idioma | 0.75 | 0.67 | 0.71 | 0.87 |
| Numérica | 0.64 | 0.47 | 0.53 | 0.67 |
| Certificación | 0.90 | 0.75 | 0.76 | 0.92 |
| Abreviatura | 0.82 | 0.99 | 1.00 | 1.00 |
| En inglés | 0.44 | 0.71 | 0.87 | 0.91 |
| Liderazgo | 0.80 | 0.69 | 0.87 | 0.66 |
| Exclusión | 0.39 | 0.26 | 0.57 | 0.63 |
| **Total** | 0.69 | 0.78 | 0.84 | **0.89** |

(La base da 0.69 y no 0.68 porque aquí se ordenan los 119 CVs en vez de los 50 primeros.)

Contra la base, consulta a consulta:

| Estrategia | Gana | Pierde | Diferencia | IC 95 % |
|---|---|---|---|---|
| reescrita | 13 | 16 | +0.10 | [+0.01, +0.20] |
| duros | 19 | 11 | +0.15 | [+0.06, +0.26] |
| **suaves** | **26** | **3** | **+0.21** | **[+0.11, +0.30]** |

Lecturas:

- **Entender la consulta es la mejora más grande del curso hasta ahora**, y la primera cuyo intervalo no incluye el
  cero. Las paráfrasis, la abreviatura y el inglés quedan prácticamente resueltos.
- **Reescribir sola ayuda menos de lo que parece**: gana en 13 consultas y pierde en 16. Quitar "senior" del texto, por
  ejemplo, hace perder la señal sin poner otra en su lugar. Reescribir y filtrar van juntos.
- **Los filtros duros fallan por la taxonomía.** En "desarrollador backend en Medellín", el parser eligió solo el rol
  `desarrollador backend`; las reglas de relevancia consideran backend también a los desarrolladores Python y .NET. El
  filtro duro los eliminó y rol + ciudad bajó de 0.56 a 0.54. Con filtros suaves, quedaron detrás de los que cumplían
  todo, y el tipo subió a 0.86. **Un filtro duro convierte cualquier desacuerdo de taxonomía en un candidato perdido.**
- **Lo que no se arregla**: la exclusión (0.63) y la numérica (0.67) siguen siendo los tipos más bajos, por la misma
  taxonomía y porque "recién egresado de desarrollo" se reescribió como "perfil de desarrollo" sin ningún rol. Y en
  liderazgo, los suaves (0.66) quedaron por debajo de la base (0.80). La causa, leída en el ranking: para "líder técnico
  de un equipo de datos" el parser eligió `roles: ['otro']` en vez de los roles de datos. El único filtro útil quedó
  "lidera", que subió a líderes de **cualquier** rol (desarrolladores) por encima de los analistas de datos (0.89 → 0.46
  en esa consulta). La otra consulta de liderazgo, en cambio, mejoró (0.72 → 0.86). Un primer diagnóstico escrito para
  este manual culpaba a la ingesta; leer el ranking lo desmintió: el índice marcaba bien el liderazgo (118 de 119).

---

<a name="6-precio"></a>
## 6. El precio de entender

El parser es **una llamada al LLM en cada búsqueda**. [`code/02_parser_barato.py`](code/02_parser_barato.py) lo repite
sin caché con tres modelos:

| Parser | nDCG@10 (suaves) | Latencia p50 | p95 |
|---|---|---|---|
| `gpt-6-luna` | 0.90 | 3.7 s | 4.8 s |
| `gpt-4.1-mini` | 0.91 | 1.3 s | 1.9 s |
| `gpt-5.4-nano` | 0.90 | **1.1 s** | 1.6 s |

**Entender una consulta corta es una tarea fácil**: el modelo más barato rinde igual que el más capaz, con un tercio de
la latencia. Aun así, 1.1 s frente a los ~15 ms de la búsqueda sin parser es setenta veces más. Formas habituales de
pagarlo menos:

- **Caché por consulta normalizada**: los reclutadores repiten consultas ("kubernetes", "data engineer senior").
- **Atajos sin LLM** para lo trivial: una consulta de una sola palabra que coincide con una tecnología del índice no
  necesita parser.
- **Mostrar primero y refinar después**: los resultados de la base en 15 ms y, cuando llega el parser, los
  reordenados.

---

<a name="7-routing"></a>
## 7. Routing: ¿hace falta?

El Módulo 1 sugería **enrutar**: cada tipo de consulta pedía un modo distinto (BM25 para tecnologías, densa para
paráfrasis). Con el parser, esa necesidad casi desaparece: la reescritura convierte las paráfrasis en consultas con el
nombre del rol, que BM25 y la híbrida resuelven bien, y los filtros resuelven el resto. Enrutar entre modos de búsqueda
sería otra decisión que puede fallar, para ganar poco.

El routing que sí aparece es otro: **qué consultas no son de búsqueda**. "¿Cuántos candidatos senior hay en Cali?" o
"¿quién tiene más años de experiencia?" no piden un ranking, piden una cuenta o un máximo. Para esas, el parser ya tiene
todo lo necesario (los filtros) y la respuesta es una consulta sobre las fichas, no un ranking. Es el Módulo 6.

---

## Resumen del módulo

- Las consultas tienen **estructura** (rol, nivel, ciudad, exclusión) que el parecido de textos no ve: extráela con un
  **parser** con salida estructurada.
- Pide **todos los roles que encajan**, y saca las negaciones del texto: van a filtros.
- **Filtros suaves** (ordenar por cuántos se cumplen) > duros: 0.89 contra 0.84; gana en 26 consultas y pierde en 3
  frente a la base (0.69).
- Un **filtro duro** convierte cualquier desacuerdo de taxonomía o error del índice en un candidato **perdido**.
- Un **parser barato** rinde igual (0.90) con un tercio de la latencia; aun así cuesta ~1 s por consulta: cachea y usa
  atajos.
- El routing útil no es entre modos de búsqueda, sino entre **buscar y contar** (Módulo 6).

Sigue con [`ejercicios.md`](ejercicios.md).
