"""
04 · Medir similitud: coseno, producto punto y distancia L2.

Muestra por qué el coseno (ángulo) es el default en NLP y cómo, sobre
vectores normalizados, dot == coseno y L2 da el mismo RANKING.

Sin dependencias de LLM; solo numpy. Los "embeddings" aquí son de juguete
para que veas la mecánica; en 06/09 usamos embeddings reales.

    pip install numpy
"""
import numpy as np


def coseno(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def dot(a, b):
    return float(np.asarray(a, float) @ np.asarray(b, float))


def l2(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.linalg.norm(a - b))


def normalizar(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


if __name__ == "__main__":
    # Dos vectores que apuntan casi en la misma dirección pero con MAGNITUD
    # muy distinta (p. ej. un texto corto y uno largo sobre lo mismo).
    corto = [1.0, 1.0]
    largo = [10.0, 11.0]          # misma dirección aprox., 10x más "grande"
    distinto = [1.0, -1.0]        # dirección opuesta en un eje

    print("== Magnitud no debería mandar: coseno lo ignora ==")
    print(f"coseno(corto, largo)    = {coseno(corto, largo):.4f}  (alto: significan parecido)")
    print(f"dot(corto, largo)       = {dot(corto, largo):.4f}  (inflado por la magnitud de 'largo')")
    print(f"L2(corto, largo)        = {l2(corto, largo):.4f}  (grande: la magnitud los 'aleja')")
    print()
    print(f"coseno(corto, distinto) = {coseno(corto, distinto):.4f}  (bajo: significan distinto)")

    print("\n== Sobre vectores normalizados, dot == coseno ==")
    cn, ln = normalizar(corto), normalizar(largo)
    print(f"dot(norm(corto), norm(largo)) = {dot(cn, ln):.4f}")
    print(f"coseno(corto, largo)          = {coseno(corto, largo):.4f}  (iguales)")

    print("\nModeraleja: normaliza y usa dot (barato) == coseno. Configura tu")
    print("colección con la métrica que pide la tarjeta del modelo.")
