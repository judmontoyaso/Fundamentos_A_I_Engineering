// Tarjeta Open Graph principal (1200x630) generada dinámicamente para redes sociales y buscadores.
import { ImageResponse } from "next/og";
import { cursos } from "@/lib/contenido";
import { NOMBRE_SITIO } from "@/lib/sitio";

export const alt = `${NOMBRE_SITIO} · Cursos técnicos de ingeniería de IA`;
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
          background: "linear-gradient(135deg, #0b1120 0%, #111b33 55%, #0f172a 100%)",
          color: "#f8fafc",
          fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 11,
                background: "linear-gradient(135deg, #2563eb, #10b981)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: 20,
              }}
            >
              IA
            </div>
            <span style={{ fontSize: 24, fontWeight: 700 }}>{NOMBRE_SITIO}</span>
          </div>
          <span
            style={{
              fontSize: 18,
              color: "#60a5fa",
              border: "1px solid rgba(96, 165, 250, 0.35)",
              borderRadius: 999,
              padding: "8px 18px",
            }}
          >
            Ingeniería de IA aplicada · En español
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px", maxWidth: "980px" }}>
          <div style={{ fontSize: 58, fontWeight: 700, lineHeight: 1.08, letterSpacing: "-0.025em" }}>
            Lleva sistemas con LLMs del notebook a producción
          </div>
          <div style={{ fontSize: 26, color: "#94a3b8", lineHeight: 1.4 }}>
            AI Engineering · Evals calibrados · AI Search &amp; RAG · Agentes con MCP y control de estado
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: "20px",
            borderTop: "1px solid rgba(148, 163, 184, 0.2)",
            paddingTop: "24px",
            fontSize: 20,
            color: "#cbd5e1",
          }}
        >
          <span>{cursos.length} cursos completos</span>
          <span>·</span>
          <span>{modulos} módulos prácticos</span>
          <span>·</span>
          <span>Código Python descargable (.zip)</span>
          <span>·</span>
          <span style={{ color: "#34d399", fontWeight: 600 }}>Certificado verificable</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
