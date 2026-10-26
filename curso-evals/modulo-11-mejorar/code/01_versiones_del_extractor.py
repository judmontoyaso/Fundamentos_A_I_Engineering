"""
01 · Cuatro versiones del extractor, cada una nacida de un fallo medido (manual §2-§4).

  v1 : el prompt inicial (Módulo 1).
  v2 : + fecha de hoy + reglas de conteo + regla de skills (Módulo 1). Arregla "hasta hoy", rompe los solapes.
  v3 : v1 + SOLO la fecha y la regla de skills: la hipótesis del ejercicio 6 del Módulo 1 (la línea larga de
       reglas de conteo es la que desestabiliza al modelo pequeño).
  v4 : el modelo ya no suma: extrae los HECHOS (cada trabajo con sus años, o un total declarado) y el
       total se calcula en código con la misma regla que las etiquetas (anios_de del Módulo 3).
  v5 : v4 + un campo para la DURACIÓN de un trabajo sin fechas ("3 años como analista"). En v4 ese hecho
       no cabía en el schema y el modelo a veces lo dejaba fuera: total 0 (manual §5).
Este archivo solo define las versiones y una función para evaluarlas; 02 y 03 las miden.
"""
from __future__ import annotations
import pathlib
import sys
from importlib import import_module

from pydantic import BaseModel, Field

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "comun"))
ev = import_module("ev_comun")

REGLA_SKILLS = ("skills: cada tecnología o herramienta tal como aparece, en minúscula y conservando su puntuación "
                "(por ejemplo '.net', 'c#'), aunque el CV esté en mayúsculas.")
ev.PROMPTS_EXTRACTOR["v3"] = (f"Extrae los datos del CV. {ev.c.INSTRUCCION_CV} No inventes. Hoy es {ev.HOY:%Y-%m-%d}.\n"
                              + REGLA_SKILLS)


class Trabajo(BaseModel):
    inicio: int | None = Field(default=None, description="año de inicio, tal como aparece")
    fin: int | None = Field(default=None, description="año de fin; null si sigue vigente ('hasta hoy', 'actual')")
    meses: int | None = Field(default=None, description="solo si el CV da la duración en meses en vez de años")


class TrabajoV5(Trabajo):
    anios: int | None = Field(default=None, description="duración en años, solo si el CV la da sin fechas "
                                                       "('3 años como analista')")


class HechosCV(BaseModel):
    nombre: str
    correo: str | None = Field(default=None, description="null si no aparece")
    skills: list[str]
    anios_declarados: int | None = Field(default=None, description="solo si el CV dice un total de años explícito")
    trabajos: list[Trabajo] = Field(description="cada trabajo; las prácticas y los estudios NO son trabajos")


PROMPT_V4 = (f"Extrae los HECHOS del CV. {ev.c.INSTRUCCION_CV} No inventes y no sumes nada: el total de años lo calcula "
             "el sistema. Para cada trabajo, sus años de inicio y fin tal como aparecen (fin null si sigue vigente), o "
             "su duración en meses si es lo único que da. Si el CV dice un total explícito ('9 años de experiencia', "
             "en número o en letras), ponlo en anios_declarados.\n" + REGLA_SKILLS)


class HechosCVV5(HechosCV):
    trabajos: list[TrabajoV5] = Field(description="cada trabajo; las prácticas y los estudios NO son trabajos")


PROMPT_V5 = PROMPT_V4.replace(
    "o su duración en meses si es lo único que da.",
    "o su duración si es lo único que da: en años ('3 años como analista' -> anios 3) o en meses ('18 meses' -> "
    "meses 18). Un trabajo con duración es un trabajo: no lo dejes fuera.")


def total_en_codigo(h: HechosCV) -> int:
    """La regla de las etiquetas (ev_datos), en código: periodos solapados una vez, 'hasta hoy' hasta este año,
    meses redondeados hacia abajo."""
    cubiertos, meses, anios = set(), 0, 0
    for t in h.trabajos:
        if t.inicio:
            cubiertos |= set(range(t.inicio, t.fin or ev.HOY.year))
        elif getattr(t, "anios", None):
            anios += t.anios
        elif t.meses:
            meses += t.meses
    if cubiertos or anios or meses:
        return len(cubiertos) + anios + meses // 12
    return h.anios_declarados or 0


def extraer(texto: str, version: str, modelo: str | None) -> ev.FichaCV:
    if version not in ("v4", "v5"):
        return ev.extraer(texto, version, modelo)
    esquema, prompt = (HechosCV, PROMPT_V4) if version == "v4" else (HechosCVV5, PROMPT_V5)
    h = ev.llm_cache(esquema, prompt, ev.c.como_cv(texto), nombre=f"extractor {version}",
                     version_prompt=f"extractor-{version}", modelo=modelo)
    return ev.FichaCV(nombre=h.nombre, correo=h.correo, anios_experiencia=total_en_codigo(h), skills=h.skills)


def evaluar(casos: list[dict], version: str, modelo: str | None, repeticiones: int = 2) -> dict:
    """Por caso: True si sale perfecto en todas las repeticiones. Devuelve {id: ok}."""
    res: dict = {}
    for _ in range(repeticiones):
        filas = ev.tz.en_paralelo(lambda cv: (cv["id"], all(ev.comparar_ficha(extraer(cv["texto"], version, modelo),
                                                                             cv["esperado"]).values())),
                                  [(cv,) for cv in casos])
        for i, ok in filas:
            res[i] = res.get(i, True) and ok
    return res
