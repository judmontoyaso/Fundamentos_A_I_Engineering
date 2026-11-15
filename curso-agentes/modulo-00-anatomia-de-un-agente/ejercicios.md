# Módulo 0 · Ejercicios

Intenta resolver cada ejercicio ejecutando y modificando los scripts de `code/` antes de desplegar la solución.

---

### Ejercicio 1 — Calcular la caída de confiabilidad compuesta
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

### Ejercicio 2 — Cortar por presupuesto en dólares (`max_costo_usd`)
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
