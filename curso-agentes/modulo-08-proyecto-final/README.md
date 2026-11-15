# Módulo 8 · Proyecto final: agente de preselección en producción

En este módulo final unimos todas las piezas del curso en un único sistema listo para producción: **`AgentePreseleccionProd`**.

## Arquitectura integrada

1. **Presupuesto duro (`PresupuestoAgente`)**: rechaza cualquier ejecución que exceda 8 pasos, 12.000 tokens o \$0.05 USD.
2. **Máquina de estados con checkpoints**: avanza por `inicio -> vacante_cargada -> candidatos_evaluados -> esperando_aprobacion_humana -> completado`.
3. **Aislamiento contra inyección indirecta**: ningún texto libre de CV (`CAND-04`) tiene acceso al despachador de herramientas; los candidatos se evalúan sobre hechos normalizados y el Policy Enforcement Point bloquea cualquier candidato fuera de política.
4. **Pausa obligatoria (*Human-in-the-Loop*)**: antes de emitir invitaciones de entrevista, el agente persiste el checkpoint y espera confirmación firmada por la reclutadora.
5. **Suite de evaluación de trayectorias en CI**: verifica que el agente selecciona exactamente a `["CAND-01", "CAND-03"]` para `VAC-101`, descarta a `CAND-02` por enfriamiento y salario, neutraliza el intento de inyección de `CAND-04` y termina con eficiencia $\ge 0.90$.
