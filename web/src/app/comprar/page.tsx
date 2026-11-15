// Resumen de la compra y elección del medio de pago.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso, cursos } from "@/lib/contenido";
import { proveedoresActivos } from "@/lib/pagos";
import { MONEDA, PLANES, esPlan, formatoMonto, montoDe } from "@/lib/planes";

export const metadata: Metadata = { title: "Comprar" };
export const dynamic = "force-dynamic";

const TRANSFERENCIA = process.env.PAGO_MANUAL_INSTRUCCIONES ?? "";

type Props = { searchParams: Promise<{ plan?: string; curso?: string; error?: string }> };

export default async function Comprar({ searchParams }: Props) {
  const sp = await searchParams;
  if (!esPlan(sp.plan)) redirect("/#planes");
  const plan = PLANES[sp.plan];
  const elegido = sp.curso ? curso(sp.curso) : null;
  const aqui = `/comprar?plan=${plan.id}${elegido ? `&curso=${elegido.id}` : ""}`;

  const usuario = await getUsuario();
  if (!usuario) redirect(urlEntrar(aqui, true));

  const monto = montoDe(plan.id);
  const pasarelas = proveedoresActivos();

  return (
    <Sitio>
      <div className="pagina">
        <h1>Confirmar compra</h1>
        <p className="muted">Compras como {usuario.email}. El acceso queda ligado a esta cuenta.</p>
        {sp.error && <div className="caja" role="alert"><span className="estado no">error</span> {sp.error}</div>}

        <form className="form" method="post" action="/api/checkout">
          <input type="hidden" name="plan" value={plan.id} />
          <div className="caja">
            <div className="fila">
              <div><b>Plan {plan.nombre.toLowerCase()}</b><div className="aviso">{plan.resumen}. No se renueva solo.</div></div>
              <b className="mono">{monto !== null ? formatoMonto(monto, MONEDA) : `${plan.usd} USD`}</b>
            </div>
            {MONEDA !== "USD" && monto !== null && <p className="aviso">Precio de referencia: {plan.usd} USD. Se cobra en {MONEDA}.</p>}
            {plan.id === "curso" && (
              <label style={{ marginTop: ".8rem" }}>Curso
                <select name="curso" defaultValue={elegido?.id ?? ""} required>
                  <option value="" disabled>Elige un curso</option>
                  {cursos.map((c) => <option key={c.id} value={c.id}>{c.titulo}</option>)}
                </select>
              </label>
            )}
          </div>

          {monto === null ? (
            <div className="caja">El precio de este plan todavía no está configurado. Vuelve pronto.</div>
          ) : pasarelas.length === 0 && !TRANSFERENCIA ? (
            <div className="caja">Los pagos en línea aún no están habilitados. Vuelve pronto.</div>
          ) : (
            <>
              {pasarelas.length > 0 && <h2>Medio de pago</h2>}
              {pasarelas.map((p) => (
                <div className="caja fila" key={p.id}>
                  <div><b>{p.nombre}</b><div className="aviso">{p.medios}</div></div>
                  <button className="btn primary" name="proveedor" value={p.id}>Pagar con {p.nombre}</button>
                </div>
              ))}
            </>
          )}
        </form>

        {TRANSFERENCIA && (
          <>
            <h2>Pago por transferencia</h2>
            <div className="caja" style={{ whiteSpace: "pre-wrap" }}>{TRANSFERENCIA}
              <p className="aviso">Activamos tu acceso manualmente cuando confirmamos el pago. Incluye tu correo ({usuario.email}) en el comprobante.</p>
            </div>
          </>
        )}
        <p className="aviso">Al pagar aceptas los <Link href="/terminos">términos y la política de reembolso</Link>.</p>
      </div>
    </Sitio>
  );
}
