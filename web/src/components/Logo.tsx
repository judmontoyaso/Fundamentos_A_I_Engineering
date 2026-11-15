// Logotipo vectorial de IA en Producción:
// Un grafo dirigido de producción (entrada -> nodo central con pulso/chispa de inferencia -> salida verificada)
// enmarcado en un bloque técnico con gradiente profundo.
export function Logo({ size = 34, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
      style={{ flexShrink: 0, display: "block" }}
    >
      <defs>
        <linearGradient id="iap-bg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0F172A" />
          <stop offset="55%" stopColor="#1E293B" />
          <stop offset="100%" stopColor="#1D4ED8" />
        </linearGradient>
        <linearGradient id="iap-glow" x1="8" y1="8" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#60A5FA" />
          <stop offset="100%" stopColor="#34D399" />
        </linearGradient>
      </defs>

      {/* Base técnica redondeada con borde sutil */}
      <rect x="1" y="1" width="38" height="38" rx="10" fill="url(#iap-bg)" stroke="#3B82F6" strokeOpacity="0.45" strokeWidth="1.5" />

      {/* Rejilla de telemetría sutil de fondo */}
      <path d="M1 13.5H39M1 26.5H39M13.5 1V39M26.5 1V39" stroke="#94A3B8" strokeOpacity="0.08" strokeWidth="1" />

      {/* Trazas de conexión del pipeline (DAG) */}
      <path
        d="M10.5 12.5L20 20M10.5 27.5L20 20M20 20H30"
        stroke="url(#iap-glow)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Nodos de entrada (datos + contexto) */}
      <circle cx="10.5" cy="12.5" r="3" fill="#0F172A" stroke="#60A5FA" strokeWidth="2" />
      <circle cx="10.5" cy="27.5" r="3" fill="#0F172A" stroke="#60A5FA" strokeWidth="2" />

      {/* Nodo central de inferencia (estrella de 4 puntas / chispa técnica) */}
      <path
        d="M20 13.2L21.75 18.25L26.8 20L21.75 21.75L20 26.8L18.25 21.75L13.2 20L18.25 18.25L20 13.2Z"
        fill="#F8FAFC"
      />

      {/* Nodo de salida en producción (verificado en verde esmeralda) */}
      <circle cx="30.5" cy="20" r="3.6" fill="#10B981" stroke="#ECFDF5" strokeWidth="1.6" />
    </svg>
  );
}
