// Autenticación directa por correo y contraseña (sin redirecciones externas) respaldada por Supabase Auth.
import { createClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { COOKIE_SESION, crearCookieSesion, rutaSegura } from "@/lib/auth";
import { urlBase } from "@/lib/pagos";
import { store } from "@/lib/store";
import type { Usuario } from "@/lib/tipos";

export async function POST(req: Request) {
  const base = urlBase(req);
  const form = await req.formData();
  const modo = String(form.get("modo") ?? "entrar");
  const volver = rutaSegura(String(form.get("returnTo") ?? "/cuenta"));
  const email = String(form.get("email") ?? "").trim().toLowerCase();
  const password = String(form.get("password") ?? "");
  const nombre = String(form.get("nombre") ?? "").trim();

  const devolverError = (msg: string) =>
    NextResponse.redirect(
      new URL(`/entrar?returnTo=${encodeURIComponent(volver)}${modo === "registro" ? "&modo=registro" : ""}&error=${encodeURIComponent(msg)}`, base),
      303,
    );

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return devolverError("Escribe un correo válido.");
  if (password.length < 6) return devolverError("La contraseña debe tener al menos 6 caracteres.");

  const supaUrl = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SERVICE_ROLE;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? serviceKey;

  let usuario: Usuario;

  if (supaUrl && serviceKey && anonKey) {
    const admin = createClient(supaUrl, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } });
    const pub = createClient(supaUrl, anonKey, { auth: { persistSession: false, autoRefreshToken: false } });

    if (modo === "registro") {
      const { data, error } = await admin.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        user_metadata: { name: nombre || email.split("@")[0] },
      });
      if (error || !data.user) {
        const yaExiste = error?.message?.toLowerCase().includes("already") || error?.message?.toLowerCase().includes("registered");
        return devolverError(
          yaExiste
            ? "Ya existe una cuenta con ese correo. Cambia a «Iniciar sesión» o entra con Google."
            : `No se pudo crear la cuenta: ${error?.message ?? "intenta de nuevo"}`,
        );
      }
      const previo = await store.usuarioPorEmail(email);
      usuario = {
        id: previo?.id ?? `email|${data.user.id}`,
        email,
        nombre: nombre || email.split("@")[0],
        verificado: true,
      };
    } else {
      const { data, error } = await pub.auth.signInWithPassword({ email, password });
      if (error || !data.user) {
        return devolverError("Correo o contraseña incorrectos (si aún no tienes cuenta, créala en la pestaña «Crear cuenta»).");
      }
      const previo = await store.usuarioPorEmail(email);
      const metaNombre = typeof data.user.user_metadata?.name === "string" ? data.user.user_metadata.name : undefined;
      usuario = {
        id: previo?.id ?? `email|${data.user.id}`,
        email,
        nombre: metaNombre || email.split("@")[0],
        verificado: true,
      };
    }
  } else {
    // Modo local sin Supabase configurado
    const previo = await store.usuarioPorEmail(email);
    usuario = { id: previo?.id ?? `dev|${email}`, email, nombre: nombre || email.split("@")[0], verificado: true };
  }

  await store.registrarUsuario(usuario);
  const jar = await cookies();
  jar.set(COOKIE_SESION, crearCookieSesion(usuario), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 30 * 86400,
  });

  return NextResponse.redirect(new URL(volver, base), 303);
}
