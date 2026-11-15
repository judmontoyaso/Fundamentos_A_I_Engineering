// Wompi · Web Checkout (pago único, solo COP).
// Variables: WOMPI_PUBLIC_KEY, WOMPI_INTEGRITY_SECRET y WOMPI_EVENTS_SECRET. Docs: https://docs.wompi.co
import { createHash, timingSafeEqual } from "node:crypto";
import type { EstadoPedido } from "../tipos";
import type { Proveedor } from "./index";

const llave = () => process.env.WOMPI_PUBLIC_KEY ?? "";
const api = () => (llave().startsWith("pub_test_") ? "https://sandbox.wompi.co/v1" : "https://production.wompi.co/v1");
const sha256 = (s: string) => createHash("sha256").update(s).digest("hex");

const ESTADOS: Record<string, EstadoPedido> = { APPROVED: "pagado", DECLINED: "rechazado", ERROR: "rechazado", VOIDED: "reembolsado" };

export const wompi: Proveedor = {
  id: "wompi",
  nombre: "Wompi",
  medios: "Tarjetas, PSE, Nequi y Bancolombia (Colombia)",
  activo: () => Boolean(llave() && process.env.WOMPI_INTEGRITY_SECRET),

  async crearCheckout(pedido, _titulo, base) {
    if (pedido.moneda !== "COP") throw new Error("Wompi solo cobra en COP: define PAGOS_MONEDA=COP");
    const centavos = Math.round(pedido.monto * 100);
    // Firma de integridad: sha256(referencia + monto en centavos + moneda + secreto de integridad).
    const firma = sha256(`${pedido.id}${centavos}${pedido.moneda}${process.env.WOMPI_INTEGRITY_SECRET}`);
    const q = new URLSearchParams({
      "public-key": llave(),
      currency: pedido.moneda,
      "amount-in-cents": String(centavos),
      reference: pedido.id,
      "signature:integrity": firma,
      "redirect-url": `${base}/pago/resultado?pedido=${pedido.id}`,
      "customer-data:email": pedido.email,
    });
    return `https://checkout.wompi.co/p/?${q}`;
  },

  async consultar(ref) {
    if (!/^[\w-]+$/.test(ref)) return null;
    const r = await fetch(`${api()}/transactions/${ref}`, { cache: "no-store" });
    if (!r.ok) return null;
    const t = (await r.json())?.data;
    if (!t?.reference) return null;
    return {
      pedidoId: String(t.reference),
      estado: ESTADOS[t.status as string] ?? "pendiente",
      monto: Number(t.amount_in_cents) / 100,
      moneda: String(t.currency),
    };
  },

  // Evento: {event:"transaction.updated", data:{transaction:{...}}, signature:{properties:[...], checksum}, timestamp}
  // checksum = sha256(valores de `properties` concatenados + timestamp + secreto de eventos).
  async refDeWebhook(_req, cuerpo) {
    const secreto = process.env.WOMPI_EVENTS_SECRET;
    if (!secreto) return null;
    let e: { event?: string; data?: Record<string, unknown>; signature?: { properties?: string[]; checksum?: string }; timestamp?: number };
    try { e = JSON.parse(cuerpo); } catch { return null; }
    if (e.event !== "transaction.updated" || !e.data || !e.signature?.checksum || !Array.isArray(e.signature.properties)) return null;
    const valor = (ruta: string) => ruta.split(".").reduce<unknown>((o, k) => (o as Record<string, unknown> | undefined)?.[k], e.data);
    const esperado = sha256(e.signature.properties.map((p) => String(valor(p) ?? "")).join("") + String(e.timestamp ?? "") + secreto);
    const a = Buffer.from(esperado), b = Buffer.from(e.signature.checksum.toLowerCase());
    if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
    const id = (e.data.transaction as { id?: string } | undefined)?.id;
    return id ? String(id) : null;
  },

  refDeRetorno: (params) => params.get("id"),
};
