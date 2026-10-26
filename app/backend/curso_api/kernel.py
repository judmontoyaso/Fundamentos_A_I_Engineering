"""
kernel.py — ejecución de celdas estilo notebook.

Cada 'sesión' (normalmente un notebook) es un MÓDULO real registrado en
sys.modules cuyo espacio de nombres persiste entre celdas, igual que Jupyter:
defines una clase en una celda y la usas en la siguiente. Que sea un módulo de
verdad importa: Pydantic, dataclasses, typing y pickle buscan la clase por
`sys.modules[cls.__module__]` para resolver anotaciones.

En el kernel cada celda es el programa principal, así que los bloques
`if __name__ == "__main__":` se ejecutan. Captura stdout/stderr y hace 'echo'
de la última expresión (como un REPL).

Seguridad: ejecuta Python arbitrario en TU máquina. La API solo escucha en
127.0.0.1 y es para uso personal local (mismo modelo de confianza que Jupyter).
"""
from __future__ import annotations
import ast
import io
import os
import re
import sys
import threading
import traceback
import types
from contextlib import redirect_stdout, redirect_stderr

# Un módulo por sesión, con su candado (una celda a la vez por sesión).
_modules: dict[str, types.ModuleType] = {}
_locks: dict[str, threading.Lock] = {}
_registry_lock = threading.Lock()


def _module_name(session_id: str) -> str:
    return "curso_kernel_" + re.sub(r"\W", "_", session_id)


def _get(session_id: str) -> tuple[dict, threading.Lock]:
    with _registry_lock:
        if session_id not in _modules:
            mod = types.ModuleType(_module_name(session_id))
            sys.modules[mod.__name__] = mod
            _modules[session_id] = mod
            _locks[session_id] = threading.Lock()
        return _modules[session_id].__dict__, _locks[session_id]


def _olvidar_modulos_del_curso() -> None:
    """Los scripts del laboratorio se importan entre sí (00_comun, el buscador...) y
    Python los cachea para todo el proceso. Sin esto, tras editar uno de esos archivos
    las celdas seguirían usando la versión vieja aunque reinicies el kernel."""
    from .content import COURSE_ROOT
    raiz = str(COURSE_ROOT.resolve()).lower()
    for nombre, mod in list(sys.modules.items()):
        archivo = getattr(mod, "__file__", None) or ""
        a = archivo.lower().replace("\\", "/")
        if a.startswith(raiz.replace("\\", "/")) and ("modulo-" in a or "/comun/" in a):
            sys.modules.pop(nombre, None)


def reset(session_id: str) -> None:
    with _registry_lock:
        mod = _modules.pop(session_id, None)
        _locks.pop(session_id, None)
        if mod is not None:
            sys.modules.pop(mod.__name__, None)
        _olvidar_modulos_del_curso()


class _MainGuard(ast.NodeTransformer):
    """`if __name__ == "__main__":` -> `if True:` (la celda es el programa principal)."""

    def visit_If(self, node: ast.If) -> ast.If:
        self.generic_visit(node)
        t = node.test
        if (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "__name__"
                and len(t.ops) == 1 and isinstance(t.ops[0], ast.Eq)
                and len(t.comparators) == 1 and isinstance(t.comparators[0], ast.Constant)
                and t.comparators[0].value == "__main__"):
            node.test = ast.copy_location(ast.Constant(True), t)
        return node


def _run_into(ns: dict, code: str, out: io.StringIO, err: io.StringIO, result_box: list):
    """Ejecuta el cuerpo y deja el repr de la última expresión en result_box[0]."""
    with redirect_stdout(out), redirect_stderr(err):
        try:
            tree = _MainGuard().visit(ast.parse(code, mode="exec"))
            ast.fix_missing_locations(tree)
        except SyntaxError:
            traceback.print_exc()
            return
        last_expr = None
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expr = ast.Expression(tree.body.pop().value)
        try:
            if tree.body:
                exec(compile(tree, "<celda>", "exec"), ns)
            if last_expr is not None:
                val = eval(compile(last_expr, "<celda>", "eval"), ns)
                if val is not None:
                    result_box[0] = repr(val)
        except Exception:
            traceback.print_exc()


def run(session_id: str, code: str, file: str | None = None, timeout: float | None = None) -> dict:
    """Ejecuta `code` en la sesión. `file` (opcional) se expone como __file__ para que
    los scripts del laboratorio resuelvan rutas relativas a su carpeta.
    Devuelve {stdout, stderr, result, timed_out}."""
    # Límite por celda: los agentes encadenan varias llamadas al modelo.
    timeout = timeout or float(os.getenv("KERNEL_TIMEOUT", "300"))
    ns, lock = _get(session_id)
    if file:
        ns["__file__"] = file
    out, err = io.StringIO(), io.StringIO()
    result_box: list = [None]

    with lock:
        t = threading.Thread(target=_run_into, args=(ns, code, out, err, result_box), daemon=True)
        t.start()
        t.join(timeout)
        timed_out = t.is_alive()

    return {
        "stdout": out.getvalue(),
        "stderr": err.getvalue(),
        "result": result_box[0],
        "timed_out": timed_out,
    }
