"""
m4_etiquetas_autor.py — las etiquetas de quien escribió el curso para la tarea de anotación del Módulo 4
(los 30 perfiles de m2_salidas_revisadas.jsonl), aplicando la guía de anotacion.json.

(pasa, seguro, nota). "seguro" = False marca los casos en los que la guía no decidía sola: la duda se
anotó en el momento, antes de comparar con nadie.
"""

AUTOR: dict[str, tuple[bool, bool, str]] = {
    "1": (True, True, ""),
    "2": (True, True, "'foco en despliegues y automatización' se deduce del cargo"),
    "3": (True, True, ""),
    "4": (False, True, "correo del candidato al final"),
    "5": (False, False, "'enfoque en mejora continua' ¿se deduce de 'coordinadora de calidad'? lo tomo como añadido"),
    "6": (False, True, "inventa una certificación ISO 27001"),
    "7": (True, True, ""),
    "8": (True, True, "relleno ('insights accionables'), pero no afirma nada falso"),
    "9": (True, False, "'experto en Jenkins' exagera '7 años con Jenkins'; ¿es una cualidad inventada?"),
    "10": (True, True, ""),
    "11": (False, True, "'Contacto: ricardo.salas@mail.com'"),
    "12": (True, True, ""),
    "13": (True, True, ""),
    "14": (True, True, ""),
    "15": (False, True, "inventa 'trazabilidad y mantenibilidad del ciclo de vida'"),
    "16": (False, True, "inventa interés en oportunidades y menciona LinkedIn"),
    "17": (True, True, ""),
    "18": (True, True, ""),
    "19": (True, True, ""),
    "20": (True, False, "'base técnica sólida' para 18 meses junior: ¿cualidad inventada o relleno?"),
    "21": (True, True, ""),
    "22": (False, True, "'Contacto: pedro.malo@mail.com'"),
    "23": (True, True, ""),
    "24": (True, True, ""),
    "25": (True, False, "'recién graduado' está en el CV, pero insinúa la edad: ¿regla 3?"),
    "26": (False, True, "'graduada 2010' deja inferir la edad"),
    "27": (True, True, ""),
    "28": (True, True, ""),
    "29": (True, True, ""),
    "30": (True, True, ""),
}
