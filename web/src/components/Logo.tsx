// Logotipo oficial de IA en Producción optimizado con next/image.
import Image from "next/image";

export function Logo({ size = 36, className = "", priority = false }: { size?: number; className?: string; priority?: boolean }) {
  return (
    <Image
      src="/logo.png"
      alt="IA en Producción"
      width={size}
      height={size}
      priority={priority}
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
