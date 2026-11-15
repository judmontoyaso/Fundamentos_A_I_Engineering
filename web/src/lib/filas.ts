// Fila de la base (snake_case) -> tipo de la app. Lo comparten el store de Postgres y el de Supabase.
import type { Acceso, Pedido } from "./tipos";

type Fila = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

const iso = (d: Date | string | null | undefined) => (d ? new Date(d).toISOString() : null);

export const aAcceso = (r: Fila): Acceso => ({
  id: r.id, userId: r.user_id, plan: r.plan, alcance: r.alcance, estado: r.estado, hasta: iso(r.hasta),
  origen: r.origen, pedidoId: r.pedido_id ?? null, creado: iso(r.creado)!,
});

export const aPedido = (r: Fila): Pedido => ({
  id: r.id, userId: r.user_id, email: r.email, plan: r.plan, curso: r.curso ?? null, monto: Number(r.monto), moneda: r.moneda,
  proveedor: r.proveedor, estado: r.estado, refProveedor: r.ref_proveedor ?? null, creado: iso(r.creado)!,
});
