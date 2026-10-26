"""
02 · Un índice que cambia todos los días, y una persona que pide que la borren (manual §5-§7).

1. VEINTE DÍAS DE CAMBIOS: el índice empieza con 100 CVs. Cada día llega un CV nuevo, se actualizan uno o dos (el
   candidato añade una tecnología) y, a veces, alguien retira su autorización y hay que borrarlo. Tres formas de
   mantener el índice:
     nocturna            : se reconstruye todo cada noche; de día se busca en el índice de anoche
     nocturna + borrados : igual, pero los borrados se filtran al buscar desde el momento en que se piden
     incremental         : cada cambio se aplica al momento (un embedding por CV nuevo o cambiado, BM25 se rehace)
   Después de cada cambio se corren las 41 consultas y se comparan con un índice construido desde cero con el estado
   real. Se mide: embeddings calculados, páginas que muestran a alguien ya borrado y páginas distintas a la verdad.
2. EL INVENTARIO: ¿en cuántos sitios del sistema está la primera persona que pidió que la borraran? Se recorren las
   salidas del curso, las bases de la app y los documentos, contando (sin borrar nada).
"""
from __future__ import annotations
import hashlib
import pathlib
import random
import sqlite3
import sys
from importlib import import_module

import numpy as np

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ac = import_module("as_comun")
q = import_module("as_consultas")
ev = ac.ev

DIAS = 20
SKILLS_NUEVAS = ["kafka", "dbt", "kubernetes", "pytorch", "airflow", "terraform", "react", "spark"]
_vectores: dict[str, np.ndarray] = {}           # memo por hash de texto: solo para que el lab corra rápido


def huella(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def vector(texto: str) -> np.ndarray:
    h = huella(texto)
    if h not in _vectores:
        v = ac.embed([texto])[0]
        _vectores[h] = v / np.linalg.norm(v)
    return _vectores[h]


class Indice:
    """Vectores por id (con la huella del texto que se indexó) y un BM25 sobre esos mismos textos."""

    def __init__(self):
        self.vec: dict[int, np.ndarray] = {}
        self.huella: dict[int, str] = {}
        self.ids_bm25: list[int] = []
        self.bm25 = None
        self.borrados: set[int] = set()           # filtro al buscar (lista de borrados pendientes)
        self.embeddings = 0

    def poner(self, i: int, texto: str):
        if self.huella.get(i) != huella(texto):  # solo se re-embebe si el texto cambió
            self.vec[i] = vector(texto)
            self.huella[i] = huella(texto)
            self.embeddings += 1

    def quitar(self, i: int):
        self.vec.pop(i, None)
        self.huella.pop(i, None)

    def rehacer_bm25(self, textos: dict[int, str]):
        self.ids_bm25 = [i for i in self.vec]
        self.bm25 = ac.bm25.BM25([textos[i] for i in self.ids_bm25])

    def reconstruir(self, textos: dict[int, str]):
        self.vec, self.huella, self.borrados = {}, {}, set()
        for i, t in textos.items():
            self.poner(i, t)
        self.rehacer_bm25(textos)

    def buscar(self, qv: np.ndarray, texto: str) -> list[int]:
        ids = [i for i in self.vec if i not in self.borrados]
        dens = sorted(ids, key=lambda i: -float(self.vec[i] @ qv))
        lex = [self.ids_bm25[j] for j, _ in self.bm25.buscar(texto, len(self.ids_bm25))]
        lex = [i for i in lex if i not in self.borrados]
        puntos: dict[int, float] = {}
        for r in (dens, lex):
            for p, i in enumerate(r, 1):
                puntos[i] = puntos.get(i, 0.0) + 1 / (60 + p)
        return sorted(puntos, key=lambda i: -puntos[i])[:10]


def eventos(rnd: random.Random, vivos: list[int], pendientes: list[int]) -> list[list[tuple[str, int]]]:
    vivos, pendientes, dias = list(vivos), list(pendientes), []
    for _ in range(DIAS):
        dia = []
        if pendientes:
            i = pendientes.pop()
            dia.append(("nuevo", i))
            vivos.append(i)
        for i in rnd.sample(vivos, rnd.choice([1, 2])):
            dia.append(("actualiza", i))
        if rnd.random() < 0.4:
            i = rnd.choice(vivos)
            dia.append(("borra", i))
            vivos.remove(i)
        dias.append(dia)                          # en orden: llega, se actualiza, se borra
    return dias


def inventario(cv: dict) -> list[tuple[str, int | str]]:
    """Cuántas veces aparece el nombre de la persona en cada almacén. No borra nada."""
    nombre = ev.norm(cv["hechos"]["nombre"])
    contar = lambda texto: ev.norm(texto).count(nombre)
    filas = []
    raices = [ac.SALIDA, ac.RAIZ / "curso-evals" / "salida", ac.RAIZ / "app" / "backend" / "data", ac.COMUN]
    for raiz in raices:
        if not raiz.exists():
            continue
        for p in sorted(raiz.rglob("*")):
            if not p.is_file():
                continue
            n = 0
            if p.suffix == ".db":
                with sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True) as con:
                    for (tabla,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                        for fila in con.execute(f'SELECT * FROM "{tabla}"'):
                            n += sum(contar(v) for v in fila if isinstance(v, str))
            elif p.suffix in (".json", ".jsonl", ".txt", ".md"):
                n = contar(p.read_text(encoding="utf-8", errors="ignore"))
            elif p.suffix == ".pdf":
                import pymupdf
                with pymupdf.open(p) as doc:
                    n = sum(contar(pg.get_text()) for pg in doc)
                    if not n and p.stem == str(cv["id"]) and not "".join(pg.get_text() for pg in doc).strip():
                        n = "escaneado: el nombre está en la imagen; solo lo encuentra el id del archivo"
            if n:
                filas.append((str(p.relative_to(ac.RAIZ)).replace("\\", "/"), n))
    return filas


if __name__ == "__main__":
    rnd = random.Random(3)
    cvs = {cv["id"]: cv for cv in ac.cvs()}
    orden = list(cvs)
    rnd.shuffle(orden)
    iniciales, pendientes = orden[:100], orden[100:]
    textos = {i: cvs[i]["texto"] for i in iniciales}          # el estado real
    dias = eventos(rnd, iniciales, pendientes)
    consultas = [t for _, t, _ in q.CONSULTAS]
    qvs = ac.embed(consultas)
    qvs = qvs / np.linalg.norm(qvs, axis=1, keepdims=True)

    formas = {"nocturna": Indice(), "nocturna + borrados": Indice(), "incremental": Indice()}
    for ix in formas.values():
        ix.reconstruir(textos)
        ix.embeddings = 0                                     # el arranque no cuenta: es igual para las tres
    stats = {f: {"borrado servido": 0, "distinta": 0} for f in formas}
    paginas = 0
    borrados_total: list[int] = []
    for d, dia in enumerate(dias, 1):
        for tipo, i in dia:
            if tipo == "nuevo":
                textos[i] = cvs[i]["texto"]
            elif tipo == "actualiza":
                textos[i] += f"\nActualización (día {d}): ahora también trabaja con {rnd.choice(SKILLS_NUEVAS)}."
            else:
                del textos[i]
                borrados_total.append(i)
                formas["nocturna + borrados"].borrados.add(i)
            inc = formas["incremental"]
            if tipo == "borra":
                inc.quitar(i)
            else:
                inc.poner(i, textos[i])
            inc.rehacer_bm25(textos)
            verdad = Indice()
            verdad.reconstruir(textos)
            for qv, texto in zip(qvs, consultas):
                v = verdad.buscar(qv, texto)
                paginas += 1
                for f, ix in formas.items():
                    pag = ix.buscar(qv, texto)
                    stats[f]["borrado servido"] += any(i not in textos for i in pag)
                    stats[f]["distinta"] += pag != v
        for f in ("nocturna", "nocturna + borrados"):
            formas[f].reconstruir(textos)                     # la noche

    n_ev = sum(len(x) for x in dias)
    print(f"{DIAS} días · {n_ev} cambios ({sum(t == 'nuevo' for x in dias for t, _ in x)} nuevos, "
          f"{sum(t == 'actualiza' for x in dias for t, _ in x)} actualizaciones, {len(borrados_total)} borrados) · "
          f"{paginas} páginas comparadas con la verdad")
    print(f"\n{'':22} {'embeddings':>11} {'muestra a un borrado':>21} {'página distinta':>16}")
    for f, ix in formas.items():
        s = stats[f]
        print(f"{f:22} {ix.embeddings:>11} {s['borrado servido'] / paginas:>20.1%} {s['distinta'] / paginas:>15.1%}")

    primero = cvs[borrados_total[0]]
    print(f"\nInventario de la primera persona que pidió que la borraran (CV {primero['id']}):")
    filas = inventario(primero)
    for ruta, n in filas:
        print(f"  {n:>4} × {ruta}" if isinstance(n, int) else f"     · {ruta} ({n})")
    print(f"  {len(filas)} archivos. Además, sin poder contarse: los pesos de los modelos afinados con su texto "
          f"(salida/minilm_afinado*), y lo que ya se envió al proveedor del LLM.")
