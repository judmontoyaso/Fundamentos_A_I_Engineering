"""Map-Reduce sobre el ATS completo: cruza todas las vacantes contra todos los candidatos en paralelo."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from comun.ag_comun import CANDIDATOS, VACANTES, ejecutar_herramienta_ats, imprimir, terna_correcta


def fase_map_par(tarea: tuple[str, str]) -> dict:
    """Fase MAP: evalúa un par (vacante_id, candidato_id) de forma independiente y sin estado compartido."""
    vac_id, cand_id = tarea
    ver = ejecutar_herramienta_ats("verificar_elegibilidad", {"vacante_id": vac_id, "candidato_id": cand_id})
    cand = CANDIDATOS[cand_id]
    return {
        "vacante_id": vac_id,
        "candidato_id": cand_id,
        "nombre": cand["nombre"],
        "aspiracion_usd": cand["aspiracion_usd"],
        "disponibilidad_dias": cand["disponibilidad_dias"],
        "elegible": ver["elegible"],
        "bloqueos": ver["motivos_bloqueo"],
    }


def fase_reduce_por_vacante(resultados_map: list[dict]) -> dict[str, dict]:
    """Fase REDUCE: agrupa por vacante, filtra elegibles y ordena por menor disponibilidad y aspiración."""
    salida: dict[str, dict] = {}
    for vid in sorted(VACANTES.keys()):
        evaluados = [r for r in resultados_map if r["vacante_id"] == vid]
        elegibles = sorted(
            [r for r in evaluados if r["elegible"]],
            key=lambda x: (x["disponibilidad_dias"], x["aspiracion_usd"]),
        )
        ids_elegibles = sorted(r["candidato_id"] for r in elegibles)
        salida[vid] = {
            "titulo": VACANTES[vid]["titulo"],
            "total_evaluados": len(evaluados),
            "ranking_elegibles": [
                {"id": r["candidato_id"], "nombre": r["nombre"], "usd": r["aspiracion_usd"], "dias": r["disponibilidad_dias"]}
                for r in elegibles
            ],
            "coincide_con_terna_correcta": ids_elegibles == terna_correcta(vid),
        }
    return salida


if __name__ == "__main__":
    pares = [(vid, cid) for vid in sorted(VACANTES.keys()) for cid in sorted(CANDIDATOS.keys())]
    with ThreadPoolExecutor(max_workers=8) as pool:
        mapeados = list(pool.map(fase_map_par, pares))
    reducido = fase_reduce_por_vacante(mapeados)
    imprimir(f"Map-Reduce completado ({len(pares)} evaluaciones independientes)", reducido)
