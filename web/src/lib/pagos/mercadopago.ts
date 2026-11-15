// Mercado Pago · Checkout Pro (pago único). Variables: MP_ACCESS_TOKEN y, recomendado, MP_WEBHOOK_SECRET.
// Docs: https://www.mercadopago.com.co/developers/es/docs/checkout-pro/landing
import { createHmac, timingSafeEqual } from "node:crypto";
import type { EstadoPedido } from "../tipos";
import type { Proveedor } from "./index";

const API = "https://api.mercadopago.com";
const token = () => process.env.MP_ACCESS_TOKEN ?? "";

async function mp(ruta: string, init?: RequestInit) {
  const r = await fetch(`${API}${ruta}`, {
    ...init,
    headers: { Authorization: `Bearer ${token()}`, "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`Mercado Pago ${r.status}: ${(await r.text()).slice(0, 300)}`);
  return r.json();
}

const ESTADOS: Record<string, EstadoPedido> = {
  approved: "pagado", refunded: "reembolsado", charged_back: "reembolsado", rejected: "rechazado", cancelled: "rechazado",
};

export const mercadopago: Proveedor = {
  id: "mercadopago",
  nombre: "Mercado Pago",
  medios: "Tarjetas, PSE y otros medios locales",
  activo: () => Boolean(token()),

  async crearCheckout(pedido, titulo, base) {
    const vuelta = `${base}/pago/resultado?pedido=${pedido.id}`;
    const pref = await mp("/checkout/preferences", {
      method: "POST",
      headers: { "X-Idempotency-Key": pedido.id },
      body: JSON.stringify({
        items: [{ id: pedido.plan, title: titulo, quantity: 1, unit_price: pedido.monto, currency_id: pedido.moneda }],
        payer: { email: pedido.email },
        external_reference: pedido.id,
        back_urls: { success: vuelta, pending: vuelta, failure: vuelta },
        // auto_return exige URLs https: en local se omite y el comprador vuelve con el botón de la pasarela.
        ...(base.startsWith("https://") ? { auto_return: "approved", notification_url: `${base}/api/webhooks/mercadopago` } : {}),
      }),
    });
    return pref.init_point as string;
  },

  async consultar(ref) {
    if (!/^\d+$/.test(ref)) return null;
    const pago = await mp(`/v1/payments/${ref}`);
    if (!pago?.external_reference) return null;
    return {
      pedidoId: String(pago.external_reference),
      estado: ESTADOS[pago.status as string] ?? "pendiente",
      monto: Number(pago.transaction_amount),
      moneda: String(pago.currency_id),
    };
  },

  // Aviso: {"type":"payment","data":{"id":"123"}} con cabecera x-signature: ts=...,v1=...
  // Firma = HMAC-SHA256 de "id:<data.id>;request-id:<x-request-id>;ts:<ts>;" con el secreto del webhook.
  async refDeWebhook(req, cuerpo) {
    const url = new URL(req.url);
    let body: { type?: string; topic?: string; data?: { id?: string | number } } = {};
    try { body = JSON.parse(cuerpo || "{}"); } catch { /* aviso sin cuerpo JSON */ }
    const tipo = body.type ?? body.topic ?? url.searchParams.get("type") ?? url.searchParams.get("topic");
    const id = String(url.searchParams.get("data.id") ?? body.data?.id ?? url.searchParams.get("id") ?? "");
    if (tipo !== "payment" || !id) return null;

    const secreto = process.env.MP_WEBHOOK_SECRET;
    if (secreto) {
      const partes = Object.fromEntries((req.headers.get("x-signature") ?? "").split(",").map((p) => p.trim().split("=") as [string, string]));
      if (!partes.ts || !partes.v1) return null;
      const manifiesto = `id:${id.toLowerCase()};request-id:${req.headers.get("x-request-id") ?? ""};ts:${partes.ts};`;
      const esperado = createHmac("sha256", secreto).update(manifiesto).digest("hex");
      const a = Buffer.from(esperado), b = Buffer.from(partes.v1);
      if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
    }
    return id;
  },

  refDeRetorno: (params) => params.get("payment_id") ?? params.get("collection_id"),
};
