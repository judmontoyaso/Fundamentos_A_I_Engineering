"""
db.py — persistencia en SQLite (se crea sola la primera vez).

Guarda:
  - progress: qué notebooks marcaste como leídos.
  - cell_edits: el código que editaste en una celda (para no perderlo).
  - runs: historial de ejecuciones (opcional, útil para depurar).
  - annotations: etiquetas que pusiste en una tarea de anotación (curso de Evals, Módulo 4).
"""
from __future__ import annotations
import os
import sqlite3
import threading
from pathlib import Path

# DB_PATH del entorno, o backend/data/curso.db
DB_PATH = Path(os.getenv("DB_PATH") or Path(__file__).resolve().parents[1] / "data" / "curso.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_local = threading.local()


def _conn() -> sqlite3.Connection:
    c = getattr(_local, "conn", None)
    if c is None:
        c = sqlite3.connect(DB_PATH)
        c.row_factory = sqlite3.Row
        _local.conn = c
    return c


def init() -> None:
    c = _conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS progress (
            nb_id TEXT PRIMARY KEY,
            done  INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cell_edits (
            nb_id    TEXT NOT NULL,
            cell_idx INTEGER NOT NULL,
            source   TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (nb_id, cell_idx)
        );
        CREATE TABLE IF NOT EXISTS annotations (
            nb_id    TEXT NOT NULL,
            item_id  TEXT NOT NULL,
            anotador TEXT NOT NULL,
            label    INTEGER NOT NULL,
            nota     TEXT NOT NULL DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (nb_id, item_id, anotador)
        );
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nb_id TEXT, cell_idx INTEGER, ok INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )
    c.commit()


# ---- progreso ----
def get_progress() -> dict[str, bool]:
    rows = _conn().execute("SELECT nb_id, done FROM progress").fetchall()
    return {r["nb_id"]: bool(r["done"]) for r in rows}


def set_progress(nb_id: str, done: bool) -> None:
    c = _conn()
    c.execute(
        "INSERT INTO progress (nb_id, done, updated_at) VALUES (?, ?, datetime('now')) "
        "ON CONFLICT(nb_id) DO UPDATE SET done=excluded.done, updated_at=datetime('now')",
        (nb_id, 1 if done else 0),
    )
    c.commit()


# ---- ediciones de celdas ----
def get_edits(nb_id: str) -> dict[int, str]:
    rows = _conn().execute(
        "SELECT cell_idx, source FROM cell_edits WHERE nb_id=?", (nb_id,)
    ).fetchall()
    return {r["cell_idx"]: r["source"] for r in rows}


def save_edit(nb_id: str, cell_idx: int, source: str) -> None:
    c = _conn()
    c.execute(
        "INSERT INTO cell_edits (nb_id, cell_idx, source, updated_at) "
        "VALUES (?, ?, ?, datetime('now')) "
        "ON CONFLICT(nb_id, cell_idx) DO UPDATE SET source=excluded.source, updated_at=datetime('now')",
        (nb_id, cell_idx, source),
    )
    c.commit()


def clear_edit(nb_id: str, cell_idx: int) -> None:
    c = _conn()
    c.execute("DELETE FROM cell_edits WHERE nb_id=? AND cell_idx=?", (nb_id, cell_idx))
    c.commit()


def log_run(nb_id: str, cell_idx: int, ok: bool) -> None:
    c = _conn()
    c.execute("INSERT INTO runs (nb_id, cell_idx, ok) VALUES (?, ?, ?)",
              (nb_id, cell_idx, 1 if ok else 0))
    c.commit()


# ---- anotaciones ----
def get_annotations(nb_id: str, anotador: str) -> dict[str, dict]:
    rows = _conn().execute(
        "SELECT item_id, label, nota FROM annotations WHERE nb_id=? AND anotador=?", (nb_id, anotador)
    ).fetchall()
    return {r["item_id"]: {"label": bool(r["label"]), "nota": r["nota"]} for r in rows}


def save_annotation(nb_id: str, item_id: str, anotador: str, label: bool, nota: str) -> None:
    c = _conn()
    c.execute(
        "INSERT INTO annotations (nb_id, item_id, anotador, label, nota, updated_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now')) "
        "ON CONFLICT(nb_id, item_id, anotador) DO UPDATE SET label=excluded.label, nota=excluded.nota, "
        "updated_at=datetime('now')",
        (nb_id, item_id, anotador, 1 if label else 0, nota),
    )
    c.commit()


def clear_annotation(nb_id: str, item_id: str, anotador: str) -> None:
    c = _conn()
    c.execute("DELETE FROM annotations WHERE nb_id=? AND item_id=? AND anotador=?", (nb_id, item_id, anotador))
    c.commit()
