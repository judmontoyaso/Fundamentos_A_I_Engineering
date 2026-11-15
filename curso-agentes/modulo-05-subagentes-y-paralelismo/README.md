# Módulo 5 · Subagentes, delegación y ejecución paralela

> **Objetivo:** descomponer tareas intensivas en un patrón **Orquestador-Trabajadores** y **Map-Reduce** con ventanas de contexto aisladas y ejecución paralela controlada.

Cuando se habla de «sistemas multiagente» abundan demos teatrales donde un *Agente Director*, un *Agente Psicólogo* y un *Agente Crítico* conversan entre sí en un hilo interminable. En ingeniería de software en producción, dividir una tarea en varios agentes solo se justifica por **dos razones físicas medibles**:

1. **Aislamiento de la ventana de contexto**: si evaluar a fondo un candidato consume `200–4.000` tokens (leer su ficha detallada, historial y reglas de bloqueo), evaluar 8 candidatos en un mismo hilo contamina la ventana del agente principal. Si delegas cada candidato a un **subagente trabajador efímero**, cada trabajador procesa la ficha en una ventana limpia y devuelve al orquestador un **dictamen compacto de ~10 tokens** (`{"id": "CAND-01", "elegible": true}`).
2. **Reducción de latencia de reloj (*wall-clock time*)**: cuando las evaluaciones por candidato son independientes entre sí, ejecutarlas en paralelo reduce la latencia de $N \times t$ al tiempo del trabajador más lento ($\approx t$).

![Módulo 5 · Patrón Orquestador y Subagentes en paralelo con ventanas de contexto limpias](/infografias/agentes-m5-subagentes-map-reduce.png)

---

## 1. Patrón Orquestador-Trabajadores (`01_orquestador_trabajadores.py`)

En `code/01_orquestador_trabajadores.py`, el orquestador obtiene la vacante `VAC-101` y ejecuta la búsqueda inicial, que arroja 4 candidatos (`CAND-01`, `CAND-03`, `CAND-04`, `CAND-07`). En lugar de inspeccionar las 4 fichas dentro de su propio historial, delega cada candidato a `subagente_evaluador(vacante_id, candidato_id)` (simulando una latencia de red de `60 ms` por llamada al modelo):

| Modo de ejecución | Candidatos evaluados | Latencia total (`ms`) | Aceleración (*speedup*) | Tokens consumidos en trabajadores | Tokens que entran al orquestador | Terna final |
|---|---|---|---|---|---|---|
| **Secuencial (`paralelo=False`)** | 4 | `~242 ms` | `1.0x` | `792` | **`37`** | `["CAND-01", "CAND-03"]` |
| **Paralelo (`ThreadPoolExecutor`)** | 4 | `~62 ms` | **`3.9x`** | `792` | **`37`** | `["CAND-01", "CAND-03"]` |

Observa los dos números clave de la tabla:
- La latencia total cae casi 4 veces (`242 ms -> 62 ms`).
- De los `792` tokens procesados al inspeccionar las fichas completas en los trabajadores, **al contexto del orquestador solo llegan `37` tokens** (un ahorro del **95.3 %** en la ventana principal).

---

## 2. Map-Reduce sobre todo el ATS (`02_map_reduce_cvs.py`)

Cuando necesitamos cruzar un lote de vacantes (`VAC-101`, `VAC-102`) contra todos los candidatos de la base (`8` candidatos = `16` evaluaciones independientes), el patrón **Map-Reduce** elimina por completo el bucle secuencial:

1. **Fase `Map` (`fase_map_par`)**: un pool de trabajadores evalúa cada par `(vacante_id, candidato_id)` sin compartir estado mutable.
2. **Fase `Reduce` (`fase_reduce_por_vacante`)**: código determinista agrupa los veredictos por vacante, filtra `elegible == True`, ordena por menor `disponibilidad_dias` y menor `aspiracion_usd`, y verifica la coincidencia exacta con `terna_correcta(vid)`:
   - `VAC-101` → `#1 CAND-03` (`10 días`, `$5.900`) y `#2 CAND-01` (`15 días`, `$6.200`).
   - `VAC-102` → `#1 CAND-05` (`20 días`, `$6.900`).
