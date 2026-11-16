// Autenticación directa por correo y contraseña (sin redirecciones externas) respaldada por Supabase Auth.
//
// Crear una cuenta NO prueba que el correo sea de quien lo escribe. Por eso la cuenta nace sin verificar:
// puede estudiar y comprar con su propio id, pero no hereda la cuenta de nadie ni puede ser administradora
// hasta que abre el enlace que se le envía (ver /api/auth/verificar).
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { COOKIE_SESION, OPCIONES_COOKIE, crearCookieSesion, crearTokenVerificacion, rutaSegura } from "@/lib/auth";
import { MAX_CLAVE, validarClaveNueva } from "@/lib/clave";
import { correoActivo, enviarVerificacion } from "@/lib/correo";
import { ipDe, permitido } from "@/lib/limite";
import { urlBase } from "@/lib/pagos";
import { clientesAuth, estaVerificado } from "@/lib/supabase-auth";
import type { Usuario } from "@/lib/tipos";

export async function POST(req: Request) {
  const base = urlBase(req);
  const form = await req.formData();
  const modo = String(form.get("modo") ?? "entrar") === "registro" ? "registro" : "entrar";
  const volver = rutaSegura(String(form.get("returnTo") ?? "/cuenta"));
  const email = String(form.get("email") ?? "").trim().toLowerCase();
  const password = String(form.get("password") ?? "");
  const nombre = String(form.get("nombre") ?? "").trim().slice(0, 80);

  const devolverError = (msg: string) =>
    NextResponse.redirect(
      new URL(`/entrar?returnTo=${encodeURIComponent(volver)}${modo === "registro" ? "&modo=registro" : ""}&error=${encodeURIComponent(msg)}`, base),
      303,
    );

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254) return devolverError("Escribe un correo válido.");
  if (!password || password.length > MAX_CLAVE) return devolverError("Escribe tu contraseña.");
  if (modo === "registro") {
    const errClave = await validarClaveNueva(password);
    if (errClave) return devolverError(errClave);
  }

  // Freno a la fuerza bruta y al registro masivo: por origen y, al entrar, también por cuenta.
  const ip = ipDe(req);
  const dentro = modo === "registro"
    ? permitido(`registro:${ip}`, 5, 3600_000)
    : permitido(`entrar:${ip}`, 30, 600_000) && permitido(`entrar:${email}`, 8, 600_000);
  if (!dentro) return devolverError("Demasiados intentos. Espera unos minutos y vuelve a probar.");

  const supa = clientesAuth();
  let usuario: Usuario;
  let avisarVerificacion: string | null = null; // uid de Supabase al que hay que enviarle el enlace

  if (supa) {
    if (modo === "registro") {
      // `email_confirm: true` solo le dice a Supabase que deje entrar con contraseña; no cuenta como verificación.
      const { data, error } = await supa.admin.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        user_metadata: { name: nombre || email.split("@")[0] },
      });
      if (error || !data.user) {
        const m = error?.message?.toLowerCase() ?? "";
        return devolverError(
          m.includes("already") || m.includes("registered")
            ? "Ya existe una cuenta con ese correo. Cambia a «Iniciar sesión» o entra con Google."
            : "No se pudo crear la cuenta. Revisa los datos e intenta de nuevo.",
        );
      }
      usuario = { id: `email|${data.user.id}`, email, nombre: nombre || email.split("@")[0], verificado: false };
      avisarVerificacion = data.user.id;
    } else {
      const { data, error } = await supa.pub.auth.signInWithPassword({ email, password });
      if (error || !data.user) {
        return devolverError("Correo o contraseña incorrectos (si aún no tienes cuenta, créala en la pestaña «Crear cuenta»).");
      }
      const metaNombre = typeof data.user.user_metadata?.name === "string" ? data.user.user_metadata.name : undefined;
      usuario = {
        id: `email|${data.user.id}`,
        email,
        nombre: metaNombre || email.split("@")[0],
        verificado: estaVerificado(data.user.app_metadata),
      };
    }
  } else if (process.env.NODE_ENV !== "production") {
    // Desarrollo local sin Supabase: entra cualquier correo. Nunca en producción.
    usuario = { id: `dev|${email}`, email, nombre: nombre || email.split("@")[0], verificado: true };
  } else {
    return devolverError("El acceso por correo no está disponible en este momento. Entra con Google.");
  }

  // La fila en `curso.usuarios` la crea getUsuario() en la siguiente petición, ya con las reglas de unificación.
  const jar = await cookies();
  jar.set(COOKIE_SESION, crearCookieSesion(usuario), OPCIONES_COOKIE);

  if (avisarVerificacion && correoActivo) {
    const enlace = `${base}/verificar?t=${encodeURIComponent(crearTokenVerificacion(avisarVerificacion, email))}`;
    await enviarVerificacion(email, usuario.nombre, enlace);
  }

  return NextResponse.redirect(new URL(volver, base), 303);
}
