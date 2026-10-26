"""
03 · Afinar el embedder con pares sintéticos, y la trampa de evaluarlo (manual §5-§6).

Se entrena MiniLM con pares (consulta, CV) generados por plantillas DESDE LOS HECHOS, con plantillas DISTINTAS a
las del set de prueba ("perfil de {rol}", "{skill} y {skill}", "{rol} con experiencia en {skill}"...).
Pérdida: MultipleNegativesRankingLoss (los otros CVs del lote hacen de negativos). Una época, en CPU.
Se evalúa la búsqueda densa antes y después, en dos condiciones:
  - los mismos 119 CVs con los que se entrenó (lo que hace casi todo el mundo, y engaña);
  - un HOLDOUT: se entrena sin los CVs de 4 roles y se evalúa solo en las consultas de esos roles.
El modelo afinado se guarda en salida/minilm_afinado (no se sube al repositorio).
"""
from __future__ import annotations
import os
import pathlib
import random
import sys
from importlib import import_module
from statistics import mean

import numpy as np

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
bs = import_module("as_buscador")
q = import_module("as_consultas")

BASE = os.getenv("EMB_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
ROLES_FUERA = {"analista de seguridad", "desarrollador móvil", "qa automation", "arquitecto cloud"}


def pares(cvs: list[dict], rnd: random.Random) -> list[tuple[str, str]]:
    out = []
    for cv in cvs:
        h = cv["hechos"]
        s = h["skills"]
        plantillas = [f"perfil de {h['rol']}", f"{rnd.choice(s)} y {rnd.choice(s)}",
                      f"{h['rol']} con experiencia en {rnd.choice(s)}", f"candidato de {h['ciudad']} que sepa {rnd.choice(s)}"]
        out += [(p, cv["texto"]) for p in plantillas]
    rnd.shuffle(out)
    return out


def entrenar(cvs: list[dict], destino: pathlib.Path, lote: int = 16, escala: float = 20.0):
    """La pérdida contrastiva a mano (la de MultipleNegativesRankingLoss): en un lote de pares (consulta, CV), cada
    consulta debe parecerse más a SU CV que a los otros CVs del lote. Una época."""
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(7)
    m = SentenceTransformer(BASE)
    m.train()
    opt = torch.optim.AdamW(m.parameters(), lr=2e-5)
    datos = pares(cvs, random.Random(7))
    for k in range(0, len(datos) - lote + 1, lote):
        a, b = zip(*datos[k:k + lote])
        ea = torch.nn.functional.normalize(m(m.preprocess(list(a)))["sentence_embedding"], dim=1)
        eb = torch.nn.functional.normalize(m(m.preprocess(list(b)))["sentence_embedding"], dim=1)
        perdida = torch.nn.functional.cross_entropy(escala * ea @ eb.T, torch.arange(len(a)))
        opt.zero_grad()
        perdida.backward()
        opt.step()
    m.eval()
    m.save(str(destino))
    return m


def ndcg_densa(modelo, cvs: list[dict], consultas, rels) -> list[float]:
    ids = [cv["id"] for cv in cvs]
    docs = modelo.encode([cv["texto"] for cv in cvs], normalize_embeddings=True)
    out = []
    for (_, texto, _), rel in zip(consultas, rels):
        qv = modelo.encode([texto], normalize_embeddings=True)[0]
        out.append(bs.ndcg([ids[i] for i in np.argsort(-(docs @ qv))], rel))
    return out


if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer
    cvs = ac.cvs()
    rels = q.relevancias(cvs)
    base = SentenceTransformer(BASE)
    print("1) Entrenar y evaluar con los mismos 119 CVs")
    afinado = entrenar(cvs, ac.SALIDA / "minilm_afinado")
    a, b = ndcg_densa(base, cvs, q.CONSULTAS, rels), ndcg_densa(afinado, cvs, q.CONSULTAS, rels)
    print(f"   densa base {mean(a):.2f} -> afinada {mean(b):.2f} (41 consultas)")

    print("2) Holdout: entrenar SIN los CVs de 4 roles; evaluar en las consultas cuyos relevantes son de esos roles")
    dentro = [cv for cv in cvs if cv["hechos"]["rol"] not in ROLES_FUERA]
    afinado_h = entrenar(dentro, ac.SALIDA / "minilm_afinado_holdout")
    hechos = {cv["id"]: cv["hechos"] for cv in cvs}
    sel = [k for k, rel in enumerate(rels) if rel and all(hechos[i]["rol"] in ROLES_FUERA for i, r in rel.items() if r == 2)]
    cons = [q.CONSULTAS[k] for k in sel]
    rs = [rels[k] for k in sel]
    a, b = ndcg_densa(base, cvs, cons, rs), ndcg_densa(afinado_h, cvs, cons, rs)
    print(f"   {len(cons)} consultas de roles que el entrenamiento no vio: densa base {mean(a):.2f} -> afinada {mean(b):.2f}")
    for c, x, y in zip(cons, a, b):
        print(f"     {c[1][:55]:55} {x:.2f} -> {y:.2f}")
