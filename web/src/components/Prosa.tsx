"use client";
// HTML de una lección (ya convertido en el servidor). Añade "copiar" a los bloques de código,
// visor ampliado (lightbox) al hacer clic en infografías, y navegación fluida entre lecciones.
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type MouseEvent } from "react";

export function Prosa({ html }: { html: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const [zoom, setZoom] = useState<{ src: string; alt: string } | null>(null);

  useEffect(() => {
    ref.current?.querySelectorAll("pre").forEach((pre) => {
      if (pre.querySelector(".copiar")) return;
      const b = document.createElement("button");
      b.className = "copiar";
      b.type = "button";
      b.textContent = "copiar";
      b.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(pre.querySelector("code")?.textContent ?? "");
          b.textContent = "✓ copiado";
        } catch {
          b.textContent = "no se pudo";
        }
        setTimeout(() => { b.textContent = "copiar"; }, 1500);
      });
      pre.appendChild(b);
    });
  }, [html]);

  useEffect(() => {
    if (!zoom) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setZoom(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [zoom]);

  function onClick(e: MouseEvent<HTMLDivElement>) {
    const target = e.target as HTMLElement;
    const img = target.closest("figure.infografia img") as HTMLImageElement | null;
    if (img) {
      setZoom({ src: img.src, alt: img.alt });
      return;
    }
    const a = target.closest("a");
    const href = a?.getAttribute("href") ?? "";
    if (href.startsWith("/leer/") && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      router.push(href);
    }
  }

  return (
    <>
      <div className="md" ref={ref} onClick={onClick} dangerouslySetInnerHTML={{ __html: html }} />
      {zoom && (
        <div className="lightbox" role="dialog" aria-modal="true" aria-label={zoom.alt} onClick={() => setZoom(null)}>
          <div className="lightbox-bar">
            <span>{zoom.alt}</span>
            <button type="button" className="btn" onClick={() => setZoom(null)}>Cerrar (Esc)</button>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={zoom.src} alt={zoom.alt} onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </>
  );
}
