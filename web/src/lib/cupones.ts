// Validación y cálculo de cupones de descuento (1 % a 100 %).
import "server-only";
import { store } from "./store";
import type { Cupon, PlanId } from "./tipos";

export type ResultadoCupon =
  | { ok: true; cupon: Cupon; porcentaje: number }
  | { ok: false; error: string };

export async function validarCupon(
  codigoRaw: string,
  plan: PlanId,
  cursoId: string | null,
): Promise<ResultadoCupon> {
  const codigo = codigoRaw.trim().toUpperCase();
  if (!codigo) return { ok: false, error: "Ingresa un código de cupón." };

  const c = await store.cupon(codigo);
  if (!c || !c.activo) {
    return { ok: false, error: "Ese código de cupón no existe o ya no está activo." };
  }
  if (c.usosMax !== null && c.usos >= c.usosMax) {
    return { ok: false, error: "Este cupón ya alcanzó su límite máximo de usos." };
  }
  if (c.plan !== null && c.plan !== plan) {
    return { ok: false, error: `Este cupón solo es válido para el plan "${c.plan}".` };
  }
  if (c.curso !== null && (plan !== "curso" || c.curso !== cursoId)) {
    return { ok: false, error: `Este cupón es exclusivo para el curso "${c.curso}".` };
  }
  const porcentaje = Math.min(100, Math.max(1, c.porcentaje));
  return { ok: true, cupon: c, porcentaje };
}

export function aplicarDescuento(montoBase: number, porcentaje: number): number {
  if (porcentaje >= 100) return 0;
  return Math.max(0, Math.round((montoBase * (100 - porcentaje)) / 100));
}
