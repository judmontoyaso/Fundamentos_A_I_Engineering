"""
content.py — carga los módulos del curso y los convierte en 'notebooks'.

Dos tipos de notebook:
  - De lectura (manual / ejercicios): la prosa se renderiza como Markdown y los
    bloques de código son FRAGMENTOS ilustrativos (editables y copiables, pero no
    ejecutables: muchos son incompletos a propósito).
  - Laboratorio: los scripts completos de la carpeta code/ de cada módulo, como
    celdas EJECUTABLES de principio a fin, más una celda en blanco para experimentar.

No reescribe tus archivos: los lee tal cual.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path

# Raíz del curso: COURSE_ROOT del entorno, o la carpeta REA/ (tres niveles arriba
# de app/backend/curso_api/).
COURSE_ROOT = Path(os.getenv("COURSE_ROOT") or Path(__file__).resolve().parents[3])

_MODULO_DIR = re.compile(r"^modulo-(\d+)-")


def _titulo(readme: Path, numero: int) -> str:
    """Primer encabezado '# ...' del README del módulo, o 'Módulo N'."""
    for line in readme.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return f"Módulo {numero}"


def cursos() -> list[dict]:
    """El curso de AI Engineering vive en la raíz (carpetas modulo-*); cada carpeta curso-*/ con README.md
    es otro curso con la misma estructura. Los ids del primero no llevan prefijo, para conservar el progreso."""
    lista = [{"id": "ai-engineering", "dir": COURSE_ROOT, "prefijo": "",
              "titulo": _titulo(COURSE_ROOT / "README.md", 0)}]
    for carpeta in sorted(COURSE_ROOT.glob("curso-*")):
        if (carpeta / "README.md").exists():
            slug = carpeta.name.removeprefix("curso-")
            lista.append({"id": slug, "dir": carpeta, "prefijo": f"{slug}-",
                          "titulo": _titulo(carpeta / "README.md", 0)})
    return lista


def modules() -> list[dict]:
    """Navegación descubierta en disco: en cada curso, cada carpeta modulo-NN-* con README.md es un módulo.
    Se recalcula en cada llamada, así que un módulo nuevo aparece sin reiniciar la API.
      type "md"   -> archivo Markdown (fragmentos NO ejecutables)
      type "lab"  -> carpeta code/ (scripts completos, SÍ ejecutables)
      type "quiz" -> autoevaluacion.json del módulo (preguntas con corrección y explicación)
      type "app"  -> el asistente del Módulo 9 funcionando (no cuenta para el progreso)
    Las rutas de "file" y "dir" son relativas a COURSE_ROOT."""
    grupos = []
    for curso in cursos():
        base, pre = curso["dir"], curso["prefijo"]
        rel = "" if base == COURSE_ROOT else f"{base.name}/"
        grupos.append({"course": curso["id"], "group": "Inicio", "items": [
            {"id": f"{pre}inicio", "title": "Presentación del curso", "type": "md", "file": f"{rel}README.md"}]})
        for carpeta in sorted(base.glob("modulo-*")):
            m = _MODULO_DIR.match(carpeta.name)
            if not m or not (carpeta / "README.md").exists():
                continue
            n = int(m.group(1))
            ruta = f"{rel}{carpeta.name}"
            items = [{"id": f"{pre}m{n}-manual", "title": "Manual", "type": "md", "file": f"{ruta}/README.md"}]
            if (carpeta / "ejercicios.md").exists():
                items.append({"id": f"{pre}m{n}-ejercicios", "title": "Ejercicios", "type": "md",
                              "file": f"{ruta}/ejercicios.md"})
            if any((carpeta / "code").glob("*.py")):
                items.append({"id": f"{pre}m{n}-lab", "title": "Laboratorio (código ejecutable)", "type": "lab",
                              "dir": f"{ruta}/code"})
            if (carpeta / "autoevaluacion.json").exists():
                items.append({"id": f"{pre}m{n}-quiz", "title": "Autoevaluación", "type": "quiz",
                              "file": f"{ruta}/autoevaluacion.json"})
            if not pre and n == 9 and (carpeta / "code" / "00_sistema.py").exists():
                items.append({"id": "asistente", "title": "Asistente de selección (en vivo)", "type": "app"})
            grupos.append({"course": curso["id"], "group": _titulo(carpeta / "README.md", n), "items": items})
    return grupos


def _item(nb_id: str) -> dict | None:
    return next((it for g in modules() for it in g["items"] if it["id"] == nb_id), None)

# Captura bloques cercados ```lang\n...\n```
_FENCE = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)


def nav_tree() -> list[dict]:
    return [
        {"course": g["course"], "group": g["group"],
         "items": [{"id": it["id"], "title": it["title"], "type": it["type"]} for it in g["items"]]}
        for g in modules()
    ]


def _split_md_cells(md: str) -> list[dict]:
    """Markdown -> celdas: prosa (md) y código como FRAGMENTO (no ejecutable)."""
    cells: list[dict] = []
    pos = idx = 0
    for m in _FENCE.finditer(md):
        before = md[pos:m.start()].strip("\n")
        if before.strip():
            cells.append({"idx": idx, "type": "md", "lang": "md", "source": before})
            idx += 1
        lang = (m.group(1) or "").strip().lower()
        cells.append({
            "idx": idx, "type": "code", "lang": lang or "text",
            "runnable": False, "fragment": True, "source": m.group(2).rstrip("\n"),
        })
        idx += 1
        pos = m.end()
    tail = md[pos:].strip("\n")
    if tail.strip():
        cells.append({"idx": idx, "type": "md", "lang": "md", "source": tail})
    return cells


def _first_docstring(code: str) -> str:
    """Primera línea útil del docstring del script, para describir la celda."""
    m = re.search(r'"""(.*?)"""', code, re.DOTALL)
    if not m:
        return ""
    for line in m.group(1).strip().splitlines():
        if line.strip():
            return line.strip()
    return ""


def _lab_cells(code_dir: Path) -> list[dict]:
    """Scripts .py de code/ -> celdas ejecutables, en orden alfabético."""
    cells: list[dict] = []
    idx = 0
    cells.append({"idx": idx, "type": "md", "lang": "md", "source":
                  "# Laboratorio\n\nCada script completo del módulo, listo para **ejecutar** "
                  "(▶ o `Ctrl/Cmd+Enter`). Las celdas comparten variables: corre de arriba "
                  "hacia abajo. Necesitas las dependencias del módulo instaladas y, para los "
                  "ejemplos con LLM, tus API keys en el entorno."})
    idx += 1
    for py in sorted(code_dir.glob("*.py")):
        code = py.read_text(encoding="utf-8")
        desc = _first_docstring(code)
        header = f"#### `{py.name}`"
        if desc:
            header += f"\n\n{desc}"
        cells.append({"idx": idx, "type": "md", "lang": "md", "source": header})
        idx += 1
        cells.append({"idx": idx, "type": "code", "lang": "python",
                      "runnable": True, "fragment": False, "source": code, "file": str(py)})
        idx += 1
    cells.append({"idx": idx, "type": "md", "lang": "md", "source":
                  "#### Celda libre\n\nTu espacio para experimentar. Lo que definas arriba está "
                  "disponible aquí."})
    idx += 1
    cells.append({"idx": idx, "type": "code", "lang": "python", "runnable": True,
                  "fragment": False, "source": "# Tu código aquí\n"})
    return cells


def notebook(nb_id: str) -> dict | None:
    item = _item(nb_id)
    if not item:
        return None
    if item["type"] == "lab":
        code_dir = COURSE_ROOT / item["dir"]
        if not code_dir.exists():
            return {"id": nb_id, "title": item["title"], "cells": [
                {"idx": 0, "type": "md", "lang": "md", "source": f"> No se encontró `{item['dir']}`."}]}
        return {"id": nb_id, "title": item["title"], "cells": _lab_cells(code_dir)}

    path = COURSE_ROOT / item["file"]
    if not path.exists():
        return {"id": nb_id, "title": item["title"], "cells": [
            {"idx": 0, "type": "md", "lang": "md", "source": f"> No se encontró `{item['file']}`."}]}
    return {"id": nb_id, "title": item["title"], "cells": _split_md_cells(path.read_text(encoding="utf-8"))}


def quiz(nb_id: str) -> dict | None:
    """Preguntas de autoevaluación. Se mandan con la respuesta y la explicación: es para estudiar, no un examen."""
    item = _item(nb_id)
    if not item or item["type"] != "quiz":
        return None
    datos = json.loads((COURSE_ROOT / item["file"]).read_text(encoding="utf-8"))
    return {"id": nb_id, "title": item["title"], "preguntas": datos["preguntas"]}


def exists(nb_id: str) -> bool:
    return _item(nb_id) is not None
