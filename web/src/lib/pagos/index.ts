// Capa de pagos. Cada pasarela es un `Proveedor`; el resto de la app solo conoce esta interfaz.
// Para sumar otra (Lemon Squeezy, Stripe...): un archivo nuevo que la implemente y una línea en TODOS.
//
// Regla de seguridad: nunca se confía en lo que dice el navegador o el cuerpo de un webhook.
// Ambos solo aportan una referencia; el estado real del pago se consulta siempre a la pasarela.
import "server-only";
import { confirmarPedido, reembolsarPedido } from "../acceso";
import { store } from "../store";
import type { EstadoPedido, Pedido } from "../tipos";
import { lemonsqueezy } from "./lemonsqueezy";
import { mercadopago } from "./mercadopago";
import { simulado } from "./simulado";
import { wompi } from "./wompi";

export type Consulta = { pedidoId: string; estado: EstadoPedido; monto: number; moneda: string };

export interface Proveedor {
  id: string;
  nombre: string;
  medios: string;                                    // qué acepta, para mostrarlo al elegir
  activo(): boolean;
  /** Crea el cobro y devuelve la URL a la que se envía al comprador. */
  crearCheckout(pedido: Pedido, titulo: string, base: string): Promise<string>;
  /** Estado real de un pago según la pasarela. `ref` es el id del pago en la pasarela. */
  consultar(ref: string): Promise<Consulta | null>;
  /** Valida la firma del webhook y devuelve el id del pago a consultar (o null si no aplica o no es auténtico). */
  refDeWebhook(req: Request, cuerpo: string): Promise<string | null>;
  /** Id del pago en los parámetros con los que la pasarela devuelve al comprador. */
  refDeRetorno(params: URLSearchParams): string | null;
}

const TODOS: Proveedor[] = [wompi, lemonsqueezy, mercadopago, simulado];

export const proveedoresActivos = () => TODOS.filter((p) => p.activo());
export const proveedor = (id: string) => TODOS.find((p) => p.id === id && p.activo()) ?? null;

/** Consulta el pago en la pasarela y deja el pedido y el acceso en el estado que corresponde. */
export async function aplicarPago(proveedorId: string, ref: string): Promise<Pedido | null> {
  const p = proveedor(proveedorId);
  if (!p) return null;
  const c = await p.consultar(ref);
  if (!c) return null;
  const pedido = await store.pedido(c.pedidoId);
  if (!pedido || pedido.proveedor !== p.id) return null;

  if (c.estado === "pagado") {
    // El monto y la moneda deben ser los del pedido: evita pagar un pedido caro con un cobro barato.
    if (c.moneda.toUpperCase() !== pedido.moneda.toUpperCase() || c.monto + 0.01 < pedido.monto) {
      console.error(`[pagos] ${p.id}: el pago ${ref} no coincide con el pedido ${pedido.id} (${c.monto} ${c.moneda} vs ${pedido.monto} ${pedido.moneda})`);
      return pedido;
    }
    await confirmarPedido(pedido, ref);
  } else if (c.estado === "reembolsado") {
    await reembolsarPedido(pedido);
  } else if (c.estado === "rechazado") {
    await store.transicionPedido(pedido.id, ["pendiente"], "rechazado", ref);
  }
  return store.pedido(pedido.id);
}

/** URL pública de la app: APP_BASE_URL si existe; si no, la de la petición. */
export function urlBase(req: Request): string {
  if (process.env.APP_BASE_URL) return process.env.APP_BASE_URL.replace(/\/$/, "");
  const h = req.headers;
  const host = h.get("x-forwarded-host") ?? h.get("host");
  return host ? `${h.get("x-forwarded-proto") ?? "http"}://${host}` : new URL(req.url).origin;
}
