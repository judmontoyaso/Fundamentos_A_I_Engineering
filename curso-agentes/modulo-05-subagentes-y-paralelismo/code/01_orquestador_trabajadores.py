"""Patrón Orquestador-Trabajadores: aislamiento de ventana de contexto y ganancia de latencia en paralelo."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import ejecutar_herramienta_ats, herramientas_ats, imprimir, terna_correcta
from comun.ag_modelo import contar_tokens, crear_modelo


def subagente_evaluador(vacante_id: str, candidato_id: str, latencia_s: float = 0.06) -> dict:
    """Trabajador efímero: abre su propio contexto limpio, lee la ficha y verifica elegibilidad de UN candidato."""
    modelo = crear_modelo(latencia_s=latencia_s)
    esquemas = herramientas_ats("consultar_ficha_candidato", "verificar_elegibilidad")
    ficha = ejecutar_herramienta_ats("consultar_ficha_candidato", {"candidato_id": candidato_id})
    # El subagente hace una llamada al modelo con la ficha completa en su propio contexto aislado
    mensajes = [
        {"role": "system", "content": "Evalúa al candidato frente a la vacante usando verificar_elegibilidad."},
        {"role": "user", "content": f"Vacante {vacante_id}. Ficha: {json.dumps(ficha, ensure_ascii=False)}"},
    ]
    _ = modelo.responder(mensajes, esquemas)
    veredicto = ejecutar_herramienta_ats("verificar_elegibilidad", {"vacante_id": vacante_id, "candidato_id": candidato_id})
    tokens_locales = contar_tokens(mensajes) + contar_tokens(veredicto)
    # Al orquestador SOLO le devuelve el dictamen compacto (sin el CV crudo)
    return {
        "candidato_id": candidato_id,
        "elegible": bool(veredicto["elegible"]),
        "motivos_bloqueo": veredicto["motivos_bloqueo"],
        "tokens_consumidos_en_trabajador": tokens_locales,
    }


def ejecutar_orquestador(vacante_id: str, *, paralelo: bool) -> dict:
    t0 = time.perf_counter()
    vac = ejecutar_herramienta_ats("obtener_vacante", {"vacante_id": vacante_id})
    busq = ejecutar_herramienta_ats(
        "buscar_candidatos",
        {"habilidades": vac["requisitos_obligatorios"], "max_aspiracion_usd": vac["presupuesto_usd_mes"]},
    )
    ids = [c["id"] for c in busq["candidatos"]]

    if paralelo:
        with ThreadPoolExecutor(max_workers=len(ids)) as pool:
            dictamenes = list(pool.map(lambda cid: subagente_evaluador(vacante_id, cid), ids))
    else:
        dictamenes = [subagente_evaluador(vacante_id, cid) for cid in ids]

    elegibles = sorted(d["candidato_id"] for d in dictamenes if d["elegible"])
    resumen_orquestador = [{"id": d["candidato_id"], "elegible": d["elegible"]} for d in dictamenes]
    ms = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "modo": "paralelo_threadpool" if paralelo else "secuencial",
        "candidatos_evaluados": len(ids),
        "latencia_total_ms": ms,
        "tokens_en_trabajadores": sum(d["tokens_consumidos_en_trabajador"] for d in dictamenes),
        "tokens_recibidos_por_orquestador": contar_tokens(resumen_orquestador),
        "terna": elegibles,
        "exacta": elegibles == terna_correcta(vacante_id),
    }


if __name__ == "__main__":
    sec = ejecutar_orquestador("VAC-101", paralelo=False)
    par = ejecutar_orquestador("VAC-101", paralelo=True)
    aceleracion = round(sec["latencia_total_ms"] / max(par["latencia_total_ms"], 1.0), 2)
    imprimir("1. Ejecución secuencial de subagentes", sec)
    imprimir("2. Ejecución paralela de subagentes", {**par, "aceleracion_x": aceleracion})
