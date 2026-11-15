// A donde vuelve el comprador tras pagar. Si el aviso de la pasarela aún no llegó, se consulta el pago aquí mismo.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { itemsDe } from "@/lib/contenido";
import { aplicarPago, proveedor } from "@/lib/pagos";
import { store } from "@/lib/store";

export const metadata: Metadata = { title: "Resultado del pago" };
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
    const ref = proveedor(pedido.proveedor)?.refDeRetorno(params);
    if (ref) {
      try {
        const aplicado = await aplicarPago(pedido.proveedor, ref);
        // Solo vale si la pasarela dice que ese pago corresponde a este mismo pedido.
        if (aplicado?.id === pedido.id) pedido = aplicado;
      } catch (e) {
        console.error("[pago/resultado]", e);
      }
    }
  }

  const destino = pedido?.curso ? itemsDe(pedido.curso)[0]?.id : itemsDe("ai-engineering")[0]?.id;

  return (
    <Sitio>
      <div className="pagina">
        {!pedido ? (
          <><h1>No encontramos ese pedido</h1><p className="muted">Revisa tu acceso en <Link href="/cuenta">Mi cuenta</Link>.</p></>
        ) : pedido.estado === "pagado" ? (
          <>
            <h1>Pago confirmado</h1>
            <p className="muted">Tu acceso ya está activo en esta cuenta.</p>
            <p><Link className="btn primary grande" href={`/leer/${destino}`}>Empezar a leer</Link>{" "}
              <Link className="btn grande" href="/cuenta">Mi cuenta</Link></p>
          </>
        ) : pedido.estado === "pendiente" ? (
          <>
            <h1>Estamos confirmando tu pago</h1>
            <p className="muted">
              Algunos medios, como PSE o efectivo, tardan unos minutos. Tu acceso se activa solo cuando la pasarela
              confirma; puedes recargar esta página o revisar <Link href="/cuenta">Mi cuenta</Link>.
            </p>
            <p><a className="btn" href={`/pago/resultado?${params}`}>Volver a comprobar</a></p>
          </>
        ) : (
          <>
            <h1>{pedido.estado === "reembolsado" ? "Pago reembolsado" : "El pago no se completó"}</h1>
            <p className="muted">No se activó ningún acceso con este pedido.</p>
            <p><Link className="btn primary" href={`/comprar?plan=${pedido.plan}${pedido.curso ? `&curso=${pedido.curso}` : ""}`}>Intentar de nuevo</Link></p>
          </>
        )}
      </div>
    </Sitio>
  );
}
