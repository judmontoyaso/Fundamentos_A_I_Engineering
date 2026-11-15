# Módulo 2 · Máquinas de estados, checkpoints e idempotencia

> **Objetivo:** gobernar el bucle del agente con invariantes de estado que impidan saltarse verificaciones obligatorias, persistir checkpoints en disco para reanudar corridas interrumpidas y deduplicar efectos secundarios con claves de idempotencia.

En un bucle ReAct ingenuo, todo el estado del agente vive implícitamente dentro de la lista `mensajes` en memoria RAM. Ese diseño tiene tres fallas graves cuando pasa a producción:

1. **El modelo puede saltarse pasos obligatorios**: por prisa o alucinación, el LLM puede llamar a `entregar_terna` inmediatamente después de `buscar_candidatos`, sin haber llamado a `verificar_elegibilidad` para comprobar si el candidato está en enfriamiento o cumple el nivel de inglés.
2. **Cero tolerancia a fallos de proceso**: si el contenedor se reinicia en el paso 6 de 11, pierdes todos los tokens ya pagados y debes empezar desde el paso 1.
3. **Efectos secundarios duplicados**: si el agente ya había ejecutado `agendar_entrevista` para `CAND-01` antes del reinicio y reintenta la corrida, creará dos eventos duplicados en el calendario de la reclutadora.

![Módulo 2 · Máquina de estados, persistencia por checkpoint y claves de idempotencia](/infografias/agentes-m2-maquina-estados-checkpoints.png)

---

## 1. Máquina de estados e invariantes de transición (`01_maquina_de_estados.py`)

Las reglas de negocio críticas no se piden «por favor» en el system prompt: **se imponen como precondiciones en el despachador de herramientas**.

En `code/01_maquina_de_estados.py` definimos `EstadoPreseleccion`, que lleva el registro estructurado de qué vacante se cargó, qué candidatos devolvió la búsqueda y cuáles fueron pasados por `verificar_elegibilidad`:

```python
if herramienta == "entregar_terna":
    sin_verificar = [c for c in propuestos if c not in self.verificados]
    if sin_verificar:
        return f"Transición bloqueada: intentaste incluir {sin_verificar} sin llamar a verificar_elegibilidad."
```

Para probar su eficacia, ejecutamos el agente con `crear_modelo(p_descuido=1.0)` (un modelo negligente que da por elegibles a todos los candidatos devueltos por `buscar_candidatos` sin verificarlos):

| Configuración | Qué hace el modelo descuidado (`p_descuido=1.0`) | Respuesta del controlador | Terna final entregada | ¿Cumple reglas? |
|---|---|---|---|---|
| **Sin guarda (`usar_guarda=False`)** | Llama a `entregar_terna` con los 4 candidatos de la búsqueda | Acepta la llamada sin objetar | `["CAND-01", "CAND-03", "CAND-04", "CAND-07"]` | **No** (cuela a `CAND-04` con 1 año exp. e inyección, y a `CAND-07` en Medellín) |
| **Con guarda (`usar_guarda=True`)** | Intenta llamar a `entregar_terna` sin verificar | Bloquea el cierre prematuro, fuerza `verificar_elegibilidad` en los 4 y filtra no elegibles | `["CAND-01", "CAND-03"]` | **Sí** (`exacta: true`) |

---

## 2. Checkpoints atómicos e idempotencia (`02_checkpoints_e_idempotencia.py`)

Para que una ejecución larga pueda pausarse, caerse y reanudarse sin perder progreso ni repetir mutaciones externas, combinamos dos mecanismos en `code/02_checkpoints_e_idempotencia.py`:

### A. Persistencia de checkpoint paso a paso
Al terminar cada turno del bucle, `EjecutorConCheckpoint` serializa en `salida/m2_checkpoint.json` el diccionario completo de estado (`paso`, `mensajes`, `cache_idempotencia`, `completado`, `terna`).

### B. Clave de idempotencia determinista (`clave_idempotencia`)
Para cualquier llamada a herramienta, `comun/ag_comun.py` calcula un hash SHA-256 canónico sobre el nombre de la herramienta y sus argumentos ordenados:

```python
def clave_idempotencia(herramienta: str, argumentos: dict[str, Any]) -> str:
    cuerpo = json.dumps({"h": herramienta, "a": argumentos}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()[:16]
```

Si la clave ya existe en `estado["cache_idempotencia"]`, el controlador devuelve el resultado guardado **sin volver a invocar el sistema externo**.

Al correr `code/02_checkpoints_e_idempotencia.py` comprobamos los tres momentos:
1. **Caída simulada en el paso 6**: el proceso lanza `RuntimeError("Caída simulada del proceso en el paso 6")` tras haber guardado 6 pasos y sus resultados en `salida/m2_checkpoint.json`.
2. **Reanudación en caliente**: al invocar de nuevo `ejecutor.correr("VAC-101")`, lee el checkpoint del paso 6 y completa los pasos restantes hasta el paso 13 (`terna: ["CAND-01", "CAND-03"]`, 2 entrevistas agendadas).
3. **Deduplicación ante reintento**: al disparar de nuevo `agendar_entrevista` para `CAND-01` con la misma fecha, el caché de idempotencia intercepta la llamada (`reintento_duplicado_bloqueado_por_cache: true`) y el contador de entrevistas reales en el calendario permanece en `2`.
