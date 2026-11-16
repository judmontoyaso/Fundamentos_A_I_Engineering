// Página de destino del enlace para restablecer la contraseña (POST al confirmar).
import type { Metadata } from "next";
import Link from "next/link";
import { Sitio } from "@/components/Sitio";
import { leerTokenRecuperacion } from "@/lib/auth";

export const metadata: Metadata = { title: "Nueva contraseña", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ t?: string; error?: string }> };

export default async function Recuperar({ searchParams }: Props) {
  const { t, error } = await searchParams;
  const token = leerTokenRecuperacion(t);

  return (
    <Sitio>
      <div className="pagina" style={{ maxWidth: "28rem", paddingTop: "3.5rem" }}>
        <div className="caja auth-card">
          {token ? (
            <>
              <h1 style={{ fontSize: "1.45rem", margin: ".2rem 0 .5rem" }}>Asigna una nueva contraseña</h1>
              <p className="aviso" style={{ marginBottom: "1rem" }}>
                Cuenta: <b>{token.email}</b>
              </p>
              {error && (
                <div className="auth-error" role="alert">
                  <span className="estado no">error</span> {error}
                </div>
              )}
              <form className="form" method="post" action="/api/auth/recuperar">
                <input type="hidden" name="accion" value="confirmar" />
                <input type="hidden" name="t" value={t} />
                <label>
                  Nueva contraseña (mínimo 8 caracteres)
                  <input type="password" name="password" required minLength={8} autoComplete="new-password" placeholder="••••••••" />
                </label>
                <button className="btn primary" type="submit" style={{ width: "100%", textAlign: "center", padding: ".7rem 1rem" }}>
                  Guardar contraseña y entrar
                </button>
              </form>
            </>
          ) : (
            <>
              <h1 style={{ fontSize: "1.45rem", margin: ".2rem 0 .5rem" }}>El enlace venció o no es válido</h1>
              <p className="aviso" style={{ marginBottom: "1rem" }}>
                Los enlaces de restablecimiento duran 1 hora por seguridad. Solicita uno nuevo desde el inicio de sesión.
              </p>
              <Link className="btn primary" href="/entrar?modo=recuperar">Pedir nuevo enlace</Link>
            </>
          )}
        </div>
      </div>
    </Sitio>
  );
}
