"use client";

import confetti from "canvas-confetti";
import { toPng } from "html-to-image";
import { jsPDF } from "jspdf";
import { useEffect, useState } from "react";

export function ImprimirBtn({
  idCertificado = "IA-CERT",
  celebrar = false,
}: {
  idCertificado?: string;
  celebrar?: boolean;
}) {
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    if (!celebrar) return;
    const t = setTimeout(() => {
      try {
        confetti({
          particleCount: 55,
          spread: 68,
          origin: { y: 0.62 },
          colors: ["#2563eb", "#059669", "#eab308", "#38bdf8"],
        });
      } catch {
        /* ignore if canvas blocked */
      }
    }, 280);
    return () => clearTimeout(t);
  }, [celebrar]);

  async function descargarPdfOficial() {
    const nodo = document.getElementById("certificado-diploma");
    if (!nodo || descargando) return;
    setDescargando(true);
    try {
      // El diploma se captura a su tamaño real (sin la reducción que se aplica en pantallas angostas).
      const zoomPrevio = nodo.style.zoom;
      nodo.style.zoom = "1";
      const rect = { width: nodo.offsetWidth, height: nodo.offsetHeight };
      const dataUrl = await toPng(nodo, {
        quality: 1,
        pixelRatio: 2.5,
        cacheBust: true,
        width: rect.width,
        height: rect.height,
      }).finally(() => { nodo.style.zoom = zoomPrevio; });

      const w = rect.width;
      const h = rect.height;
      const orientacion = w >= h ? "l" : "p";
      const pdf = new jsPDF({
        orientation: orientacion,
        unit: "px",
        format: [w, h],
        compress: true,
      });
      pdf.addImage(dataUrl, "PNG", 0, 0, w, h, undefined, "FAST");
      pdf.save(`Certificado-${idCertificado}.pdf`);
    } catch (e) {
      console.error("[certificado pdf]", e);
      window.print();
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div style={{ display: "inline-flex", gap: ".5rem", flexWrap: "wrap" }}>
      <button
        type="button"
        className="btn primary"
        onClick={descargarPdfOficial}
        disabled={descargando}
      >
        {descargando ? "Generando PDF HD…" : "Descargar PDF oficial"}
      </button>
      <button type="button" className="btn" onClick={() => window.print()}>
        Imprimir
      </button>
    </div>
  );
}
