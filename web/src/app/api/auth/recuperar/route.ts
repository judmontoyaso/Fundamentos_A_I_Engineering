// Solicitud y confirmación de restablecimiento de contraseña para cuentas con correo y contraseña.
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  COOKIE_SESION,
  OPCIONES_COOKIE,
  crearCookieSesion,
  crearTokenRecuperacion,
  leerTokenRecuperacion,
} from "@/lib/auth";
import { validarClaveNueva } from "@/lib/clave";
import { correoActivo, enviarRecuperacion } from "@/lib/correo";
import { ipDe, permitido } from "@/lib/limite";
import { urlBase } from "@/lib/pagos";
import { store } from "@/lib/store";
import { MARCA_VERIFICADO, clientesAuth } from "@/lib/supabase-auth";

async function buscarUsuarioCorreo(email: string): Promise<{ uid: string; nombre?: string } | null> {
  const supa = clientesAuth();
  if (!supa) return null;

  const filas = await store.usuariosPorEmail(email);
  const deCorreo = filas.find((f) => f.id.startsWith("email|"));
  if (deCorreo) {
    const uid = deCorreo.id.slice("email|".length);
    const { data } = await supa.admin.auth.admin.getUserById(uid);
    if (data.user && data.user.email?.toLowerCase() === email) {
      const metaNombre = typeof data.user.user_metadata?.name === "string" ? data.user.user_metadata.name : undefined;
      return { uid, nombre: deCorreo.nombre ?? metaNombre };
    }
  }

  const { data } = await supa.admin.auth.admin.listUsers({ perPage: 1000 });
  const match = data.users.find((u) => u.email?.toLowerCase() === email && (u.app_metadata?.provider === "email" || u.identities?.some((i) => i.provider === "email")));
  if (!match) return null;
  const metaNombre = typeof match.user_metadata?.name === "string" ? match.user_metadata.name : undefined;
  return { uid: match.id, nombre: metaNombre };
}

export async function POST(req: Request) {
  const base = urlBase(req);
  const form = await req.formData();
  const accion = String(form.get("accion") ?? "");

  if (accion === "solicitar") {
    const email = String(form.get("email") ?? "").trim().toLowerCase();
    const volver = (msg: string) =>
      NextResponse.redirect(new URL(`/entrar?modo=recuperar&aviso=${encodeURIComponent(msg)}`, base), 303);

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.redirect(new URL("/entrar?modo=recuperar&error=Escribe+un+correo+v%C3%A1lido.", base), 303);
    }
    if (!correoActivo) {
      return NextResponse.redirect(
        new URL("/entrar?modo=recuperar&error=El+restablecimiento+por+correo+a%C3%BAn+no+est%C3%A1+habilitado.+Entra+con+Google+o+escribe+a+soporte.", base),
        303,
      );
    }
    const ip = ipDe(req);
    if (!permitido(`rec:${ip}`, 6, 3600_000) || !permitido(`rec:${email}`, 3, 3600_000)) {
      return NextResponse.redirect(new URL("/entrar?modo=recuperar&error=Demasiados+intentos.+Espera+una+hora+antes+de+volver+a+pedirlo.", base), 303);
    }

    const hallado = await buscarUsuarioCorreo(email);
    if (hallado) {
      const enlace = `${base}/recuperar?t=${encodeURIComponent(crearTokenRecuperacion(hallado.uid, email))}`;
      await enviarRecuperacion(email, hallado.nombre, enlace);
    }
    // Respuesta neutra para no revelar si un correo existe en la base de datos.
    return volver("Si existe una cuenta por correo con esa dirección, te enviamos un enlace válido por 1 hora.");
  }

  if (accion === "confirmar") {
    const rawT = String(form.get("t") ?? "");
    const token = leerTokenRecuperacion(rawT);
    const password = String(form.get("password") ?? "");
    if (!token) return NextResponse.redirect(new URL("/recuperar", base), 303);
    const errClave = await validarClaveNueva(password);
    if (errClave) {
      return NextResponse.redirect(
        new URL(`/recuperar?t=${encodeURIComponent(rawT)}&error=${encodeURIComponent(errClave)}`, base),
        303,
      );
    }

    const supa = clientesAuth();
    if (!supa) return NextResponse.redirect(new URL("/entrar?error=Servicio+no+disponible.", base), 303);
    const { data: userData } = await supa.admin.auth.admin.getUserById(token.uid);
    if (!userData.user || userData.user.email?.toLowerCase() !== token.email.toLowerCase()) {
      return NextResponse.redirect(new URL("/recuperar", base), 303);
    }

    const { error } = await supa.admin.auth.admin.updateUserById(token.uid, {
      password,
      app_metadata: { ...(userData.user.app_metadata ?? {}), [MARCA_VERIFICADO]: true },
    });
    if (error) {
      return NextResponse.redirect(
        new URL(`/recuperar?t=${encodeURIComponent(rawT)}&error=${encodeURIComponent("No se pudo actualizar la contraseña. Intenta de nuevo.")}`, base),
        303,
      );
    }

    const metaNombre = typeof userData.user.user_metadata?.name === "string" ? userData.user.user_metadata.name : undefined;
    const jar = await cookies();
    jar.set(
      COOKIE_SESION,
      crearCookieSesion({
        id: `email|${token.uid}`,
        email: token.email,
        nombre: metaNombre || token.email.split("@")[0],
        verificado: true,
      }),
      OPCIONES_COOKIE,
    );
    return NextResponse.redirect(new URL("/cuenta?correo=clave-actualizada", base), 303);
  }

  return NextResponse.redirect(new URL("/entrar", base), 303);
}
