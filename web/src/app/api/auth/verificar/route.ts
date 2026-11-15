// Verificación del correo de las cuentas de correo y contraseña.
//   accion=confirmar  → llega desde el botón de /verificar con el token del enlace enviado por correo.
//   accion=reenviar   → la persona con sesión pide que se le envíe otra vez el enlace.
// Es un POST a propósito: los filtros de correo que "abren" los enlaces para revisarlos no envían formularios,
// así que no pueden verificar la cuenta por su dueño.
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { COOKIE_SESION, OPCIONES_COOKIE, crearCookieSesion, crearTokenVerificacion, leerTokenVerificacion, sesionCorreo } from "@/lib/auth";
import { correoActivo, enviarVerificacion } from "@/lib/correo";
import { permitido } from "@/lib/limite";
import { urlBase } from "@/lib/pagos";
import { marcarCorreoVerificado } from "@/lib/supabase-auth";

export async function POST(req: Request) {
  const base = urlBase(req);
  const ir = (ruta: string) => NextResponse.redirect(new URL(ruta, base), 303);
  const form = await req.formData();
  const propia = await sesionCorreo();

  if (String(form.get("accion")) === "reenviar") {
    if (!propia || !propia.id.startsWith("email|")) return ir("/entrar?returnTo=%2Fcuenta");
    if (propia.verificado) return ir("/cuenta?correo=verificado");
    if (!correoActivo) return ir("/cuenta?correo=sin-servicio");
    if (!permitido(`verificar:${propia.id}`, 3, 3600_000)) return ir("/cuenta?correo=espera");
    const uid = propia.id.slice("email|".length);
    const enlace = `${base}/verificar?t=${encodeURIComponent(crearTokenVerificacion(uid, propia.email))}`;
    const ok = await enviarVerificacion(propia.email, propia.nombre, enlace);
    return ir(`/cuenta?correo=${ok ? "enviado" : "fallo"}`);
  }

  const token = leerTokenVerificacion(String(form.get("t") ?? ""));
  if (!token?.uid || !token.email) return ir("/verificar");
  if (!(await marcarCorreoVerificado(token.uid, token.email))) return ir("/verificar");

  // Si quien confirma tiene abierta la sesión de esa misma cuenta, la sesión pasa a verificada ya.
  if (propia && propia.id === `email|${token.uid}` && propia.email === token.email) {
    (await cookies()).set(COOKIE_SESION, crearCookieSesion({ ...propia, verificado: true }), OPCIONES_COOKIE);
  }
  return ir("/cuenta?correo=verificado");
}
