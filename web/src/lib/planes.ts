// Planes a la venta. El precio en USD es el de referencia que se muestra; lo que se cobra sale de
// PAGOS_MONEDA y PRECIO_* (las pasarelas locales cobran en moneda local).
import type { PlanId } from "./tipos";

export type Plan = {
  id: PlanId; nombre: string; usd: number; dias: number | null; resumen: string;
  /** Precio anterior en USD cuando el plan está en promoción (se muestra tachado). */
  usdAntes?: number;
};

export const PLANES: Record<PlanId, Plan> = {
  mensual: {
    id: "mensual",
    nombre: "Mensual",
    usd: 10,
    dias: 30,
    resumen: "Acceso a todos los cursos durante 30 días",
  },
  anual: {
    id: "anual",
    nombre: "Anual",
    usd: 100,
    dias: 365,
    resumen: "Acceso a todos los cursos, incluidos los que salgan, durante un año",
  },
  curso: {
    id: "curso",
    nombre: "Curso individual",
    usd: 30,
    usdAntes: 40, // promoción de lanzamiento
    dias: null,
    resumen: "Un curso, sin fecha de vencimiento",
  },
};

export const esPlan = (p: unknown): p is PlanId => typeof p === "string" && p in PLANES;

export const MONEDA = (process.env.PAGOS_MONEDA ?? "USD").toUpperCase();

/** Monto a cobrar en la moneda de la pasarela. En USD sale del plan; en otra moneda, de PRECIO_<PLAN>. */
export function montoDe(plan: PlanId): number | null {
  const env = Number(process.env[`PRECIO_${plan.toUpperCase()}`]);
  if (Number.isFinite(env) && env > 0) return env;
  return MONEDA === "USD" ? PLANES[plan].usd : null;
}

export function formatoMonto(monto: number, moneda: string): string {
  try {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: moneda,
      maximumFractionDigits: moneda === "COP" ? 0 : 2,
    }).format(monto);
  } catch {
    return `${monto} ${moneda}`;
  }
}
