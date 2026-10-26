"""
00 · Los datos del curso: 119 CVs con sus hechos, 41 consultas con relevancia calculada (manual §3-§4).

Sin LLM. Cuenta el corpus por rol, nivel y ciudad; las consultas por tipo y cuántos CVs relevantes tiene
cada una, y muestra un CV con sus hechos, para ver la diferencia entre lo que el sistema LEE (el texto) y
lo que sabemos que es verdad (los hechos).
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
q = import_module("as_consultas")

if __name__ == "__main__":
    cvs = ac.cvs()
    h = [cv["hechos"] for cv in cvs]
    print(f"{len(cvs)} CVs")
    for campo in ("rol", "nivel", "ciudad", "ingles", "idioma", "estilo"):
        print(f"  {campo:8} {dict(Counter(str(x[campo]) for x in h).most_common())}")
    print(f"  remoto {sum(x['remoto'] for x in h)} · con certificación {sum(bool(x['certificacion']) for x in h)} · "
          f"lideran {sum(x['lidera'] for x in h)}")

    rels = q.relevancias(cvs)
    print(f"\n{len(q.CONSULTAS)} consultas · por tipo: {dict(Counter(t for t, _, _ in q.CONSULTAS))}")
    print(f"{'tipo':14} {'consulta':58} {'rel=2':>6} {'rel=1':>6}")
    for (tipo, texto, _), r in zip(q.CONSULTAS, rels):
        print(f"{tipo:14} {texto[:58]:58} {sum(v == 2 for v in r.values()):>6} {sum(v == 1 for v in r.values()):>6}")
    sin = [t for (_, t, _), r in zip(q.CONSULTAS, rels) if not any(v == 2 for v in r.values())]
    print(f"\nConsultas sin ningún CV con relevancia 2: {sin or 'ninguna'}")

    cv = cvs[1]
    print(f"\nEl CV #{cv['id']} tal como lo lee el sistema:\n  {' '.join(cv['texto'].split())}\nY sus hechos:\n  {cv['hechos']}")
