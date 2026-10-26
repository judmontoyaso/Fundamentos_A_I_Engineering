"""
ev_comun.py — lo que comparten los laboratorios del curso de Evals.

Los sistemas que evaluamos son los del curso de AI Engineering (carpetas modulo-* de la raíz):
  extractor : texto de un CV -> FichaCV (Módulo 1). Es el más fácil de verificar: cada campo tiene
              una respuesta correcta que el código puede comprobar.
  rag       : pregunta -> respuesta citando CVs (Módulos 3 y 4). Hay que separar recuperación y respuesta.
  agente    : pedido -> búsqueda con herramientas y recomendación (Módulo 5). Hay que evaluar el camino.

Todas las llamadas pasan por el trazador del Módulo 7: cada eval deja trazas con tokens y latencia.
"""
from __future__ import annotations
import json
import os
import pathlib
import sys
import unicodedata
from datetime import date
from importlib import import_module

from pydantic import BaseModel, Field

COMUN = pathlib.Path(__file__).resolve().parent
CURSO = COMUN.parent
RAIZ = CURSO.parent                                   # carpeta del curso de AI Engineering
for sub in ("modulo-05-workflows-agentes", "modulo-07-observabilidad", "modulo-04-bm25-hibrida-rrf"):
    if str(RAIZ / sub / "code") not in sys.path:
        sys.path.append(str(RAIZ / sub / "code"))
if str(COMUN) not in sys.path:
    sys.path.append(str(COMUN))

c = import_module("00_comun")          # llm(), INSTRUCCION_CV, como_cv, buscador del Módulo 4
tz = import_module("00_trazador")      # trazas, llm_trazado, en_paralelo

HOY = date.today()


# ---------------- Sistema 1 · el extractor ----------------
class FichaCV(BaseModel):
    nombre: str
    correo: str | None = Field(default=None, description="null si no aparece")
    anios_experiencia: int = Field(ge=0, le=60, description="años de experiencia profesional total")
    skills: list[str] = Field(description="tecnologías y herramientas, en minúscula")


# El candidato a sistema barato del curso. Cambia por el que tenga tu cuenta: los modelos se retiran
# (gpt-4.1-nano respondía el 22 de octubre de 2026 y el 26 ya daba 404).
MODELO_BARATO = os.getenv("MODELO_BARATO", "gpt-5.4-nano")

PROMPTS_EXTRACTOR = {
    # v1 es el prompt "razonable" con el que se arranca. No está saboteado: es lo que casi todos escriben.
    "v1": f"Extrae los datos del CV. {c.INSTRUCCION_CV} No inventes.",
    # v2 sale de leer los fallos de v1 (Módulo 1 §6): la fecha de hoy y las reglas de conteo, que eran
    # las reglas de las etiquetas (ev_datos.py) y nunca se le habían dicho al modelo.
    "v2": (f"Extrae los datos del CV. {c.INSTRUCCION_CV} No inventes. Hoy es {HOY:%Y-%m-%d}.\n"
           "anios_experiencia: suma todo trabajo, aunque no sea del área; los periodos que se solapan cuentan "
           "una sola vez; 'hasta hoy' o 'actual' cuenta hasta hoy; prácticas y estudios no cuentan; los meses "
           "se redondean hacia abajo.\n"
           "skills: cada tecnología o herramienta tal como aparece, en minúscula y conservando su puntuación "
           "(por ejemplo '.net', 'c#'), aunque el CV esté en mayúsculas."),
}


def extraer(texto: str, version: str = "v1", modelo: str | None = None) -> FichaCV:
    return llm_cache(FichaCV, PROMPTS_EXTRACTOR[version], c.como_cv(texto), nombre="extractor",
                     version_prompt=f"extractor-{version}", modelo=modelo)


# ---------------- Comparaciones deterministas ----------------
def norm(t) -> str:
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def comparar_ficha(ficha: FichaCV, esperado: dict) -> dict[str, bool]:
    """Un booleano por campo. Las skills esperadas deben aparecer dentro de alguna extraída
    ("python" vale dentro de "python 3.12"); no se castiga extraer skills de más."""
    skills = [norm(s) for s in ficha.skills]
    correo_ok = (ficha.correo or None) == esperado["correo"] or bool(
        ficha.correo and esperado["correo"] and norm(ficha.correo) == norm(esperado["correo"]))
    return {
        "nombre": norm(ficha.nombre) == norm(esperado["nombre"]),
        "correo": correo_ok,
        "anios": ficha.anios_experiencia == esperado["anios"],
        "skills": all(any(norm(e) in s for s in skills) for e in esperado["skills"]),
    }


# ---------------- Resultados versionados ----------------
SALIDA = CURSO / "salida"


def guardar_jsonl(nombre: str, filas: list[dict]) -> pathlib.Path:
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / nombre
    ruta.write_text("\n".join(json.dumps(f, ensure_ascii=False, default=str) for f in filas) + "\n",
                    encoding="utf-8")
    return ruta


def leer_jsonl(nombre: str) -> list[dict]:
    ruta = SALIDA / nombre
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------- El pipeline del Módulo 2: extraer -> nivel -> perfil ----------------
class Nivel(BaseModel):
    razonamiento: str = Field(description="una frase con los datos del CV que justifican el nivel")
    nivel: str = Field(description="junior, semi-senior o senior")


class Perfil(BaseModel):
    perfil: str = Field(description="perfil profesional para un reclutador, máximo 40 palabras")


# Regla del nivel, escrita DESPUÉS del error analysis (Módulo 2 §6): el fallo más frecuente era que no había
# ninguna. Es una decisión de producto; lo importante es que exista y que el eval la compruebe.
RUBRICA_NIVEL = ("junior: menos de 3 años de experiencia; semi-senior: de 3 a 6 años; senior: 7 años o más, o 5 años "
                 "o más si lideró equipos o tuvo un cargo de líder o arquitecto.")

PROMPTS_NIVEL = {
    "v1": f"Clasifica el nivel del candidato según su experiencia y responsabilidades. {c.INSTRUCCION_CV}",
    "v2": f"Clasifica el nivel del candidato con esta regla: {RUBRICA_NIVEL} {c.INSTRUCCION_CV}",
}
PROMPTS_PERFIL = {
    "v1": f"Escribe el perfil profesional del candidato para un reclutador. {c.INSTRUCCION_CV} Usa solo lo que dice el CV.",
    "v2": (f"Escribe el perfil profesional del candidato para un reclutador. {c.INSTRUCCION_CV} Usa solo lo que dice "
           "el CV: no añadas cualidades, intereses ni certificaciones que no estén escritos. No incluyas nombre, "
           "correo, teléfono ni medios de contacto, ni fechas de graduación o datos que permitan inferir la edad."),
}


def pipeline(texto: str, modelo: str | None = None, version: str = "v1") -> dict:
    """Tres pasos encadenados, cada uno con su span: la traza deja ver en qué paso nace un error.
    La extracción usa siempre el prompt v1 del Módulo 1 para que el Módulo 2 cambie solo nivel y perfil."""
    with tz.span("pipeline CV", version=version):
        ficha = extraer(texto, "v1", modelo)
        nivel = tz.llm_trazado(Nivel, PROMPTS_NIVEL[version],
                               c.como_cv(texto) + f"\nDatos extraídos: {ficha.model_dump_json()}",
                               nombre="nivel", version_prompt=f"nivel-{version}", modelo=modelo)
        perfil = tz.llm_trazado(Perfil, PROMPTS_PERFIL[version], c.como_cv(texto), nombre="perfil",
                                version_prompt=f"perfil-{version}", modelo=modelo)
    return {"ficha": ficha.model_dump(), "nivel": nivel.nivel, "razon_nivel": nivel.razonamiento,
            "perfil": perfil.perfil}


# ---------------- Anotaciones de la app (Módulo 4) ----------------
DB_APP = RAIZ / "app" / "backend" / "data" / "curso.db"


def anotaciones(nb_id: str, anotador: str = "yo") -> dict[str, dict]:
    """Las etiquetas que pusiste en la página "Anotar" de la app: item_id -> {"label": bool, "nota": str}."""
    import sqlite3
    if not DB_APP.exists():
        return {}
    with sqlite3.connect(DB_APP) as con:
        try:
            filas = con.execute("SELECT item_id, label, nota FROM annotations WHERE nb_id=? AND anotador=?",
                                (nb_id, anotador)).fetchall()
        except sqlite3.OperationalError:            # la API aún no creó la tabla
            return {}
    return {i: {"label": bool(l), "nota": n} for i, l, n in filas}


def kappa(a: list[bool], b: list[bool]) -> float:
    """Kappa de Cohen para dos anotadores con etiquetas sí/no: acuerdo observado corregido por el que
    se esperaría por azar dadas las proporciones de cada uno."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


# ---------------- Caché de llamadas al LLM (Módulo 9) ----------------
CACHE_DB = SALIDA / "cache_llm.db"
CACHE = {"activa": os.getenv("EVALS_CACHE") == "1", "aciertos": 0, "fallos": 0}


def llm_cache(response_model, system: str, user: str, nombre: str = "llm", version_prompt: str | None = None,
              modelo: str | None = None):
    """Como tz.llm_trazado, pero si CACHE["activa"], devuelve la respuesta guardada para la MISMA llamada
    (modelo, schema, prompt y entrada). Cambiar cualquiera de esas cosas invalida la entrada: la caché
    nunca esconde un cambio de prompt. Lo que sí esconde es la variación entre corridas."""
    import hashlib
    import sqlite3
    if not CACHE["activa"]:
        return tz.llm_trazado(response_model, system, user, nombre, version_prompt, modelo=modelo)
    clave = hashlib.sha256(json.dumps([modelo or tz.MODELO, response_model.__name__,
                                       json.dumps(response_model.model_json_schema(), sort_keys=True),
                                       system, user]).encode()).hexdigest()
    SALIDA.mkdir(exist_ok=True)
    with sqlite3.connect(CACHE_DB) as con:
        con.execute("CREATE TABLE IF NOT EXISTS cache (clave TEXT PRIMARY KEY, valor TEXT)")
        fila = con.execute("SELECT valor FROM cache WHERE clave=?", (clave,)).fetchone()
    if fila:
        CACHE["aciertos"] += 1
        return response_model.model_validate_json(fila[0])
    CACHE["fallos"] += 1
    obj = tz.llm_trazado(response_model, system, user, nombre, version_prompt, modelo=modelo)
    with sqlite3.connect(CACHE_DB) as con:
        con.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (clave, obj.model_dump_json()))
    return obj
