// Tarjeta Open Graph dinámica (1200x630) al compartir un certificado en LinkedIn, X o WhatsApp.
import { ImageResponse } from "next/og";
import { verificarCertificado } from "@/lib/certificado";
import { NOMBRE_SITIO } from "@/lib/sitio";

export const alt = `Certificado verificable · ${NOMBRE_SITIO}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function CertificadoOg({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params;
  const cert = await verificarCertificado(decodeURIComponent(codigo));

  const nombre = cert?.nombre ?? "Credencial no válida";
  const curso = cert?.cursoTitulo ?? "Verificación de certificado";
  const id = cert?.idVerificacion ?? "SIN-VERIFICAR";
  const valido = Boolean(cert);

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          padding: "36px",
          background: "#0b1120",
          color: "#f8fafc",
          fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif",
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            padding: "44px 54px",
            borderRadius: "18px",
            border: "2px solid rgba(15, 95, 82, 0.5)",
            background: "linear-gradient(145deg, #0f172a 0%, #111c36 100%)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: "#93c5fd" }}>
              ACADEMIA DE INGENIERÍA APLICADA · {NOMBRE_SITIO.toUpperCase()}
            </span>
            <span
              style={{
                fontSize: 18,
                fontWeight: 700,
                padding: "8px 18px",
                borderRadius: 999,
                color: valido ? "#34d399" : "#f87171",
                border: `1px solid ${valido ? "rgba(52, 211, 153, 0.45)" : "rgba(248, 113, 113, 0.45)"}`,
              }}
            >
              {cert?.esEjemplo ? "CERTIFICADO DE EJEMPLO" : valido ? "CREDENCIAL VERIFICADA" : "NO VÁLIDO"}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <span style={{ fontSize: 20, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em" }}>
              Certificado de finalización otorgado a
            </span>
            <div style={{ fontSize: 56, fontWeight: 700, lineHeight: 1.1 }}>{nombre}</div>
            <div style={{ fontSize: 32, fontWeight: 600, color: "#60a5fa", lineHeight: 1.25 }}>{curso}</div>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderTop: "1px solid rgba(148, 163, 184, 0.25)",
              paddingTop: "20px",
              fontSize: 20,
              color: "#cbd5e1",
            }}
          >
            <span>{cert ? `${cert.modulos} módulos · ${cert.quizzes} autoevaluaciones aprobadas` : NOMBRE_SITIO}</span>
            <span style={{ fontFamily: "monospace", color: "#93c5fd" }}>ID: {id}</span>
          </div>
        </div>
      </div>
    ),
    { ...size },
  );
}
