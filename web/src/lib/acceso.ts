// Reglas de acceso: qué puede leer cada quién, y cómo se concede o se retira un derecho.
import "server-only";
import { randomUUID } from "node:crypto";
import { esAdmin } from "./auth";
import { PLANES } from "./planes";
import { store } from "./store";
import type { Acceso, ItemNav, Pedido, PlanId, Usuario } from "./tipos";

export const vigente = (a: Acceso, ahora = new Date()) =>
  a.estado === "activo" && (a.hasta === null || new Date(a.hasta) > ahora);

export const cubre = (a: Acceso, cursoId: string) => a.alcance === "todo" || a.alcance === cursoId;

export async function accesosVigentes(u: Usuario | null): Promise<Acceso[]> {
  if (!u) return [];
  return (await store.accesos(u.id)).filter((a) => vigente(a));
}

/** Cursos que el usuario puede leer completos. */
export async function cursosAbiertos(u: Usuario | null, todos: string[]): Promise<Set<string>> {
  if (esAdmin(u)) return new Set(todos);
  const acc = await accesosVigentes(u);
  return new Set(todos.filter((c) => acc.some((a) => cubre(a, c))));
}

export async function puedeLeer(u: Usuario | null, it: ItemNav): Promise<boolean> {
  if (it.gratis) return true;
  return (await cursosAbiertos(u, [it.curso])).has(it.curso);
}

type Concesion = { userId: string; plan: PlanId; curso: string | null; origen: string; pedidoId?: string | null; dias?: number | null };

/** Concede un acceso. Los planes por tiempo se suman al final del periodo vigente, no lo pisan. */
export async function conceder(o: Concesion): Promise<Acceso> {
  const alcance = o.plan === "curso" ? (o.curso ?? "") : "todo";
  if (!alcance) throw new Error("falta el curso del plan por curso");
  const dias = o.dias === undefined ? PLANES[o.plan].dias : o.dias;
  let hasta: string | null = null;
  if (dias) {
    const actuales = (await store.accesos(o.userId)).filter((a) => vigente(a) && a.alcance === alcance && a.hasta);
    const desde = Math.max(Date.now(), ...actuales.map((a) => new Date(a.hasta!).getTime()));
    hasta = new Date(desde + dias * 86_400_000).toISOString();
  }
  const acceso: Acceso = {
    id: randomUUID(), userId: o.userId, plan: o.plan, alcance, estado: "activo", hasta,
    origen: o.origen, pedidoId: o.pedidoId ?? null, creado: new Date().toISOString(),
  };
  await store.crearAcceso(acceso);
  return acceso;
}

/** Marca el pedido como pagado y concede su acceso. Idempotente: un webhook repetido no duplica nada. */
export async function confirmarPedido(pedido: Pedido, refProveedor: string | null): Promise<boolean> {
  const cambio = await store.transicionPedido(pedido.id, ["pendiente", "rechazado"], "pagado", refProveedor);
  if (!cambio) return false;
  await conceder({ userId: pedido.userId, plan: pedido.plan, curso: pedido.curso, origen: pedido.proveedor, pedidoId: pedido.id });
  return true;
}

export async function reembolsarPedido(pedido: Pedido): Promise<boolean> {
  const cambio = await store.transicionPedido(pedido.id, ["pagado"], "reembolsado", pedido.refProveedor);
  if (cambio) await store.revocarPorPedido(pedido.id);
  return cambio;
}
