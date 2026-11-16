// Página nativa de acceso: Google en 1 clic, correo/contraseña, registro y restablecimiento de clave.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { getUsuario, rutaSegura } from "@/lib/auth";
import { auth0Activo } from "@/lib/auth0";
import { cursos } from "@/lib/contenido";

export const metadata: Metadata = {
  title: "Entrar",
  robots: { index: false, follow: false },
};
export const dynamic = "force-dynamic";

type Props = { searchParams: Promise<{ returnTo?: string; modo?: string; error?: string; aviso?: string }> };

export default async function Entrar({ searchParams }: Props) {
  const sp = await searchParams;
  const volver = rutaSegura(sp.returnTo);
  const modo = sp.modo === "registro" ? "registro" : sp.modo === "recuperar" ? "recuperar" : "entrar";
  const esRegistro = modo === "registro";
  const esRecuperar = modo === "recuperar";
  const mostrarDemo = process.env.DESACTIVAR_DEMO !== "1";

  const usuario = await getUsuario();
  if (usuario) redirect(volver);

  const urlGoogle = `/auth/login?connection=google-oauth2&returnTo=${encodeURIComponent(volver)}`;

  return (
    <Sitio>
      <div className="pagina" style={{ maxWidth: "28rem", paddingTop: "3.5rem" }}>
        <div className="caja auth-card">
          <div className="auth-tabs">
            <Link
              className={"auth-tab" + (modo === "entrar" ? " active" : "")}
              href={`/entrar?returnTo=${encodeURIComponent(volver)}`}
            >
              Iniciar sesión
            </Link>
            <Link
              className={"auth-tab" + (esRegistro ? " active" : "")}
              href={`/entrar?returnTo=${encodeURIComponent(volver)}&modo=registro`}
            >
              Crear cuenta
            </Link>
          </div>

          <h1 style={{ fontSize: "1.45rem", margin: ".9rem 0 .25rem" }}>
            {esRegistro ? "Crea tu cuenta" : esRecuperar ? "Recuperar contraseña" : "Bienvenido de vuelta"}
          </h1>
          <p className="aviso" style={{ marginBottom: "1.1rem" }}>
            {esRecuperar
              ? "Te enviaremos un enlace temporal para asignar una contraseña nueva a tu cuenta."
              : `Guarda tu progreso en los ${cursos.length} cursos del catálogo, tus autoevaluaciones y tus certificados verificables.`}
          </p>

          {sp.error && (
            <div className="auth-error" role="alert">
              <span className="estado no">error</span> {sp.error}
            </div>
          )}
          {sp.aviso && (
            <div className="auth-ok" role="status">
              <span className="estado ok">listo</span> {sp.aviso}
            </div>
          )}

          {esRecuperar ? (
            <>
              <form className="form" method="post" action="/api/auth/recuperar">
                <input type="hidden" name="accion" value="solicitar" />
                <label>
                  Correo de tu cuenta
                  <input name="email" type="email" required autoComplete="email" placeholder="tu@correo.com" />
                </label>
                <button className="btn primary" type="submit" style={{ width: "100%", textAlign: "center", padding: ".7rem 1rem", marginTop: ".3rem" }}>
                  Enviar enlace de recuperación
                </button>
              </form>
              <p className="aviso" style={{ marginTop: "1rem", textAlign: "center" }}>
                <Link href={`/entrar?returnTo=${encodeURIComponent(volver)}`}>Volver a iniciar sesión</Link>
              </p>
            </>
          ) : (
            <>
              {auth0Activo && (
                <>
                  <a className="btn google-btn" href={urlGoogle}>
                    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
                      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
                      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
                      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
                      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
                    </svg>
                    <span>Continuar con Google</span>
                  </a>
                  <div className="auth-sep"><span>o con tu correo</span></div>
                </>
              )}

              <form className="form" method="post" action="/api/auth/correo">
                <input type="hidden" name="returnTo" value={volver} />
                <input type="hidden" name="modo" value={esRegistro ? "registro" : "entrar"} />

                {esRegistro && (
                  <label>
                    Nombre completo (para tus certificados)
                    <input
                      name="nombre"
                      type="text"
                      required
                      autoComplete="name"
                      placeholder="Tu nombre y apellido"
                    />
                  </label>
                )}

                <label>
                  Correo electrónico
                  <input
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    placeholder="tu@correo.com"
                  />
                </label>

                <label>
                  Contraseña {esRegistro && <span className="aviso">(mínimo 8 caracteres)</span>}
                  <input
                    name="password"
                    type="password"
                    required
                    minLength={esRegistro ? 8 : undefined}
                    autoComplete={esRegistro ? "new-password" : "current-password"}
                    placeholder="••••••••"
                  />
                </label>

                <button className="btn primary" type="submit" style={{ width: "100%", textAlign: "center", padding: ".7rem 1rem", marginTop: ".3rem" }}>
                  {esRegistro ? "Crear mi cuenta" : "Entrar con mi correo"}
                </button>
              </form>

              {!esRegistro && (
                <p className="aviso" style={{ marginTop: ".8rem", textAlign: "center" }}>
                  <Link href={`/entrar?returnTo=${encodeURIComponent(volver)}&modo=recuperar`}>
                    ¿Olvidaste tu contraseña?
                  </Link>
                </p>
              )}

              {!esRegistro && mostrarDemo && (
                <>
                  <div className="auth-sep"><span>o prueba el entorno demo</span></div>
                  <form method="post" action="/api/auth/correo">
                    <input type="hidden" name="returnTo" value={volver} />
                    <input type="hidden" name="modo" value="entrar" />
                    <input type="hidden" name="email" value="demo@iaenproduccion.com" />
                    <input type="hidden" name="password" value="Demo2026!" />
                    <button
                      type="submit"
                      className="btn"
                      style={{ width: "100%", textAlign: "center", padding: ".6rem .9rem", fontSize: ".84rem" }}
                    >
                      Entrar con usuario de prueba (cursos completados + certificados)
                    </button>
                  </form>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </Sitio>
  );
}
