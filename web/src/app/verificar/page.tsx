// Destino del enlace de verificación. Solo muestra un botón: la verificación ocurre al enviarlo (POST).
import type { Metadata } from "next";
import Link from "next/link";
import { Sitio } from "@/components/Sitio";
import { leerTokenVerificacion } from "@/lib/auth";

export const metadata: Metadata = { title: "Confirmar correo", robots: { index: false } };
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ t?: string }> };

export default async function Verificar({ searchParams }: Props) {
  const { t } = await searchParams;
  const token = leerTokenVerificacion(t);

  return (
    <Sitio>
      <div className="pagina" style={{ maxWidth: "28rem", paddingTop: "3.5rem" }}>
        <div className="caja auth-card">
          {token ? (
            <>
              <h1 style={{ fontSize: "1.45rem", margin: ".2rem 0 .5rem" }}>Confirma tu correo</h1>
              <p className="aviso" style={{ marginBottom: "1.1rem" }}>
                Vas a confirmar que <b>{token.email}</b> es tu correo. Si no creaste esta cuenta, cierra esta página.
              </p>
              <form className="form" method="post" action="/api/auth/verificar">
                <input type="hidden" name="accion" value="confirmar" />
                <input type="hidden" name="t" value={t} />
                <button className="btn primary" type="submit" style={{ width: "100%", textAlign: "center", padding: ".7rem 1rem" }}>
                  Sí, es mi correo
                </button>
              </form>
            </>
          ) : (
            <>
              <h1 style={{ fontSize: "1.45rem", margin: ".2rem 0 .5rem" }}>El enlace no es válido</h1>
              <p className="aviso">
                Puede haber vencido (vale 48 horas) o estar incompleto. Entra a <Link href="/cuenta">tu cuenta</Link> y
                pide que te lo enviemos otra vez.
              </p>
            </>
          )}
        </div>
      </div>
    </Sitio>
  );
}
