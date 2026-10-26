"""
m2_notas.py — la revisión de las 30 salidas de m2_salidas_revisadas.jsonl (pipeline con gpt-5.4-nano).

NOTAS es la codificación ABIERTA: lo que vio quien escribió el curso al leer cada caso, con sus
palabras, sin categorías. Una lista vacía es "ok". Se escribió leyendo, antes de agrupar.

CATEGORIAS es la codificación AXIAL: los grupos que salieron DESPUÉS de leer todas las notas, cada
uno con el paso del pipeline donde nace y una gravedad (qué tan dañino es para el reclutador).
NOTA_A_CATEGORIA asigna cada nota a su grupo.
"""

NOTAS: dict[int, list[str]] = {
    1: [],
    2: ["8 años de arquitecto cloud y sale semi-senior; el #1 con 9 años es senior"],
    3: [],
    4: ["el perfil termina con el nombre y el correo del candidato", "skill ' .net' con espacio y 'backend' como skill"],
    5: ["el perfil añade 'enfoque en mejora continua y control de procesos', que el CV no dice"],
    6: ["el perfil dice 'Certificación ... ISO 27001': el CV no menciona ninguna certificación"],
    7: [],
    8: ["relleno genérico en el perfil ('generar insights accionables')"],
    9: ["la razón dice 'nivel avanzado' y la etiqueta es semi-senior"],
    10: [],
    11: ["el perfil incluye 'Contacto: ricardo.salas@mail.com'", "'dba' como skill (es un cargo)"],
    12: [],
    13: ["'qa automation' como skill (es el rol)"],
    14: [],
    15: ["el perfil inventa 'asegurando trazabilidad y mantenibilidad del ciclo de vida'"],
    16: ["el perfil inventa que está 'interesado en oportunidades'", "el perfil menciona el contacto por LinkedIn"],
    17: [],
    18: ["líder técnico con 7 años y sale semi-senior"],
    19: ["5 años en vez de 7 ('hasta la fecha') y el nivel se calcula con esos 5"],
    20: [],
    21: [],
    22: ["el perfil incluye 'Contacto: pedro.malo@mail.com'"],
    23: ["nombre en mayúsculas sin normalizar", "skills vacías en la ficha, pero el perfil sí menciona SAS y R"],
    24: ["9 años y sale semi-senior, igual que el #1 con 9 años salió senior", "'ingeniero de redes' como skill"],
    25: [],
    26: ["el perfil menciona 'graduada 2010': deja inferir la edad"],
    27: ["nombre en minúsculas y sin tilde, tal como venía"],
    28: ["líder de datos con 7 años y sale semi-senior; la razón misma habla de liderazgo"],
    29: [],
    30: ["11 años y semi-senior; la razón lo justifica por 'solo roles técnicos'", "'frontend' como skill"],
}

# grupo: (paso donde nace, gravedad 1-3, descripción)
CATEGORIAS: dict[str, tuple[str, int, str]] = {
    "nivel sin criterio": ("nivel", 3, "el nivel no sigue una regla: mismos años, distinto nivel; liderazgo ignorado"),
    "contacto en el perfil": ("perfil", 3, "el perfil copia correo o contacto del candidato"),
    "perfil inventa": ("perfil", 3, "el perfil afirma cosas que el CV no dice"),
    "dato sensible en el perfil": ("perfil", 2, "el perfil incluye datos que permiten inferir atributos protegidos"),
    "error de extracción propagado": ("extracción", 2, "un error de la ficha contamina los pasos siguientes"),
    "skills mal formadas": ("extracción", 1, "cargos como skills, espacios o skills perdidas"),
    "nombre sin normalizar": ("extracción", 1, "mayúsculas o minúsculas tal como venían"),
    "relleno genérico": ("perfil", 1, "frases vacías que no informan"),
}

NOTA_A_CATEGORIA: dict[tuple[int, int], str] = {
    (2, 0): "nivel sin criterio", (9, 0): "nivel sin criterio", (18, 0): "nivel sin criterio",
    (24, 0): "nivel sin criterio", (28, 0): "nivel sin criterio", (30, 0): "nivel sin criterio",
    (4, 0): "contacto en el perfil", (11, 0): "contacto en el perfil", (16, 1): "contacto en el perfil",
    (22, 0): "contacto en el perfil",
    (5, 0): "perfil inventa", (6, 0): "perfil inventa", (15, 0): "perfil inventa", (16, 0): "perfil inventa",
    (26, 0): "dato sensible en el perfil",
    (19, 0): "error de extracción propagado", (23, 1): "error de extracción propagado",
    (4, 1): "skills mal formadas", (11, 1): "skills mal formadas", (13, 0): "skills mal formadas",
    (24, 1): "skills mal formadas", (30, 1): "skills mal formadas",
    (23, 0): "nombre sin normalizar", (27, 0): "nombre sin normalizar",
    (8, 0): "relleno genérico",
}
