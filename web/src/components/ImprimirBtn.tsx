"use client";

export function ImprimirBtn() {
  return (
    <button type="button" className="btn primary" onClick={() => window.print()}>
      Imprimir / Guardar PDF
    </button>
  );
}
