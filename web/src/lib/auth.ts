// Quién está leyendo. Una sola función, getUsuario(), para que el resto de la app no sepa qué proveedor hay detrás.
import "server-only";
import { cookies } from "next/headers";
import { auth0, auth0Activo } from "./auth0";
import { store } from "./store";
import type { Usuario } from "./tipos";

/** Login de desarrollo: solo sin Auth0 configurado y fuera de producción. */
export const modoDev = !auth0Activo && process.env.NODE_ENV !== "production";
export const COOKIE_DEV = "dev_usuario";

const vistos = new Set<string>(); // usuarios ya registrados en el store durante la vida de este proceso

export async function getUsuario(): Promise<Usuario | null> {
  let u: Usuario | null = null;
  if (auth0) {
    const s = await auth0.getSession();
    if (s?.user?.sub && s.user.email)
      u = { id: s.user.sub, email: String(s.user.email).toLowerCase(), nombre: s.user.name, verificado: Boolean(s.user.email_verified) };
  } else if (modoDev) {
    const email = (await cookies()).get(COOKIE_DEV)?.value?.toLowerCase();
    if (email) u = { id: `dev|${email}`, email, nombre: email.split("@")[0], verificado: true };
  }
  if (u && !vistos.has(`${u.id}:${u.email}`)) {
    await store.registrarUsuario(u);
    vistos.add(`${u.id}:${u.email}`);
  }
  return u;
}

/** Solo rutas internas: evita que `returnTo` se use para redirigir a otro sitio. */
export function rutaSegura(r: string | null | undefined, fallback = "/cuenta"): string {
  return r && r.startsWith("/") && !r.startsWith("//") && !r.includes("\\") ? r : fallback;
}

export function urlEntrar(returnTo = "/cuenta", registro = false): string {
  const r = encodeURIComponent(rutaSegura(returnTo));
  if (auth0Activo) return `/auth/login?returnTo=${r}${registro ? "&screen_hint=signup" : ""}`;
  return modoDev ? `/dev/entrar?returnTo=${r}` : "/";
}
export const urlSalir = () => (auth0Activo ? "/auth/logout" : "/api/dev/salir");

const ADMINS = (process.env.ADMIN_EMAILS ?? "").split(",").map((e) => e.trim().toLowerCase()).filter(Boolean);
/** Administrador = correo listado en ADMIN_EMAILS y verificado por el proveedor de identidad. */
export const esAdmin = (u: Usuario | null) => Boolean(u && u.verificado && ADMINS.includes(u.email));
