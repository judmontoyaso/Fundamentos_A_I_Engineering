// Reglas de acceso: qué puede leer cada quién, y cómo se concede o se retira un derecho.
import "server-only";
import { randomUUID } from "node:crypto";
import { esAdmin } from "./auth";
import { curso } from "./contenido";
import { enviarConfirmacionCompra } from "./correo";
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

type Concesion = {
  userId: string; plan: PlanId; curso: string | null; origen: string; pedidoId?: string | null; dias?: number | null;
  /** Id fijo del acceso. Con él, conceder dos veces lo mismo choca con la clave primaria en vez de duplicar. */
  id?: string;
};

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
    id: o.id ?? randomUUID(), userId: o.userId, plan: o.plan, alcance, estado: "activo", hasta,
    origen: o.origen, pedidoId: o.pedidoId ?? null, creado: new Date().toISOString(),
  };
  await store.crearAcceso(acceso);
  return acceso;
}

/**
 * Marca el pedido como pagado y concede su acceso. Idempotente: un webhook repetido no duplica nada.
 *
 * Son dos escrituras (pedido y acceso) y la segunda puede fallar. Por eso un pedido que ya está pagado
 * no se da por terminado: se comprueba que su acceso exista y, si falta, se concede en este intento.
 * Si la concesión falla, la excepción sube, el webhook responde 500 y la pasarela reintenta.
 */
export async function confirmarPedido(pedido: Pedido, refProveedor: string | null): Promise<boolean> {
  const cambio = await store.transicionPedido(pedido.id, ["pendiente", "rechazado"], "pagado", refProveedor);
  if (!cambio && (await store.pedido(pedido.id))?.estado !== "pagado") return false; // reembolsado o inexistente

  const tieneAcceso = async () => (await store.accesos(pedido.userId)).some((a) => a.pedidoId === pedido.id);
  if (await tieneAcceso()) return cambio;

  let acceso: Acceso;
  try {
    acceso = await conceder({
      id: `ped-${pedido.id}`, userId: pedido.userId, plan: pedido.plan, curso: pedido.curso,
      origen: pedido.proveedor, pedidoId: pedido.id,
    });
  } catch (e) {
    if (await tieneAcceso()) return cambio; // otro aviso simultáneo lo concedió primero
    throw e;
  }

  const descripcion = pedido.plan === "curso" && pedido.curso
    ? `Plan por curso · ${curso(pedido.curso)?.titulo ?? pedido.curso}`
    : `Plan ${PLANES[pedido.plan].nombre.toLowerCase()}`;
  await enviarConfirmacionCompra(pedido, descripcion, acceso.hasta);
  return true;
}

/** Marca el pedido como reembolsado y retira su acceso. Repetirlo es inofensivo: revocar dos veces da lo mismo. */
export async function reembolsarPedido(pedido: Pedido): Promise<boolean> {
  const cambio = await store.transicionPedido(pedido.id, ["pagado"], "reembolsado", pedido.refProveedor);
  if (cambio || (await store.pedido(pedido.id))?.estado === "reembolsado") await store.revocarPorPedido(pedido.id);
  return cambio;
}
