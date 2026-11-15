# Módulo 1 · Diseño de herramientas y contratos poka-yoke

La mayoría de los agentes que fallan en producción no fallan porque el modelo sea incapaz de razonar, sino porque **sus herramientas son un espejo crudo de endpoints internos o consultas SQL**. Una API pensada para un desarrollador humano asume que quien la llama leyó la documentación una vez y recuerda los códigos numéricos. Un LLM, en cambio, decide en cada turno a partir del nombre de la herramienta, las descripciones de los parámetros y las observaciones previas.

---

## Cinco reglas para diseñar herramientas para agentes

1. **Agrupa operaciones atómicas de negocio, no endpoints CRUD de bajo nivel**:
   - *Mal*: `obtener_usuario_id(email)`, `obtener_historial_entrevistas(uid)`, `obtener_banda_salarial(uid)` como tres herramientas separadas cuando siempre se consultan juntas.
   - *Bien*: `consultar_ficha_candidato(identificador)` que acepta `CAND-01` o el correo y devuelve el resumen consolidado.
2. **Usa tipos restringidos (`Literal` / `Enum`) y nombres autoexplicativos**:
   - En lugar de `modo: int` (`1`, `2`, `3`), usa `modalidad: Literal["remoto", "hibrido", "presencial"]`.
3. **Diseño *poka-yoke* (a prueba de errores)**:
   - Si una ruta de archivo debe ser absoluta o un ID debe tener el prefijo `VAC-`, normalízalo o valídalo con un mensaje claro antes de tocar la base de datos.
4. **Recorta y estructura la salida de la herramienta**:
   - Nunca devuelvas un JSON crudo de 40 KB con 120 columnas internas. Devuelve los 6 campos relevantes y un indicador `total_encontrados` + `mostrando_primeros` para que el modelo sepa si debe paginar o refinar.
5. **Errores accionables orientados al modelo**:
   - Un stacktrace `KeyError: 'VAC-99'` solo confunde al LLM. Devuelve `{"ok": False, "error": "La vacante 'VAC-99' no existe.", "vacantes_activas": ["VAC-101", "VAC-102"]}`: le ahorras un turno entero de adivinanza.
