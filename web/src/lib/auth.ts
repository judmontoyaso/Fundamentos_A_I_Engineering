// Quién está leyendo. Una sola función, getUsuario(), para que el resto de la app no sepa qué proveedor hay detrás.
// Soporta:
//   1. Sesión propia por correo y contraseña (cookie firmada `ia_sesion`, validada contra Supabase Auth).
//   2. Sesión de Auth0 (Google OAuth directo).
//   3. Unifica la cuenta por correo en `curso.usuarios` para que entrar con Google o con correo comparta
//      progreso, compras y certificados, pero solo entre identidades con el correo verificado.
import "server-only";
import { cookies } from "next/headers";
import { auth0, auth0Activo } from "./auth0";
import { firmarDatos, leerDatos } from "./secreto";
import { store } from "./store";
import { correoVerificado } from "./supabase-auth";
import type { Usuario } from "./tipos";

/** Login de desarrollo: solo sin Auth0 ni Supabase configurados y fuera de producción. */
export const modoDev = !auth0Activo && !process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NODE_ENV !== "production";
export const COOKIE_DEV = "dev_usuario";
export const COOKIE_SESION = "ia_sesion";
export const OPCIONES_COOKIE = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
  maxAge: 30 * 86400,
};

const vistos = new Set<string>(); // usuarios ya registrados en el store durante la vida de este proceso
const verificadas = new Set<string>(); // identidades de correo y contraseña ya comprobadas como verificadas

// "ses2": las cookies emitidas antes (etiqueta "ses") declaraban verificado cualquier correo y dejan de valer.
const ETIQUETA_SESION = "ses2";

type DatosSesion = { id: string; email: string; nombre?: string; verificado?: boolean; exp: number };

export function crearCookieSesion(u: Usuario): string {
  return firmarDatos(ETIQUETA_SESION, {
    id: u.id, email: u.email.toLowerCase(), nombre: u.nombre, verificado: u.verificado, exp: Date.now() + 30 * 86400_000,
  });
}

export function leerCookieSesion(valor: string | undefined): Usuario | null {
  const d = leerDatos<DatosSesion>(ETIQUETA_SESION, valor);
  if (!d?.id || !d.email) return null;
  return { id: String(d.id), email: String(d.email).toLowerCase(), nombre: d.nombre ? String(d.nombre) : undefined, verificado: d.verificado === true };
}

/** La sesión de correo y contraseña tal como se emitió (con su id propio `email|...`), sin unificar cuentas. */
export async function sesionCorreo(): Promise<Usuario | null> {
  return leerCookieSesion((await cookies()).get(COOKIE_SESION)?.value);
}

/** Enlace de verificación de correo: lo firma el servidor y vale 48 horas. */
export const crearTokenVerificacion = (uid: string, email: string) =>
  firmarDatos("ver", { uid, email: email.toLowerCase(), exp: Date.now() + 48 * 3600_000 });
export const leerTokenVerificacion = (t: string | null | undefined) =>
  leerDatos<{ uid: string; email: string; exp: number }>("ver", t);

/** ¿La cuenta guardada con este id nació de un correo comprobado? Solo esas pueden recibir otra identidad. */
async function identidadVerificada(id: string, email: string): Promise<boolean> {
  if (id.startsWith("google-oauth2|")) return true; // Google responde por el correo
  if (verificadas.has(id)) return true;
  if (!id.startsWith("email|")) return false; // p. ej. alta por base de datos de Auth0: no consta
  const ok = await correoVerificado(id.slice("email|".length), email);
  if (ok) verificadas.add(id);
  return ok;
}

export async function getUsuario(): Promise<Usuario | null> {
  const jar = await cookies();
  let u: Usuario | null = leerCookieSesion(jar.get(COOKIE_SESION)?.value);

  if (!u && auth0) {
    const s = await auth0.getSession();
    if (s?.user?.sub && s.user.email) {
      const email = String(s.user.email).toLowerCase();
      u = { id: s.user.sub, email, nombre: s.user.name, verificado: Boolean(s.user.email_verified) };
    }
  } else if (!u && modoDev) {
    const email = jar.get(COOKIE_DEV)?.value?.toLowerCase();
    if (email) u = { id: `dev|${email}`, email, nombre: email.split("@")[0], verificado: true };
  }

  if (u) {
    // Unificación por correo (entrar con Google o con contraseña y ver el mismo progreso y compras).
    // Solo ocurre si AMBOS lados tienen el correo comprobado: quien entra y la cuenta más antigua que lo recibe.
    // Sin esa condición, registrar el correo de otra persona bastaba para heredar su cuenta.
    const propioId = u.id;
    const filas = await store.usuariosPorEmail(u.email); // de la más antigua a la más reciente
    let fila = filas.find((f) => f.id === propioId) ?? null;
    if (u.verificado) {
      for (const f of filas) {
        if (f.id === propioId) break; // la propia ya es la más antigua con el correo comprobado
        if (await identidadVerificada(f.id, u.email)) {
          fila = f;
          u.id = f.id;
          break;
        }
      }
    }
    if (fila?.nombre) u.nombre = fila.nombre;

    const clave = `${u.id}:${u.email}:${u.nombre ?? ""}`;
    if (!vistos.has(clave)) {
      await store.registrarUsuario(u);
      vistos.add(clave);
    }
  }
  return u;
}

/** Solo rutas internas: evita que `returnTo` se use para redirigir a otro sitio. */
export function rutaSegura(r: string | null | undefined, fallback = "/cuenta"): string {
  return r && r.startsWith("/") && !r.startsWith("//") && !r.includes("\\") ? r : fallback;
}

export function urlEntrar(returnTo = "/cuenta", registro = false): string {
  const r = encodeURIComponent(rutaSegura(returnTo));
  return `/entrar?returnTo=${r}${registro ? "&modo=registro" : ""}`;
}
export const urlSalir = () => "/api/auth/salir";

const ADMINS = (process.env.ADMIN_EMAILS ?? "").split(",").map((e) => e.trim().toLowerCase()).filter(Boolean);
/** Administrador = correo listado en ADMIN_EMAILS y verificado por el proveedor de identidad. */
export const esAdmin = (u: Usuario | null) => Boolean(u && u.verificado && ADMINS.includes(u.email));
