# Módulo 0 · Ejercicios

Intenta resolver cada ejercicio ejecutando y modificando los scripts de `code/` antes de desplegar la solución.

---

### Ejercicio 1. Calcular la caída de confiabilidad compuesta
Si un agente necesita dar 11 pasos de herramientas para preseleccionar `VAC-101` y tu modelo acierta cada decisión individual con probabilidad $p = 0.95$, ¿cuál es la probabilidad de que complete los 11 pasos sin ningún error? ¿Qué precisión por paso $p$ necesitarías para que la trayectoria completa de 11 pasos tenga al menos un **90 %** de éxito?

<details>
<summary>Ver solución</summary>

1. Con $p = 0.95$ y $n = 11$ pasos independientes:
   $$\text{Éxito}_{11} = 0.95^{11} \approx 0.5688 \text{ (56.9 \%)}$$
2. Para lograr $\text{Éxito}_{11} \ge 0.90$, despejamos $p$:
   $$p \ge 0.90^{1/11} \approx 0.9905 \text{ (99.05 \% por paso)}$$

Por eso en producción reducimos el número de pasos libres delegando las validaciones repetitivas a funciones deterministas o máquinas de estados.
</details>

---

### Ejercicio 2. Cortar por presupuesto en dólares (`max_costo_usd`)
En `code/02_presupuesto_y_frenos.py`, la ejecución sana de `VAC-101` consume `15.915` tokens de entrada y `224` de salida (`$0.006724 USD` a los precios por defecto de `$0.40 / $1.60` por millón). Añade un cuarto caso que simule el uso de un modelo grande de razonamiento (`precio_entrada_1m=10.0`, `precio_salida_1m=30.0`) con un techo de `max_costo_usd=0.05`. ¿En qué paso se dispara `PresupuestoAgotado`?

<details>
<summary>Ver solución</summary>

```python
presupuesto_caro = PresupuestoAgente(
    max_pasos=16,
    max_tokens=60_000,
    max_costo_usd=0.05,
    precio_entrada_1m=10.0,
    precio_salida_1m=30.0,
)
resultado = correr_con_presupuesto(crear_modelo(), "VAC-101", presupuesto_caro)
```

Con `$10 / 1M` de entrada, apenas la suma acumulada de `tokens_entrada` supera los `5.000` tokens (alrededor del **paso 5**), `costo_usd` rebasa `$0.05` y `registrar()` corta la corrida con `motivo_corte="max_costo_usd=0.05"`.
</details>

---

### Ejercicio 3. Calibrar el presupuesto con datos
Corre `bucle_agente` sobre las dos vacantes con el modelo normal y con `errata=True`. Anota pasos y tokens de cada
corrida. ¿Qué `max_pasos` y `max_tokens` pondrías para que ninguna corrida sana se corte y un bucle se corte pronto?

<details>
<summary>Ver solución</summary>

Las corridas sanas usan 7 a 12 pasos y hasta unos 17.000 tokens de entrada (la de errata, un paso más). Un límite de
16 pasos y 30.000 tokens deja margen a las sanas y corta un bucle en pocas vueltas. Con un conjunto real de tareas, el
criterio es el mismo: por encima del percentil 99 de las ejecuciones buenas. Revisa el límite cuando cambies de modelo
o añadas herramientas, porque la distribución cambia.
</details>

---

### Ejercicio 4. Workflow con un LLM dentro
Imagina que los CVs llegan en texto libre y hay que extraer años, inglés y habilidades. Diseña la solución en el nivel
más bajo de la escalera que funcione. ¿Cuántas llamadas al modelo hace por vacante?

<details>
<summary>Ver solución</summary>

Nivel 1 dentro de un workflow (nivel 2): una llamada de extracción estructurada por CV (texto → esquema validado con
Pydantic, como en el curso de AI Engineering) y después `motivos_bloqueo` en código. Son N llamadas para N CVs, sin
decisiones de flujo para el modelo, paralelizables y cacheables (un CV no cambia entre vacantes). Un agente solo se
justifica si además hay que decidir qué fuentes consultar según lo que se encuentre.
</details>

---

### Ejercicio 5. Detector de llamadas repetidas
Añade al bucle de `02_presupuesto_y_frenos.py` un detector: si el modelo repite una llamada idéntica (misma herramienta
y mismos argumentos) a otra que ya tuvo éxito, no la ejecutes y devuélvele un error que lo diga. Si lo hace 3 veces
seguidas, corta. Pruébalo con `terco=True`.

<details>
<summary>Ver solución</summary>

Guarda en un conjunto las huellas `clave_idempotencia(nombre, argumentos)` de las llamadas exitosas. Antes de ejecutar,
si la huella está, responde `{"ok": false, "codigo": "LLAMADA_DUPLICADA", "error": "Ya hiciste esta llamada; usa ese
resultado o cambia los argumentos."}` y suma uno a un contador de repeticiones seguidas (que vuelve a 0 con cualquier
llamada nueva). Con el modelo terco, la ejecución se corta por bucle en el paso 4, antes que el freno de `max_pasos`,
y el motivo queda claro en el reporte.
</details>
