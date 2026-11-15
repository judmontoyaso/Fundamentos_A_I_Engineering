# Módulo 3 · Presupuesto de contexto, poda y memoria

En un chat convencional el usuario escribe mensajes cortos. En un agente, **cada llamada a una herramienta inyecta cientos o miles de tokens de observación** (JSONs de candidatos, historiales del ATS, fragmentos de documentos). Al cabo de 10 pasos:

- Pagas los tokens de las observaciones del paso 1 en los pasos 2, 3, 4... hasta el 10 (crecimiento cuadrático en tokens facturados: $\sum_{i=1}^{N} T_i$).
- El modelo sufre degradación en la mitad del contexto (*lost in the middle*) y empieza a confundir atributos de un candidato descartado en el paso 2 con el candidato final del paso 9.

![Módulo 3 · Presupuesto de contexto, poda de observaciones (observation masking) y memoria episódica](/infografias/agentes-m3-poda-contexto-memoria.png)

---

## Tres técnicas de higiene de contexto

1. **Poda de observaciones antiguas (*observation masking*)**:
   - Conserva íntegras las observaciones de los últimos $K=2$ pasos.
   - Reemplaza el cuerpo voluminoso de las observaciones más antiguas por un puntero compacto (`"[Observación de buscar_candidatos archivada en estado: 4 candidatos procesados]"`) mientras los hechos extraídos viven en el diccionario de estado.
2. **Compactación estructurada (cuaderno de trabajo / *scratchpad*)**:
   - En lugar de resumir en prosa libre (donde se pierden IDs exactos o cifras salariales), actualiza una tabla o estructura JSON de `hallazgos_confirmados`.
3. **Memoria episódica entre ejecuciones**:
   - Guarda lecciones operativas verificadas (p. ej., *"Para la vacante VAC-101 el gerente de contratación prioriza experiencia real en evaluación de LLMs sobre años totales"*) en una tabla indexada por entidad (`vacante_id` o `cliente_id`) y recupérala al iniciar una nueva corrida.
