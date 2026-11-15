// Logotipo oficial de IA en Producción generado por IA (cubo isométrico neural en azul zafiro y verde esmeralda).
export function Logo({ size = 36, className = "" }: { size?: number; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/logo.png"
      alt="IA en Producción"
      width={size}
      height={size}
      className={className}
      style={{
        width: size,
        height: size,
        borderRadius: Math.max(7, Math.round(size * 0.24)),
        objectFit: "cover",
        flexShrink: 0,
        display: "block",
        border: "1px solid rgba(59, 130, 246, 0.35)",
        boxShadow: "0 2px 10px rgba(15, 23, 42, 0.35)",
      }}
    />
  );
}
