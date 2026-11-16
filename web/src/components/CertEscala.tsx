"use client";
// El diploma tiene un tamaño fijo (1120 px de ancho), como una hoja. En pantallas más angostas no se
// reacomoda: se reduce entero, igual que al alejar un PDF.
import { useEffect, useRef, type ReactNode } from "react";

const ANCHO = 1120;

export function CertEscala({ children }: { children: ReactNode }) {
  const caja = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = caja.current;
    const hoja = el?.firstElementChild as HTMLElement | null;
    if (!el || !hoja) return;
    const ajustar = () => {
      hoja.style.zoom = String(Math.min(1, el.clientWidth / ANCHO));
    };
    ajustar();
    const ro = new ResizeObserver(ajustar);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return <div ref={caja} className="cert-escala">{children}</div>;
}
