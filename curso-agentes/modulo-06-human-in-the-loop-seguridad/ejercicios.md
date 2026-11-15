# Módulo 6 · Ejercicios

---

### Ejercicio 1 — Por qué el botón «Aprobar» no debe ser un trámite ciego
En `code/01_interrupt_aprobacion.py`, el humano puede elegir `"aprobar"`, `"editar"` o `"rechazar"`. ¿Qué información mínima debe mostrar la interfaz de aprobación a la reclutadora para evitar la *fatiga de alertas* (aprobar todo sin leer)?

<details>
<summary>Ver solución</summary>

No basta con mostrar `agendar_entrevista(vacante_id='VAC-101', candidato_id='CAND-01')`. La tarjeta de aprobación debe mostrar:
1. **Nombre, aspiración salarial vs. presupuesto** (`$6.200 / $6.500`).
2. **Resultado determinista de `verificar_elegibilidad`** (`motivos_bloqueo: []`).
3. **Diferencia exacta (*diff*)** de lo que cambiará en el sistema externo (fecha, hora y destinatario).
</details>

---

### Ejercicio 2 — Por qué un LLM con herramientas no debe resumir CVs directamente
Explica por qué separar el sistema en (a) un extractor sin herramientas que lee el texto libre del CV y emite un esquema cerrado, y (b) un agente planificador que solo ve el esquema cerrado, es el patrón estándar de seguridad (patrón *Dual-LLM* de Willison).

<details>
<summary>Ver solución</summary>

Porque el modelo (a) que está expuesto al texto hostil no tiene ninguna herramienta conectada (`tools=[]`), así que aunque el CV le ordene *"llama a enviar_oferta"*, es físicamente incapaz de invocar funciones. Y el modelo (b) que sí tiene herramientas solo recibe enteros, booleanos y listas de un catálogo cerrado (`anos_experiencia: 1`, `ingles: "A2"`), donde no cabe ninguna instrucción en lenguaje natural que pueda secuestrar su prompt.
</details>
