"""
02 · ¿Falló la recuperación o la respuesta? El sistema completo contra un oráculo (manual §5-§6).

Cada pregunta se responde dos veces:
  sistema : con los CVs que recuperó la búsqueda (lo que pasa en producción);
  oráculo : con los CVs relevantes, exactamente (la recuperación perfecta).
Con el oráculo, un fallo solo puede ser de la generación. Comparando las dos, cada pregunta del sistema
cae en una casilla: ok · falla la recuperación · falla la respuesta · acierta sin la recuperación completa.
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter
from importlib import import_module

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
pr = import_module("01_preguntas_y_recuperacion")
rag, ev = pr.rag, pr.ev

REPETICIONES = 2


def correcta(r, esperado: list[str], relevantes: list[int]) -> bool:
    if not relevantes:                                     # sin respuesta: debe abstenerse
        return r.sin_informacion
    texto = ev.norm(r.respuesta)
    return not r.sin_informacion and all(ev.norm(e) in texto for e in esperado)


def diagnostico(completos: bool | None, ok: bool) -> str:
    if completos is None:
        return "ok" if ok else "no se abstuvo"
    if ok:
        return "ok" if completos else "acierta sin recuperar todo"
    return "falla la respuesta" if completos else "falla la recuperación"


if __name__ == "__main__":
    recuperacion = pr.medir_recuperacion()
    casillas: Counter = Counter()
    oraculo_ok = sistema_ok = 0
    with ev.tz.nueva_traza("rag: sistema contra oráculo"):
        for vez in range(1, REPETICIONES + 1):
            def uno(args):
                (tipo, pregunta, relevantes, esperado), rec = args
                sis = rag.responder(pregunta, rec["top"])
                ora = rag.responder(pregunta, relevantes)
                return tipo, pregunta, rec, correcta(sis, esperado, relevantes), correcta(ora, esperado, relevantes), sis
            filas = ev.tz.en_paralelo(lambda a: uno(a), [((p, r),) for p, r in zip(pr.PREGUNTAS, recuperacion)])
            print(f"== Pasada {vez} ==")
            for tipo, pregunta, rec, s_ok, o_ok, sis in filas:
                d = diagnostico(rec["completos"], s_ok)
                casillas[d] += 1
                sistema_ok += s_ok
                oraculo_ok += o_ok
                if d != "ok" or not o_ok:
                    print(f"  {tipo:13} {d:27} oráculo {'✓' if o_ok else '✗'}  {pregunta}\n"
                          f"  {'':13} respuesta: {' '.join(sis.respuesta.split())[:120]}")
    n = len(pr.PREGUNTAS) * REPETICIONES
    print(f"\nRespuestas correctas · sistema {sistema_ok}/{n} ({sistema_ok / n:.0%}) · oráculo {oraculo_ok}/{n} "
          f"({oraculo_ok / n:.0%})")
    print("Casillas del sistema:", dict(casillas))
    print("La distancia entre el oráculo y el sistema es lo que cuesta la recuperación; lo que falla con el")
    print("oráculo es trabajo de la generación (prompt, modelo), y ahí cambiar la búsqueda no ayuda.")
