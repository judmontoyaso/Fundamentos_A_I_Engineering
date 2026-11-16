// Resumen de la compra, aplicación de cupones de descuento (incluso 100 % gratis) y elección del medio de pago.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso, cursos } from "@/lib/contenido";
import { aplicarDescuento, validarCupon } from "@/lib/cupones";
import { proveedoresActivos } from "@/lib/pagos";
import { MONEDA, PLANES, esPlan, formatoMonto, montoDe } from "@/lib/planes";

export const metadata: Metadata = { title: "Comprar", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

const TRANSFERENCIA = process.env.PAGO_MANUAL_INSTRUCCIONES ?? "";

type Props = { searchParams: Promise<{ plan?: string; curso?: string; cupon?: string; error?: string }> };

export default async function Comprar({ searchParams }: Props) {
  const sp = await searchParams;
  if (!esPlan(sp.plan)) redirect("/#planes");
  const plan = PLANES[sp.plan];
  const elegido = sp.curso ? curso(sp.curso) : null;
  const codigoRaw = (sp.cupon ?? "").trim().toUpperCase();
  const aqui = `/comprar?plan=${plan.id}${elegido ? `&curso=${elegido.id}` : ""}${codigoRaw ? `&cupon=${encodeURIComponent(codigoRaw)}` : ""}`;

  const usuario = await getUsuario();
  if (!usuario) redirect(urlEntrar(aqui, true));

  const montoBase = montoDe(plan.id);
  const pasarelas = proveedoresActivos();

  const resCupon = codigoRaw ? await validarCupon(codigoRaw, plan.id, elegido?.id ?? null) : null;
  const descuentoPct = resCupon && resCupon.ok ? resCupon.porcentaje : 0;
  const montoFinal = montoBase !== null ? aplicarDescuento(montoBase, descuentoPct) : null;
  const usdFinal = aplicarDescuento(plan.usd, descuentoPct);
  const esGratisConCupon = descuentoPct >= 100;

  return (
    <Sitio>
      <div className="pagina">
        <h1>Confirmar compra</h1>
        <p className="muted">Compras como <b>{usuario.email}</b>. El acceso queda ligado de inmediato a esta cuenta.</p>
        {sp.error && <div className="caja" role="alert"><span className="estado no">error</span> {sp.error}</div>}

        {/* Formulario GET para validar cupón al instante */}
        <form className="caja" method="get" action="/comprar" style={{ display: "grid", gap: ".6rem" }}>
          <input type="hidden" name="plan" value={plan.id} />
          {elegido && <input type="hidden" name="curso" value={elegido.id} />}
          <div className="fila">
            <div>
              <b>¿Tienes un cupón de descuento o beca?</b>
              <div className="aviso">Aplica descuentos parciales o acceso 100 % gratuito a un curso, mes o plan.</div>
            </div>
            <div style={{ display: "flex", gap: ".45rem", alignItems: "center", flexWrap: "wrap" }}>
              <input
                type="text"
                name="cupon"
                defaultValue={codigoRaw}
                placeholder="Ej. LANZAMIENTO50"
                style={{
                  font: "600 .88rem 'IBM Plex Mono', monospace",
                  textTransform: "uppercase",
                  padding: ".48rem .7rem",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg)",
                  color: "var(--fg)",
                  width: "12rem",
                }}
              />
              <button className="btn" type="submit">Aplicar cupón</button>
              {codigoRaw && (
                <Link className="btn" href={`/comprar?plan=${plan.id}${elegido ? `&curso=${elegido.id}` : ""}`}>
                  Quitar
                </Link>
              )}
            </div>
          </div>
          {resCupon && (
            <div>
              {resCupon.ok ? (
                <span className="estado ok">
                  cupón {resCupon.cupon.codigo} aplicado · -{resCupon.porcentaje} %
                </span>
              ) : (
                <span className="estado no">{resCupon.error}</span>
              )}
            </div>
          )}
        </form>

        <form className="form" method="post" action="/api/checkout">
          <input type="hidden" name="plan" value={plan.id} />
          {resCupon?.ok && <input type="hidden" name="cupon" value={resCupon.cupon.codigo} />}
          <div className="caja">
            <div className="fila">
              <div>
                <b>Plan {plan.nombre.toLowerCase()}</b>
                <div className="aviso">{plan.resumen}. Pago único · no se renueva solo.</div>
              </div>
              <div style={{ textAlign: "right" }}>
                {descuentoPct > 0 && montoBase !== null && (
                  <div className="aviso" style={{ textDecoration: "line-through" }}>
                    {formatoMonto(montoBase, MONEDA)}
                  </div>
                )}
                <b className="mono" style={{ fontSize: "1.12rem", color: esGratisConCupon ? "var(--ok)" : undefined }}>
                  {esGratisConCupon
                    ? `GRATIS (0 ${MONEDA})`
                    : montoFinal !== null
                      ? formatoMonto(montoFinal, MONEDA)
                      : `${usdFinal} USD`}
                </b>
              </div>
            </div>
            {MONEDA !== "USD" && montoFinal !== null && !esGratisConCupon && (
              <p className="aviso">Precio de referencia: {usdFinal} USD. Se cobra en {MONEDA}.</p>
            )}
            {plan.id === "curso" && (
              <label style={{ marginTop: ".8rem" }}>Curso
                <select name="curso" defaultValue={elegido?.id ?? ""} required>
                  <option value="" disabled>Elige un curso</option>
                  {cursos.map((c) => <option key={c.id} value={c.id}>{c.titulo}</option>)}
                </select>
              </label>
            )}
          </div>

          {esGratisConCupon ? (
            <div className="caja fila">
              <div>
                <b>Activación directa con cupón ({resCupon?.ok ? resCupon.cupon.codigo : codigoRaw})</b>
                <div className="aviso">100 % de descuento · No necesitas tarjeta ni pasarela de pago.</div>
              </div>
              <button className="btn primary grande" name="proveedor" value="cupon">
                Canjear cupón y activar acceso gratis
              </button>
            </div>
          ) : montoFinal === null ? (
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

        {TRANSFERENCIA && !esGratisConCupon && (
          <>
            <h2>Pago por transferencia</h2>
            <div className="caja" style={{ whiteSpace: "pre-wrap" }}>{TRANSFERENCIA}
              <p className="aviso">Activamos tu acceso manualmente cuando confirmamos el pago. Incluye tu correo ({usuario.email}) en el comprobante.</p>
            </div>
          </>
        )}
        <p className="aviso">Al continuar aceptas los <Link href="/terminos">términos y la política de reembolso</Link>.</p>
      </div>
    </Sitio>
  );
}
