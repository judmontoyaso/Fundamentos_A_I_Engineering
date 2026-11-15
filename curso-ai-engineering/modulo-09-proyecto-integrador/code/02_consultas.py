"""
02 · Consultas por el grafo completo, cada una con su traza.

Cuatro pedidos de dos reclutadoras, en paralelo (cada consulta tarda varios segundos y
la celda tiene un límite de tiempo). La memoria de Ana se usa en su segundo pedido,
que se lanza después del primero para que el recuerdo ya exista.
"""
from __future__ import annotations
import pathlib
import sys
import time
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
S = import_module("00_sistema")
s = S.sistema()


def mostrar(r: dict, segundos: float | None = None):
    print(f"\n[{r['usuario']}] {r['pedido']}")
    if r["bloqueado"]:
        print(f"  BLOQUEADO -> {r['respuesta']}")
        return
    print(f"  recuerdos  : {r['recuerdos'] or 'ninguno'}")
    print(f"  candidatos : {[x['cv']['nombre'] for x in r['candidatos']]}")
    print(f"  puntajes   : {sorted(((e['puntaje'], e['nombre']) for e in r['evaluaciones']), reverse=True)}")
    print(f"  salida     : {r['estado_salida']}")
    print(f"  respuesta  : {r['respuesta']}")


if __name__ == "__main__":
    S.c.reiniciar_contador()
    t = time.time()
    primera = [("ana", "Para mis vacantes de datos exijo inglés avanzado. Busco a alguien senior para liderar un equipo "
                       "de datos en tiempo real."),
               ("bea", "Necesito un perfil de ciencia de datos con PyTorch."),
               ("bea", "Que sea menor de 30 años.")]
    resultados = S.tz.en_paralelo(s.consultar, primera, hilos=3)
    segunda = s.consultar("ana", "¿A quién me recomiendas para la vacante de datos?")   # después: usa su recuerdo
    for r in [*resultados, segunda]:
        mostrar(r)

    print(f"\n{S.c.resumen_costo('Costo: ')} · {time.time() - t:.1f} s de reloj")
    print(f"\n== Traza de la primera consulta de Ana ({resultados[0]['trace_id']}) ==")
    print(S.tz.arbol(resultados[0]["trace_id"]))
