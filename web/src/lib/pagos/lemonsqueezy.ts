// Lemon Squeezy · Hosted Checkout (Merchant of Record global, cobra en USD).
// Variables: LEMONSQUEEZY_API_KEY, LEMONSQUEEZY_STORE_ID, LEMONSQUEEZY_VARIANT_<PLAN> y LEMONSQUEEZY_WEBHOOK_SECRET.
// Docs: https://docs.lemonsqueezy.com/api/checkouts/create-checkout
import { createHmac, timingSafeEqual } from "node:crypto";
import type { EstadoPedido, PlanId } from "../tipos";
import type { Proveedor } from "./index";

const API = "https://api.lemonsqueezy.com/v1";
const key = () => process.env.LEMONSQUEEZY_API_KEY ?? "";
const storeId = () => process.env.LEMONSQUEEZY_STORE_ID ?? "";
const variantDe = (plan: PlanId) => process.env[`LEMONSQUEEZY_VARIANT_${plan.toUpperCase()}`] ?? "";

async function ls(ruta: string, init?: RequestInit) {
  const r = await fetch(`${API}${ruta}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${key()}`,
      Accept: "application/vnd.api+json",
      "Content-Type": "application/vnd.api+json",
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`Lemon Squeezy ${r.status}: ${(await r.text()).slice(0, 300)}`);
  return r.json();
}

const ESTADOS: Record<string, EstadoPedido> = {
  paid: "pagado",
  refunded: "reembolsado",
  failed: "rechazado",
};

export const lemonsqueezy: Proveedor = {
  id: "lemonsqueezy",
  nombre: "Lemon Squeezy",
  medios: "Tarjetas internacionales, PayPal y Apple Pay (USD)",
  activo: () => Boolean(key() && storeId()),

  async crearCheckout(pedido, titulo, base) {
    const variantId = variantDe(pedido.plan);
    if (!variantId) throw new Error(`Falta LEMONSQUEEZY_VARIANT_${pedido.plan.toUpperCase()}`);
    const vuelta = `${base}/pago/resultado?pedido=${pedido.id}`;
    const res = await ls("/checkouts", {
      method: "POST",
      body: JSON.stringify({
        data: {
          type: "checkouts",
          attributes: {
            product_options: { name: titulo, redirect_url: vuelta },
            checkout_data: {
              email: pedido.email,
              custom: { pedido_id: pedido.id },
            },
          },
          relationships: {
            store: { data: { type: "stores", id: String(storeId()) } },
            variant: { data: { type: "variants", id: String(variantId) } },
          },
        },
      }),
    });
    return res?.data?.attributes?.url as string;
  },

  async consultar(ref) {
    if (!/^\d+$/.test(ref)) return null;
    const res = await ls(`/orders/${ref}`);
    const attr = res?.data?.attributes;
    const pedidoId = res?.meta?.custom_data?.pedido_id ?? attr?.first_order_item?.custom_data?.pedido_id;
    if (!attr || !pedidoId) return null;
    return {
      pedidoId: String(pedidoId),
      estado: ESTADOS[attr.status as string] ?? "pendiente",
      monto: Number(attr.subtotal_usd ?? attr.total_usd ?? attr.total) / 100,
      moneda: String(attr.currency ?? "USD"),
    };
  },

  // Webhook con cabecera X-Signature = HMAC-SHA256(cuerpo, LEMONSQUEEZY_WEBHOOK_SECRET).
  async refDeWebhook(req, cuerpo) {
    const secreto = process.env.LEMONSQUEEZY_WEBHOOK_SECRET;
    if (!secreto) return null;
    const firma = req.headers.get("x-signature") ?? "";
    const esperado = createHmac("sha256", secreto).update(cuerpo).digest("hex");
    const a = Buffer.from(esperado), b = Buffer.from(firma.toLowerCase());
    if (a.length !== b.length || !timingSafeEqual(a, b)) return null;

    let body: { meta?: { event_name?: string }; data?: { id?: string | number } } = {};
    try { body = JSON.parse(cuerpo); } catch { return null; }
    const ev = body.meta?.event_name ?? "";
    if ((ev !== "order_created" && ev !== "order_refunded") || !body.data?.id) return null;
    return String(body.data.id);
  },

  refDeRetorno: (params) => params.get("order_id"),
};
