// A donde vuelve el comprador tras pagar. Si el aviso de la pasarela aún no llegó, se consulta el pago aquí mismo.
// Si el comprador volvió con el botón "Atrás / Volver al sitio" sin pagar, se cancela el pedido pendiente.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { confirmarPedido } from "@/lib/acceso";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { itemsDe } from "@/lib/contenido";
import { aplicarPago, proveedor } from "@/lib/pagos";
import { store } from "@/lib/store";

export const metadata: Metadata = { title: "Resultado del pago", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function Resultado({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const sp = await searchParams;
  const params = new URLSearchParams(Object.entries(sp).flatMap(([k, v]) => (typeof v === "string" ? [[k, v]] : [])));
  const id = params.get("pedido") ?? "";
  const usuario = await getUsuario();
  if (!usuario) redirect(urlEntrar(`/pago/resultado?${params}`));

  let pedido = await store.pedido(id);
  if (pedido && pedido.userId !== usuario.id) pedido = null;

  if (pedido?.estado === "pendiente") {
    const ref = proveedor(pedido.proveedor)?.refDeRetorno(params) ?? null;
    const canceladoExplicito =
      params.get("retorno") === "cancelado" ||
      params.get("status") === "null" ||
      params.get("collection_status") === "null" ||
      params.get("cancelar") === "1";

    if (ref && !canceladoExplicito) {
      try {
        const aplicado = await aplicarPago(pedido.proveedor, ref);
        // Solo vale si la pasarela dice que ese pago corresponde a este mismo pedido.
        if (aplicado?.id === pedido.id) pedido = aplicado;
      } catch (e) {
        console.error("[pago/resultado]", e);
      }
    } else if (canceladoExplicito || ((pedido.proveedor === "mercadopago" || pedido.proveedor === "wompi") && !ref)) {
      // Volvió del checkout sin haber iniciado ningún cobro: cerramos el pedido como rechazado/cancelado.
      await store.transicionPedido(pedido.id, ["pendiente"], "rechazado", null);
      pedido = await store.pedido(pedido.id);
    }
  } else if (pedido?.estado === "pagado") {
    // Pagado pero quizá sin acceso (si la concesión falló en un intento previo): se repara al volver aquí.
    try {
      await confirmarPedido(pedido, null);
    } catch (e) {
      console.error("[pago/resultado] no se pudo conceder el acceso", e);
    }
  }

  const destino = pedido?.curso ? itemsDe(pedido.curso)[0]?.id : itemsDe("ai-engineering")[0]?.id;
  const urlReintentar = pedido ? `/comprar?plan=${pedido.plan}${pedido.curso ? `&curso=${pedido.curso}` : ""}` : "/#planes";

  return (
    <Sitio>
      <div className="pagina">
        {!pedido ? (
          <div className="caja">
            <h1>No encontramos ese pedido</h1>
            <p className="muted">Revisa tu acceso en <Link href="/cuenta">Mi cuenta</Link>.</p>
          </div>
        ) : pedido.estado === "pagado" ? (
          <div className="caja">
            <span className="estado ok">acceso activado</span>
            <h1 style={{ marginTop: ".6rem" }}>
              {pedido.proveedor.startsWith("cupon:") ? "¡Cupón canjeado con éxito!" : "Pago confirmado"}
            </h1>
            <p className="muted">
              Tu acceso ya está activo en <b>{usuario.email}</b>. Ya puedes entrar a todas las lecciones, laboratorios y
              autoevaluaciones incluidas en tu plan.
            </p>
            <p style={{ marginTop: "1.1rem", display: "flex", gap: ".6rem", flexWrap: "wrap" }}>
              <Link className="btn primary grande" href={`/leer/${destino}`}>Empezar a estudiar ahora</Link>
              <Link className="btn grande" href="/cuenta">Ir a Mi cuenta</Link>
            </p>
          </div>
        ) : pedido.estado === "pendiente" ? (
          <div className="caja">
            <span className="estado pend">pendiente de confirmación</span>
            <h1 style={{ marginTop: ".6rem" }}>Estamos confirmando tu pago</h1>
            <p className="muted">
              Algunos medios, como PSE o efectivo, tardan unos minutos en reportar la confirmación bancaria. Tu acceso
              se activa automáticamente en cuanto la pasarela confirme.
            </p>
            <p style={{ marginTop: "1.1rem", display: "flex", gap: ".6rem", flexWrap: "wrap" }}>
              <a className="btn primary" href={`/pago/resultado?${params}`}>Volver a comprobar</a>
              <a className="btn" href={`/pago/resultado?pedido=${pedido.id}&cancelar=1`}>No pagué: cancelar el pedido</a>
            </p>
          </div>
        ) : (
          <div className="caja">
            <span className="estado no">{pedido.estado === "reembolsado" ? "reembolsado" : "sin cobro"}</span>
            <h1 style={{ marginTop: ".6rem" }}>
              {pedido.estado === "reembolsado" ? "Pago reembolsado" : "No se realizó ningún cobro"}
            </h1>
            <p className="muted">
              {pedido.estado === "reembolsado"
                ? "Este pedido fue reembolsado y su acceso fue desactivado."
                : "Saliste de la pasarela antes de completar el pago o la operación fue cancelada. No se te cobró nada."}
            </p>
            <p style={{ marginTop: "1.1rem", display: "flex", gap: ".6rem", flexWrap: "wrap" }}>
              <Link className="btn primary" href={urlReintentar}>Volver a intentar o usar un cupón</Link>
              <Link className="btn" href="/cuenta">Ir a Mi cuenta</Link>
            </p>
          </div>
        )}
      </div>
    </Sitio>
  );
}
