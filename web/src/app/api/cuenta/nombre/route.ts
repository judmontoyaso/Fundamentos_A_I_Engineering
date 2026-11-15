// Permite al estudiante actualizar su nombre completo para que aparezca en sus certificados.
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { COOKIE_SESION, crearCookieSesion, getUsuario, leerCookieSesion } from "@/lib/auth";
import { urlBase } from "@/lib/pagos";
import { store } from "@/lib/store";

export async function POST(req: Request) {
  const base = urlBase(req);
  const usuario = await getUsuario();
  if (!usuario) return NextResponse.redirect(new URL("/entrar?returnTo=%2Fcuenta", base), 303);

  const form = await req.formData();
  const nombre = String(form.get("nombre") ?? "").trim().slice(0, 80);
  if (nombre) {
    const actualizado = { ...usuario, nombre };
    await store.registrarUsuario(actualizado);
    const jar = await cookies();
    if (leerCookieSesion(jar.get(COOKIE_SESION)?.value)) {
      jar.set(COOKIE_SESION, crearCookieSesion(actualizado), {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: 30 * 86400,
      });
    }
  }
  return NextResponse.redirect(new URL("/cuenta", base), 303);
}
