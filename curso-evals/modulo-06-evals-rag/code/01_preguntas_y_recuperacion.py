"""
01 · Un set de preguntas con su respuesta Y sus CVs relevantes, y la recuperación medida sola (manual §2-§4).

Cada pregunta tiene: los CVs que hay que recuperar (relevantes) y lo que la respuesta debe contener.
Aquí solo se mide la mitad de recuperación (sin LLM): recall@k y si están TODOS los relevantes en el top k.
Tipos: dato de un candidato · búsqueda por tecnología · paráfrasis · agregación · sin respuesta.
"""
from __future__ import annotations
import pathlib
import sys
from collections import defaultdict
from importlib import import_module

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
rag = import_module("ev_rag")
ev = rag.ev

# (tipo, pregunta, CVs relevantes, lo que la respuesta debe contener)
PREGUNTAS = [
    ("dato", "¿Cuántos años de experiencia tiene Laura Gómez?", [1], ["9"]),
    ("dato", "¿Qué correo tiene Óscar Lindo?", [24], ["oscar.lindo@gmail.com"]),
    ("dato", "¿Con qué tecnologías trabaja Camilo Herrera?", [4], ["c#", ".net", "sql server"]),
    ("dato", "¿En qué empresa trabaja Lucía Torres?", [19], ["northwind"]),
    ("dato", "¿Cuánto tiempo trabajó Daniela Peña como desarrolladora?", [20], ["18"]),
    ("dato", "¿Qué norma ISO maneja Sofía León?", [5], ["9001"]),
    ("tecnología", "¿Quién sabe Terraform?", [2], ["diego ruiz"]),
    ("tecnología", "¿Quién trabaja con Kotlin?", [14], ["carolina ramos"]),
    ("tecnología", "¿Quién tiene experiencia con Airflow?", [19], ["lucia torres"]),
    ("tecnología", "¿Quiénes trabajan con PyTorch?", [15, 21], ["mateo giraldo", "valentina cruz"]),
    ("tecnología", "¿Quién maneja SAP?", [17], ["isabel moreno"]),
    ("tecnología", "¿Quién sabe Selenium?", [13], ["felipe duarte"]),
    ("paráfrasis", "¿Quién se dedica a la infraestructura como código en la nube?", [2], ["diego ruiz"]),
    ("paráfrasis", "¿Quién hace pruebas automatizadas de software?", [13], ["felipe duarte"]),
    ("paráfrasis", "¿Quién administra bases de datos?", [11], ["ricardo salas"]),
    ("paráfrasis", "¿Quién diseña interfaces y estudia a los usuarios?", [10], ["natalia ortiz"]),
    ("agregación", "¿Quién tiene más años de experiencia de todos los candidatos?", [6], ["andres pardo"]),
    ("agregación", "¿Cuántos candidatos trabajan con Python?", [1, 8, 12, 20, 21, 25, 29], ["7"]),
    ("sin respuesta", "¿Quién habla japonés?", [], []),
    ("sin respuesta", "¿Quién tiene experiencia con COBOL?", [], []),
]
K = 3


def medir_recuperacion(k: int = K) -> list[dict]:
    filas = []
    for tipo, pregunta, relevantes, _ in PREGUNTAS:
        top = rag.buscar(pregunta, k)
        if relevantes:
            recall = len(set(top) & set(relevantes)) / len(relevantes)
            completos = set(relevantes) <= set(top)
        else:
            recall, completos = None, None
        filas.append({"tipo": tipo, "pregunta": pregunta, "relevantes": relevantes, "top": top,
                      "recall": recall, "completos": completos})
    return filas


if __name__ == "__main__":
    filas = medir_recuperacion()
    por_tipo = defaultdict(list)
    print(f"{len(PREGUNTAS)} preguntas · top {K} con búsqueda híbrida (densa + BM25, RRF)\n")
    for f in filas:
        estado = "—" if f["recall"] is None else f"{f['recall']:.0%}"
        print(f"  {f['tipo']:13} recall@{K} {estado:>4}  relevantes {f['relevantes']} · top {f['top']}  {f['pregunta']}")
        if f["recall"] is not None:
            por_tipo[f["tipo"]].append(f["recall"])
    print("\nRecall medio por tipo:", {t: f"{sum(v) / len(v):.0%}" for t, v in por_tipo.items()})
    print("Con k = 3 es IMPOSIBLE recuperar los 7 CVs con Python: la agregación falla antes de llegar al LLM.")
