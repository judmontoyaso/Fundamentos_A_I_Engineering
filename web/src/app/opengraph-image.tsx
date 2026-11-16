// Tarjeta Open Graph principal (1200x630) que muestran redes sociales y buscadores al compartir el sitio.
import { ImageResponse } from "next/og";
import { cursos } from "@/lib/contenido";
import { NOMBRE_SITIO } from "@/lib/sitio";

export const alt = `${NOMBRE_SITIO}: cursos de ingeniería de IA en español, con código en Python`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  const modulos = cursos.reduce((n, c) => n + c.modulos, 0);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "58px 66px",
          background: "#10201c",
          color: "#e3ebe7",
          fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 11,
              background: "#0f5f52",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: 20,
            }}
          >
            IA
          </div>
          <span style={{ fontSize: 26, fontWeight: 700 }}>{NOMBRE_SITIO}</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px", maxWidth: "1000px" }}>
          <div style={{ fontSize: 60, fontWeight: 700, lineHeight: 1.08, letterSpacing: "-0.02em" }}>
            Cursos de ingeniería de IA en español, con código en Python
          </div>
          <div style={{ fontSize: 26, color: "#94a39c", lineHeight: 1.4 }}>
            Construye, evalúa y lleva a producción un sistema con modelos de lenguaje, del RAG a los agentes.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: "28px",
            borderTop: "1px solid rgba(148, 163, 156, 0.25)",
            paddingTop: "24px",
            fontSize: 21,
            color: "#c5d3cc",
          }}
        >
          <span>{cursos.length} cursos</span>
          <span>{modulos} módulos</span>
          <span>Primer módulo gratis</span>
          <span style={{ color: "#5cc4a8", fontWeight: 600 }}>Certificado verificable</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
