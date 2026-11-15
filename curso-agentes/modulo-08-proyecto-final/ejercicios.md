# Ejercicios · Módulo 8

## Ejercicio 1: Agregar una restricción de disponibilidad inmediata

El gerente de la vacante `VAC-101` pide priorizar a quienes tengan `disponibilidad_dias <= 20`. Modifica el agente final (`code/01_agente_reclutador_prod.py`) para que incluya el puntaje de disponibilidad en el dictamen y verifica que la suite de evaluación (`code/02_suite_eval_agente.py`) siga pasando al 100 %.

<details>
<summary>Solución comentada</summary>

Tanto `CAND-01` (15 días) como `CAND-03` (10 días) cumplen `disponibilidad_dias <= 20`, con `CAND-03` ganando un bono de rapidez de incorporación. Al añadir el campo `disponibilidad_dias` al dictamen estructurado, la reclutadora recibe la recomendación ordenada junto con la evidencia exacta antes de aprobar el envío de invitaciones.

</details>
