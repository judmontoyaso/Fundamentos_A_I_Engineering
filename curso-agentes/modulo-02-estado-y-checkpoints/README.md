# Módulo 2 · Máquinas de estados, checkpoints e idempotencia

Un bucle `ReAct` clásico guarda todo su estado como una lista de mensajes de chat en memoria RAM. En cuanto una llamada HTTP expira en el paso 5, el contenedor se reinicia o el proceso espera la respuesta de un reclutador humano durante dos horas, **todo el trabajo previo se pierde**. Peor aún: si reintentas desde cero, el agente puede volver a ejecutar efectos secundarios que ya habían ocurrido en los pasos 1 a 4.

---

## Separar el estado del historial de mensajes

En producción, el estado de un agente es una **estructura tipada y serializable** independiente del prompt de turno:

```python
@dataclass
class EstadoPreseleccion:
    ejecucion_id: str
    etapa: Literal["inicio", "vacante_cargada", "candidatos_filtrados", "verificados_ats", "listo_para_revision", "completado"]
    vacante_id: str
    candidatos_preseleccionados: list[str]
    verificaciones_ats: dict[str, dict]
    efectos_ejecutados: dict[str, Any]  # idempotency_key -> resultado
```

Cada vez que un nodo termina, el motor guarda un **checkpoint** atómico en base de datos o disco. Si el proceso cae en la etapa `verificados_ats`, al reanudar con el mismo `ejecucion_id` el agente continúa exactamente desde `verificados_ats` sin repetir las etapas anteriores.

---

## Idempotencia en herramientas con efectos secundarios

Las herramientas se dividen en dos categorías:

- **Lecturas puras (`GET`)**: `obtener_vacante`, `buscar_candidatos`. Se pueden repetir sin riesgo.
- **Mutaciones con efectos secundarios (`POST` / `UPDATE`)**: `registrar_nota_ats`, `reservar_slot_entrevista`, `enviar_correo`.

Para toda mutación, el runtime calcula una **clave de idempotencia** determinista a partir de `(ejecucion_id, herramienta, argumentos_canonicos)`. Si esa clave ya figura en `efectos_ejecutados`, el runtime devuelve el resultado almacenado sin volver a disparar el efecto externo.
