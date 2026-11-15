# Módulo 1 · Diseño de herramientas y contratos poka-yoke

> **Objetivo:** diseñar esquemas de herramientas a prueba de errores (*poka-yoke*) con tipos restringidos, cotas explícitas y mensajes de error accionables que permitan al modelo autocorregirse en un solo turno.

La mayoría de los agentes que fallan en producción no fallan porque el LLM «no sepa razonar», sino porque **sus herramientas son un volcado directo de endpoints CRUD internos o consultas SQL**. Una API interna para desarrolladores asume que quien la invoca leyó la documentación una vez y conoce las tablas; un agente, en cambio, reconstruye su decisión en cada turno únicamente a partir de:

1. El nombre y la descripción de la función en el JSON Schema.
2. Las restricciones de tipos (`enum`, `minimum`, `maximum`, `additionalProperties: false`).
3. El texto o JSON que devolvió la herramienta en el turno anterior.

![Módulo 1 · Comparación entre una API CRUD cruda y una herramienta Poka-Yoke diseñada para LLMs](/infografias/agentes-m1-herramientas-poka-yoke.png)

---

## 1. Cinco reglas de diseño *Poka-Yoke* para herramientas de agentes

El término japonés *poka-yoke* significa «a prueba de errores inadvertidos»: diseñar la pieza para que sea imposible enchufarla al revés. Aplicado a herramientas de LLMs:

| Antipatrón frecuente (API cruda) | Diseño *Poka-Yoke* en `comun/ag_comun.py` | Por qué evita fallos del agente |
|---|---|---|
| `ejecutar_sql(query: str)` | `buscar_candidatos(habilidades: list[str], max_aspiracion_usd: int)` | Elimina errores de sintaxis SQL, inyecciones y volcados de tablas enteras |
| `vacante_id: str` libre | `"enum": ["VAC-101", "VAC-102"]` | El decodificador restringido impide inventar IDs como `"VAC-1"` o `"101"` |
| Tres llamadas separadas para ver salario, inglés y último contacto | `verificar_elegibilidad(vacante_id, candidato_id)` | Consolida la regla de negocio en una sola operación atómica |
| Devolver `[]` cuando una habilidad está mal escrita (`"Evaluacion de LLM"`) | Devolver `{"ok": False, "error": ..., "sugerencias": {"Evaluacion de LLM": ["Evaluación de LLMs"]}}` | Distingue entre *«no hay candidatos»* y *«escribiste mal el filtro»* |
| Volcar 120 columnas y logs internos | Devolver solo `{id, nombre, ciudad, aspiracion_usd, habilidades}` | Ahorra ~70 % de tokens de observación y evita contaminar la ventana |

---

## 2. Herramienta frágil frente a contrato Poka-Yoke (`01_herramienta_fragil_vs_poka_yoke.py`)

En `code/01_herramienta_fragil_vs_poka_yoke.py` ponemos a prueba el contrato `ESQUEMAS_HERRAMIENTAS` y el despachador `ejecutar_herramienta_ats` ante cuatro llamadas:

1. **Búsqueda válida (`["Python", "RAG"]`, `max_aspiracion_usd=6500`)**: devuelve exactamente los 4 candidatos que cumplen ambos criterios (`CAND-01`, `CAND-03`, `CAND-04`, `CAND-07`).
2. **Vacante inexistente (`"VAC-999"`)**: en vez de lanzar un `KeyError` que rompa el proceso, devuelve `{"ok": False, "error": "Vacante 'VAC-999' no encontrada.", "vacantes_validas": ["VAC-101", "VAC-102"]}`.
3. **Habilidad con errata (`"Evaluacion de LLM"` sin tilde ni plural)**: no devuelve una lista vacía engañosa; calcula la distancia de edición con `difflib.get_close_matches` contra `CATALOGO_HABILIDADES` y responde:
   ```json
   {
     "ok": false,
     "error": "Habilidades no reconocidas en el catálogo: ['Evaluacion de LLM'].",
     "sugerencias": { "Evaluacion de LLM": ["Evaluación de LLMs"] }
   }
   ```
4. **Presupuesto fuera de rango (`-50`)**: rechaza la llamada indicando la cota mínima (`>= 1000`).

---

## 3. Autocorrección gracias a errores accionables (`02_errores_accionables.py`)

¿Qué ocurre dentro del bucle del agente cuando el modelo comete una errata al invocar una herramienta? En `code/02_errores_accionables.py` corremos `crear_modelo(errata=True)` —que en su primera llamada a `buscar_candidatos` envía `"Evaluacion de LLM"`— bajo dos políticas de respuesta de error:

| Política de la herramienta | Turno 1 (`buscar_candidatos`) | Turno 2 del agente | Pasos totales | Terna final | ¿Acierta? |
|---|---|---|---|---|---|
| **Error opaco (`sugerir_en_error=False`)** | Devuelve `{"ok": False, "candidatos": []}` sin pistas | El agente asume que no existen candidatos y aborta | 3 | `[]` | **No** |
| **Error accionable (`sugerir_en_error=True`)** | Devuelve `sugerencias: {"Evaluacion de LLM": ["Evaluación de LLMs"]}` | El agente reemplaza el término por la sugerencia, halla los 4 candidatos y los verifica | 12 | `["CAND-01", "CAND-03"]` | **Sí** |

Un buen mensaje de error en una herramienta no está escrito para el log de Datadog: **está escrito como el prompt que necesita el modelo para corregir su siguiente llamada**.
