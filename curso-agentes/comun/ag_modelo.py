"""El modelo detrás del agente, con una sola interfaz: responder(mensajes, herramientas) -> Respuesta.

Dos implementaciones:

- ModeloOpenAI: un modelo real con tool calling (necesita OPENAI_API_KEY; el modelo se elige con MODELO).
- ModeloSimulado: una política fija, sin red y sin azar salvo el que pidas, que se comporta como un modelo que
  sigue el procedimiento de preselección. Sirve para correr todos los laboratorios sin gastar y para que los tests
  sean reproducibles. Sus defectos se encienden uno a uno (errata, terquedad, obediencia a una inyección,
  descuidos al azar) para ver cómo responde EL CONTROLADOR, que es lo que este curso enseña a construir.

Lo que mide el modelo simulado es tu código (el bucle, las herramientas, las políticas), no la calidad de un LLM.
Los números sobre cómo se comporta un modelo de verdad solo salen de correr los mismos scripts con una API key.

crear_modelo() devuelve el real si hay OPENAI_API_KEY (y no pusiste AGENTE_SIMULADO=1); si no, el simulado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import json
import os
import random
import re
import time

try:  # un .env en la carpeta del curso o en la raíz, si existe
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass


@dataclass
class Llamada:
    id: str
    nombre: str
    argumentos: dict[str, Any]


@dataclass
class Respuesta:
    texto: str | None
    llamadas: list[Llamada] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_salida: int = 0


class Modelo(Protocol):
    nombre: str

    def responder(self, mensajes: list[dict], herramientas: list[dict]) -> Respuesta: ...


def contar_tokens(dato: Any) -> int:
    """Estimación barata (4 caracteres por token) para cuando no hay un proveedor que los cuente."""
    return max(1, len(dato if isinstance(dato, str) else json.dumps(dato, ensure_ascii=False)) // 4)


# ---------------------------------------------------------------------------------------------- modelo real
class ModeloOpenAI:
    def __init__(self, modelo: str | None = None) -> None:
        from openai import OpenAI
        self.nombre = modelo or os.getenv("MODELO", "gpt-4.1-mini")
        self._cliente = OpenAI()

    def responder(self, mensajes: list[dict], herramientas: list[dict]) -> Respuesta:
        extra = {"tools": herramientas, "parallel_tool_calls": False} if herramientas else {}
        r = self._cliente.chat.completions.create(model=self.nombre, messages=mensajes, **extra)
        m = r.choices[0].message
        llamadas = []
        for tc in m.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_json_invalido": tc.function.arguments}  # la validación de la herramienta lo rechazará
            llamadas.append(Llamada(tc.id, tc.function.name, args if isinstance(args, dict) else {"_valor": args}))
        return Respuesta(m.content, llamadas, r.usage.prompt_tokens, r.usage.completion_tokens)


# ------------------------------------------------------------------------------------------ modelo simulado
# Una instrucción incrustada en un dato: "llama a herramienta(arg='x', n=1)".
PATRON_INYECCION = re.compile(r"llama a (\w+)\(([^)]*)\)", re.IGNORECASE)
PATRON_ARG = re.compile(r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\d+))")


def historial(mensajes: list[dict]) -> list[tuple[str, dict, dict]]:
    """Las llamadas ya hechas y lo que devolvieron: [(herramienta, argumentos, resultado), ...]."""
    pedidas: dict[str, tuple[str, dict]] = {}
    hechas: list[tuple[str, dict, dict]] = []
    for m in mensajes:
        for tc in m.get("tool_calls") or []:
            pedidas[tc["id"]] = (tc["function"]["name"], json.loads(tc["function"]["arguments"]))
        if m.get("role") == "tool" and m.get("tool_call_id") in pedidas:
            nombre, args = pedidas[m["tool_call_id"]]
            try:
                res = json.loads(m["content"])
            except (json.JSONDecodeError, TypeError):
                res = {"texto": m.get("content")}
            hechas.append((nombre, args, res if isinstance(res, dict) else {"valor": res}))
    return hechas


class ModeloSimulado:
    """Política fija de preselección: vacante -> búsqueda -> ficha y elegibilidad de cada uno -> terna.

    Defectos opcionales:
      errata             la primera búsqueda lleva una habilidad mal escrita.
      terco              repite siempre la misma llamada (un agente atascado en un bucle).
      obedece_inyeccion  si un dato le dice "llama a X(...)", lo hace (un modelo vulnerable).
      p_descuido         probabilidad de dar por elegible a un candidato sin verificarlo.
      agenda             tras la terna, intenta agendar una entrevista con cada elegible.
      latencia_s         segundos que tarda cada respuesta (para medir paralelismo).
    """

    def __init__(self, *, errata: bool = False, terco: bool = False, obedece_inyeccion: bool = False,
                 p_descuido: float = 0.0, semilla: int = 0, lee_cv: bool = True, agenda: bool = False,
                 latencia_s: float = 0.0) -> None:
        self.nombre = "simulado"
        self.errata, self.terco, self.obedece_inyeccion = errata, terco, obedece_inyeccion
        self.p_descuido, self.lee_cv, self.agenda, self.latencia_s = p_descuido, lee_cv, agenda, latencia_s
        self._azar = random.Random(semilla)
        self._asumidos: set[str] = set()  # candidatos dados por buenos sin verificar
        self._n = 0

    def responder(self, mensajes: list[dict], herramientas: list[dict]) -> Respuesta:
        if self.latencia_s:
            time.sleep(self.latencia_s)
        ofrecidas = [h["function"]["name"] for h in herramientas]
        decision = self._decidir(mensajes, ofrecidas)
        entrada = contar_tokens(mensajes) + contar_tokens(herramientas)
        if isinstance(decision, str):
            return Respuesta(decision, [], entrada, contar_tokens(decision))
        nombre, args = decision
        self._n += 1
        return Respuesta(None, [Llamada(f"sim-{self._n}", nombre, args)], entrada, contar_tokens(args) + 8)

    # La "cabeza" del modelo simulado: mira qué se ha hecho y elige el siguiente paso.
    def _decidir(self, mensajes: list[dict], ofrecidas: list[str]) -> tuple[str, dict] | str:
        def tool(base: str) -> str | None:  # acepta prefijos, p. ej. "ats_buscar_candidatos"
            return next((n for n in ofrecidas if n == base or n.endswith("_" + base)), None)

        def es(nombre: str, base: str) -> bool:
            return nombre == base or nombre.endswith("_" + base)

        hechas = historial(mensajes)
        tarea = next((m["content"] for m in mensajes if m.get("role") == "user"), "")
        sistema = next((m["content"] for m in mensajes if m.get("role") == "system"), "")
        vac_id = (re.search(r"VAC-\d+", tarea) or re.search(r"VAC-\d+", "VAC-101")).group(0)

        if self.terco and tool("buscar_candidatos"):
            return tool("buscar_candidatos"), {"habilidades": ["Python"], "max_aspiracion_usd": 1000}

        if self.obedece_inyeccion:
            for _, _, res in hechas:
                m = PATRON_INYECCION.search(json.dumps(res, ensure_ascii=False))
                if not m or not tool(m.group(1)):
                    continue
                args = {k: (int(n) if n else a or b) for k, a, b, n in PATRON_ARG.findall(m.group(2))}
                if not any(es(n, m.group(1)) and a == args for n, a, _ in hechas):
                    return tool(m.group(1)), args

        vac = next((r for n, _, r in hechas if es(n, "obtener_vacante") and r.get("ok")), None)
        if vac is None:
            if not tool("obtener_vacante") or any(es(n, "obtener_vacante") for n, _, _ in hechas):
                return f"No pude cargar la vacante {vac_id}."
            return tool("obtener_vacante"), {"vacante_id": vac_id}

        busquedas = [(a, r) for n, a, r in hechas if es(n, "buscar_candidatos")]
        if not busquedas:
            if not tool("buscar_candidatos"):
                return "En esta etapa no tengo una herramienta para buscar candidatos."
            habilidades = list(vac["requisitos_obligatorios"])
            # Una regla aprendida en ejecuciones anteriores puede pedir una habilidad más (Módulo 3).
            habilidades += [h for h in re.findall(r"REQUISITO_EXTRA: ([^\n]+)", sistema) if h not in habilidades]
            if self.errata:
                habilidades[-1] = habilidades[-1].replace("ó", "o").rstrip("s")  # "Evaluacion de LLM"
            return tool("buscar_candidatos"), {"habilidades": habilidades, "max_aspiracion_usd": vac["presupuesto_usd_mes"]}

        args_busqueda, res_busqueda = busquedas[-1]
        if not res_busqueda.get("ok"):
            sugeridas = res_busqueda.get("sugerencias") or {}
            corregidas = [(sugeridas.get(h) or [h])[0] for h in args_busqueda.get("habilidades", [])]
            if sugeridas and corregidas != args_busqueda.get("habilidades") and len(busquedas) < 3:
                return tool("buscar_candidatos"), {**args_busqueda, "habilidades": corregidas}
            return self._entregar(tool, vac_id, [], "La búsqueda falló y no supe corregirla.")

        candidatos = [c["id"] for c in res_busqueda.get("candidatos", [])]
        fichas = {a.get("candidato_id") for n, a, _ in hechas if es(n, "consultar_ficha_candidato")}
        veredictos = {a.get("candidato_id"): r for n, a, r in hechas if es(n, "verificar_elegibilidad")}
        for cid in candidatos:
            if cid in veredictos or cid in self._asumidos:
                continue
            if self.lee_cv and tool("consultar_ficha_candidato") and cid not in fichas:
                return tool("consultar_ficha_candidato"), {"candidato_id": cid}
            if self._azar.random() < self.p_descuido or not tool("verificar_elegibilidad"):
                self._asumidos.add(cid)  # el descuido: lo da por bueno sin comprobarlo
                continue
            return tool("verificar_elegibilidad"), {"vacante_id": vac_id, "candidato_id": cid}

        elegibles = [c for c in candidatos if c in self._asumidos or veredictos.get(c, {}).get("elegible")]
        if self.agenda and tool("agendar_entrevista"):
            agendados = {a.get("candidato_id") for n, a, _ in hechas if es(n, "agendar_entrevista")}
            for cid in elegibles:
                if cid not in agendados:
                    return tool("agendar_entrevista"), {"vacante_id": vac_id, "candidato_id": cid, "fecha": "2026-11-20T15:00"}
        return self._entregar(tool, vac_id, elegibles, f"{len(elegibles)} de {len(candidatos)} candidatos encontrados son elegibles.")

    @staticmethod
    def _entregar(tool, vac_id: str, elegibles: list[str], motivo: str) -> tuple[str, dict] | str:
        if tool("entregar_terna"):
            return tool("entregar_terna"), {"vacante_id": vac_id, "candidatos": elegibles, "justificacion": motivo}
        return json.dumps({"vacante_id": vac_id, "candidatos": elegibles, "justificacion": motivo}, ensure_ascii=False)


def crear_modelo(**defectos: Any) -> Modelo:
    """El modelo real si hay API key; si no, el simulado con los defectos que pidas."""
    if os.getenv("OPENAI_API_KEY") and os.getenv("AGENTE_SIMULADO") != "1":
        return ModeloOpenAI()
    return ModeloSimulado(**defectos)
