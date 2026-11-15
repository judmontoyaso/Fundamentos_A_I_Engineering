"""
08 · Un servidor MCP: las herramientas del asistente, fuera del código del agente.

Hasta ahora buscar_cvs y ver_cv eran funciones de Python que el bucle del agente
llamaba directamente. Aquí son las mismas dos herramientas, pero publicadas por un
proceso aparte que habla MCP (Model Context Protocol). Cualquier cliente MCP puede
descubrirlas y usarlas sin importar este archivo: el agente de 09, un asistente de
escritorio o un IDE.

No llama a ningún modelo ni necesita API key. Para que el protocolo sea lo único
nuevo, el corpus es pequeño y la búsqueda es por coincidencia de palabras; en el
proyecto, dentro de buscar_cvs iría el buscador híbrido del Módulo 4.

No se ejecuta a mano: lo arranca el cliente (09) como subproceso y se hablan por
stdin/stdout. Por eso este archivo NO debe imprimir nada con print(): la salida
estándar es el canal del protocolo, y una línea suelta lo corrompe. Los mensajes
de diagnóstico van a stderr.
"""
from __future__ import annotations
import sys
from typing import Literal

from mcp.server.mcpserver import MCPServer      # SDK 2.x (en la 1.x se llamaba FastMCP)

CVS = {
    1: {"nombre": "Laura Méndez", "nivel": "senior",
        "texto": "Ingeniera de datos, 9 años. Lideró un equipo de 6 personas. Kafka, Flink y Spark en streaming "
                 "de eventos de pago. Diseñó la plataforma de datos en tiempo real de una fintech."},
    2: {"nombre": "Pedro Salas", "nivel": "junior",
        "texto": "Analista de datos, 1 año. SQL, Excel y Power BI. Reportes semanales para el área comercial."},
    3: {"nombre": "Camila Ortiz", "nivel": "semi-senior",
        "texto": "Desarrolladora backend, 4 años. Python, FastAPI y PostgreSQL. Certificada en ISO 27001. "
                 "Mantiene pipelines por lotes con Airflow."},
    4: {"nombre": "Andrés Rojas", "nivel": "senior",
        "texto": "Arquitecto de software, 12 años. Microservicios en Java y Go, Kubernetes. Sin experiencia "
                 "en streaming; fuerte en diseño de APIs y mentoría de equipos."},
}

mcp = MCPServer("buscador-cvs")


def _log(mensaje: str) -> None:
    print(f"[servidor] {mensaje}", file=sys.stderr, flush=True)


# El docstring y las anotaciones de tipo NO son documentación interna: el SDK los convierte en la
# descripción y el JSON Schema que lee el modelo. Es la misma regla del §10: la descripción es prompt.
@mcp.tool()
def buscar_cvs(consulta: str, nivel: Literal["junior", "semi-senior", "senior"] | None = None, k: int = 3) -> str:
    """Busca CVs por palabras clave. Devuelve id, nombre, nivel y un extracto de cada uno.

    Usa `nivel` solo si el pedido exige una seniority concreta. Para leer un CV completo, llama a ver_cv con su id.
    """
    _log(f"buscar_cvs(consulta={consulta!r}, nivel={nivel!r}, k={k})")
    k = max(1, min(k, 5))                                    # argumento del modelo: acotar, no confiar
    palabras = [p for p in consulta.lower().split() if len(p) > 2]
    puntuados = []
    for cv_id, cv in CVS.items():
        if nivel and cv["nivel"] != nivel:
            continue
        aciertos = sum(p in cv["texto"].lower() for p in palabras)
        if aciertos:
            puntuados.append((aciertos, cv_id))
    if not puntuados:
        # Error accionable (§10): le dice al modelo qué probar después, no solo que falló.
        filtro = f" con nivel='{nivel}'" if nivel else ""
        return f"Sin resultados para '{consulta}'{filtro}. Prueba con otras palabras o quita el filtro de nivel."
    puntuados.sort(reverse=True)
    return "\n".join(
        f"[id={cv_id}] {CVS[cv_id]['nombre']} ({CVS[cv_id]['nivel']}): {CVS[cv_id]['texto'][:90]}..."
        for _, cv_id in puntuados[:k]
    )


@mcp.tool()
def ver_cv(cv_id: int) -> str:
    """Devuelve el CV completo de un candidato a partir de su id. Úsalo antes de recomendar a alguien."""
    _log(f"ver_cv(cv_id={cv_id})")
    cv = CVS.get(cv_id)
    if cv is None:
        return f"No existe el CV {cv_id}. Ids válidos: {sorted(CVS)}. Usa buscar_cvs para encontrar candidatos."
    return f"{cv['nombre']} · {cv['nivel']}\n{cv['texto']}"


if __name__ == "__main__":
    _log("listo, esperando al cliente por stdio")
    mcp.run()                                                # transporte por defecto: stdio
