"use client";
// Acciones del certificado: descargar el PDF (captura del diploma a tamaño real), imprimir y copiar el enlace.
import confetti from "canvas-confetti";
import { Download, Link2, Printer } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export function ImprimirBtn({
  idCertificado = "IA-CERT",
  celebrar = false,
  url,
}: {
  idCertificado?: string;
  celebrar?: boolean;
  url?: string;
}) {
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    if (!celebrar || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setTimeout(() => {
      try {
        confetti({ particleCount: 55, spread: 68, origin: { y: 0.62 }, colors: ["#0f5f52", "#1f7a4d", "#b7790c", "#5cc4a8"] });
      } catch {
        /* canvas bloqueado */
      }
    }, 280);
    return () => clearTimeout(t);
  }, [celebrar]);

  async function descargar() {
    const nodo = document.getElementById("certificado-diploma");
    if (!nodo || descargando) return;
    setDescargando(true);
    try {
      // Las librerías del PDF (~120 KB) se cargan solo cuando alguien lo pide.
      const [{ toPng }, { jsPDF }] = await Promise.all([import("html-to-image"), import("jspdf")]);
      // El diploma se captura a su tamaño real (sin la reducción que se aplica en pantallas angostas).
      const zoomPrevio = nodo.style.zoom;
      nodo.style.zoom = "1";
      const w = nodo.offsetWidth;
      const h = nodo.offsetHeight;
      const dataUrl = await toPng(nodo, { quality: 1, pixelRatio: 2.5, cacheBust: true, width: w, height: h }).finally(() => {
        nodo.style.zoom = zoomPrevio;
      });
      const pdf = new jsPDF({ orientation: w >= h ? "l" : "p", unit: "px", format: [w, h], compress: true });
      pdf.addImage(dataUrl, "PNG", 0, 0, w, h, undefined, "FAST");
      pdf.save(`Certificado-${idCertificado}.pdf`);
      toast.success("PDF descargado");
    } catch (e) {
      console.error("[certificado pdf]", e);
      toast.error("No se pudo generar el PDF. Se abrió la impresión: elige “Guardar como PDF”.");
      window.print();
    } finally {
      setDescargando(false);
    }
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(url ?? window.location.href);
      toast.success("Enlace copiado", { description: "Cualquiera con el enlace puede comprobar el certificado." });
    } catch {
      toast.error("No se pudo copiar el enlace. Cópialo desde la barra de direcciones.");
    }
  }

  return (
    <>
      <button type="button" className="btn primary con-icono" onClick={descargar} disabled={descargando}>
        <Download size={16} aria-hidden />
        {descargando ? "Generando el PDF…" : "Descargar PDF"}
      </button>
      <button type="button" className="btn con-icono" onClick={() => window.print()}>
        <Printer size={16} aria-hidden /> Imprimir
      </button>
      <button type="button" className="btn con-icono" onClick={copiar}>
        <Link2 size={16} aria-hidden /> Copiar enlace
      </button>
    </>
  );
}
