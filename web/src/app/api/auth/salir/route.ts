// Cierra tanto la sesión por correo (`ia_sesion`) como la sesión de Auth0 si existiera.
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { COOKIE_DEV, COOKIE_SESION } from "@/lib/auth";
import { auth0 } from "@/lib/auth0";
import { urlBase } from "@/lib/pagos";

export async function GET(req: Request) {
  const base = urlBase(req);
  const jar = await cookies();
  jar.delete(COOKIE_SESION);
  jar.delete(COOKIE_DEV);

  if (auth0) {
    const s = await auth0.getSession();
    if (s) return NextResponse.redirect(new URL("/auth/logout", base), 303);
  }
  return NextResponse.redirect(new URL("/", base), 303);
}
