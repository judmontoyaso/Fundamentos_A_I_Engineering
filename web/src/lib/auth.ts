// Quién está leyendo. Una sola función, getUsuario(), para que el resto de la app no sepa qué proveedor hay detrás.
// Soporta:
//   1. Sesión propia por correo y contraseña (cookie firmada `ia_sesion`, validada contra Supabase Auth).
//   2. Sesión de Auth0 (Google OAuth directo).
//   3. En ambos casos unifica la cuenta por correo en `curso.usuarios` para que entrar con Google o con correo
//      comparta el mismo progreso, compras y certificados.
import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import { auth0, auth0Activo } from "./auth0";
import { store } from "./store";
import type { Usuario } from "./tipos";

/** Login de desarrollo: solo sin Auth0 ni Supabase configurados y fuera de producción. */
export const modoDev = !auth0Activo && !process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NODE_ENV !== "production";
export const COOKIE_DEV = "dev_usuario";
export const COOKIE_SESION = "ia_sesion";

const vistos = new Set<string>(); // usuarios ya registrados en el store durante la vida de este proceso

function secretoSesion(): string {
  return process.env.AUTH0_SECRET || process.env.SERVICE_ROLE || process.env.SUPABASE_SERVICE_ROLE_KEY || "dev-secret-ia-en-produccion";
}

function firmarToken(payloadB64: string): string {
  return createHmac("sha256", secretoSesion()).update(`ses:${payloadB64}`).digest("base64url");
}

export function crearCookieSesion(u: Usuario): string {
  const payload = Buffer.from(
    JSON.stringify({ id: u.id, email: u.email.toLowerCase(), nombre: u.nombre, verificado: u.verificado, exp: Date.now() + 30 * 86400_000 }),
    "utf8",
  ).toString("base64url");
  return `${payload}.${firmarToken(payload)}`;
}

export function leerCookieSesion(valor: string | undefined): Usuario | null {
  if (!valor) return null;
  const [payload, firma] = valor.split(".");
  if (!payload || !firma) return null;
  const esperada = firmarToken(payload);
  const a = Buffer.from(esperada);
  const b = Buffer.from(firma);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const d = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!d?.id || !d?.email || (d.exp && Date.now() > d.exp)) return null;
    return { id: String(d.id), email: String(d.email).toLowerCase(), nombre: d.nombre ? String(d.nombre) : undefined, verificado: Boolean(d.verificado) };
  } catch {
    return null;
  }
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
    // Si ya existe un usuario con este mismo correo (p. ej. entró antes por correo y ahora por Google, o al revés),
    // conservamos su id original en la base para no dividir su progreso ni sus compras.
    const existente = await store.usuarioPorEmail(u.email);
    if (existente) {
      u.id = existente.id;
      if (existente.nombre) u.nombre = existente.nombre;
    }

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
