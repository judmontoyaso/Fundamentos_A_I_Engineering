// Pasarela de mentira para probar el flujo completo en local. Solo existe en modo desarrollo.
import { auth0Activo } from "../auth0";
import { store } from "../store";
import type { Proveedor } from "./index";

export const simulado: Proveedor = {
  id: "simulado",
  nombre: "Pago simulado",
  medios: "Solo desarrollo: aprueba el pago sin cobrar nada",
  activo: () => !auth0Activo && process.env.NODE_ENV !== "production",
  async crearCheckout(pedido) {
    return `/pago/resultado?pedido=${pedido.id}&simulado=${pedido.id}`;
  },
  async consultar(ref) {
    const p = await store.pedido(ref);
    return p ? { pedidoId: p.id, estado: "pagado", monto: p.monto, moneda: p.moneda } : null;
  },
  async refDeWebhook() {
    return null;
  },
  refDeRetorno: (params) => params.get("simulado"),
};
