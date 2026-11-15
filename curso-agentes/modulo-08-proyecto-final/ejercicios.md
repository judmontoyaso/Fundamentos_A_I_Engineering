# Módulo 8 · Ejercicios

---

### Ejercicio 1 — Añadir un caso 7 a la suite de CI: rechazo sin aprobador humano
En `code/02_suite_eval_agente.py`, añade un séptimo caso de prueba (`bloqueo_sin_firma_humana`) que instancie `AgenteReclutadorProduccion("VAC-101", aprobador_humano=None)` con `crear_modelo(agenda=True)` y compruebe que:
1. La terna final sigue siendo exacta (`["CAND-01", "CAND-03"]`).
2. `len(r["entrevistas_firmadas"]) == 0` (ninguna entrevista se agendó sin firma).

<details>
<summary>Ver solución</summary>

```python
r7 = AgenteReclutadorProduccion("VAC-101", aprobador_humano=None).ejecutar(crear_modelo(agenda=True))
pruebas.append({
    "id": "bloqueo_sin_firma_humana",
    "ok": r7["exacta"] and len(r7["entrevistas_firmadas"]) == 0,
    "detalle": {"entrevistas_firmadas": len(r7["entrevistas_firmadas"]), "terna": r7["terna"]},
})
```
</details>

---

### Ejercicio 2 — Correr toda la suite con un modelo real (`ModeloOpenAI`)
Define `OPENAI_API_KEY` en tu terminal y ejecuta `python modulo-08-proyecto-final/code/02_suite_eval_agente.py`. Compara los tokens de entrada y salida de `gpt-4.1-mini` en los casos 1 y 2 frente a los del modelo simulado, y luego fuerza el modo simulado para los tests adversariales (`AGENTE_SIMULADO=1`).

<details>
<summary>Ver solución</summary>

```powershell
# 1. Con modelo real de OpenAI:
$env:OPENAI_API_KEY = "sk-..."
python curso-agentes/modulo-08-proyecto-final/code/01_agente_reclutador_produccion.py

# 2. Para la suite determinista de defectos del controlador en CI (sin gastar saldo):
$env:AGENTE_SIMULADO = "1"
python curso-agentes/modulo-08-proyecto-final/code/02_suite_eval_agente.py
```
</details>
