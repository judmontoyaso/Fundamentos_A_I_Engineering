"""
01 · Un set con la respuesta conocida para calibrar al juez, separado en desarrollo y prueba (manual §2-§3).

Pregunta del juez: ¿el perfil INVENTA algo que el CV no dice?
  - Los 30 perfiles reales del Módulo 2, con la etiqueta del autor (4 inventan: #5, #6, #15, #16).
  - 26 copias de los perfiles que no inventan, con una invención INSERTADA por código: obvia (una
    certificación), sutil (liderazgo, una tecnología, un idioma) o numérica (los años cambiados).
    Su etiqueta es "inventa" por construcción.
Se separa POR CV (un CV y su copia van juntos) en desarrollo (para mejorar el prompt del juez) y prueba
(para medirlo una sola vez al final). Sin LLM.
"""
from __future__ import annotations
import json
import pathlib
import random
import re
import sys
from collections import Counter
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")
autor = import_module("m4_etiquetas_autor").AUTOR

INVENTA_AUTOR = {"5", "6", "15", "16"}          # los "perfil inventa" del Módulo 2
TECNOLOGIAS = ["Kubernetes", "Snowflake", "Terraform", "Salesforce", "Rust", "Tableau", "Kafka", "Angular"]
INVENCIONES = {
    "obvia": ["Certificado como AWS Solutions Architect Professional.", "Ganó el premio a la innovación de su empresa en 2022.",
              "Certificación PMP vigente.", "Publicó dos artículos en conferencias internacionales."],
    "sutil": ["Lideró un equipo de cinco personas.", "Con nivel de inglés C1.", "Con experiencia adicional en {tec}.",
              "Coordinó la migración de la plataforma a la nube."],
}


def _insertar(perfil: str, cv: str, tipo: str, rnd: random.Random) -> str | None:
    if tipo == "numérica":
        m = re.search(r"\b(\d{1,2}) años\b", perfil)
        return perfil.replace(m.group(0), f"{int(m.group(1)) + 3} años", 1) if m else None
    frase = rnd.choice(INVENCIONES[tipo])
    if "{tec}" in frase:
        libres = [t for t in TECNOLOGIAS if t.lower() not in cv.lower()]
        frase = frase.format(tec=rnd.choice(libres))
    return perfil.rstrip(". ") + ". " + frase


def construir(semilla: int = 11) -> list[dict]:
    filas = [json.loads(l) for l in (ev.COMUN / "m2_salidas_revisadas.jsonl").read_text(encoding="utf-8").splitlines()]
    rnd = random.Random(semilla)
    items = []
    tipos = ["obvia", "sutil", "sutil", "numérica"]           # una de cada cuatro copias es obvia...
    k = 0
    for f in filas:
        cid = str(f["id"])
        cv = " ".join(f["texto"].split())
        items.append({"item": f"{cid}", "cv_id": cid, "cv": cv, "perfil": f["perfil"],
                      "inventa": cid in INVENTA_AUTOR, "origen": "real"})
        if cid not in INVENTA_AUTOR:
            tipo = tipos[k % len(tipos)]
            k += 1
            nuevo = _insertar(f["perfil"], cv, tipo, rnd)
            if nuevo is None:                                  # el perfil no dice "N años": va una sutil
                tipo, nuevo = "sutil", _insertar(f["perfil"], cv, "sutil", rnd)
            items.append({"item": f"{cid}+", "cv_id": cid, "cv": cv, "perfil": nuevo, "inventa": True,
                          "origen": f"insertada {tipo}"})
    return items


def separar(items: list[dict], semilla: int = 11) -> tuple[list[dict], list[dict]]:
    ids = sorted({it["cv_id"] for it in items}, key=int)
    random.Random(semilla).shuffle(ids)
    dev = set(ids[: len(ids) // 2])
    return [it for it in items if it["cv_id"] in dev], [it for it in items if it["cv_id"] not in dev]


if __name__ == "__main__":
    items = construir()
    dev, test = separar(items)
    print(f"{len(items)} ítems · {sum(it['inventa'] for it in items)} inventan · "
          f"{sum(not it['inventa'] for it in items)} no inventan")
    print("Por origen:", dict(Counter(it["origen"] for it in items)))
    for nombre, parte in (("desarrollo", dev), ("prueba", test)):
        print(f"  {nombre:10} {len(parte)} ítems · {sum(it['inventa'] for it in parte)} inventan · "
              f"CVs {sorted({it['cv_id'] for it in parte}, key=int)}")
    ejemplo = next(it for it in items if it["origen"] == "insertada sutil")
    print(f"\nEjemplo ({ejemplo['item']}, {ejemplo['origen']}):\n  {ejemplo['perfil']}")
