// Supabase Auth como almacén de contraseñas del acceso por correo. La verificación del correo es nuestra:
// se guarda como una marca en app_metadata (que el usuario no puede editar) cuando abre el enlace que le enviamos.
// No usamos `email_confirmed_at`: en un proyecto con autoconfirmación, o con usuarios creados por la API de
// administración, ese campo no prueba que la persona controle el buzón.
import "server-only";
import { createClient } from "@supabase/supabase-js";

const URL_SUPA = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
const CLAVE_SERVICIO = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SERVICE_ROLE;
const CLAVE_PUBLICA = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? CLAVE_SERVICIO;
const OPCIONES = { auth: { persistSession: false, autoRefreshToken: false } };

export const MARCA_VERIFICADO = "curso_correo_verificado";

export function clientesAuth() {
  if (!URL_SUPA || !CLAVE_SERVICIO || !CLAVE_PUBLICA) return null;
  return {
    admin: createClient(URL_SUPA, CLAVE_SERVICIO, OPCIONES),
    pub: createClient(URL_SUPA, CLAVE_PUBLICA, OPCIONES),
  };
}

type Meta = Record<string, unknown> | null | undefined;
export const estaVerificado = (appMetadata: Meta) => appMetadata?.[MARCA_VERIFICADO] === true;

/** ¿El usuario `uid` de Supabase Auth confirmó por nuestro enlace que controla `email`? */
export async function correoVerificado(uid: string, email: string): Promise<boolean> {
  const c = clientesAuth();
  if (!c) return false;
  const { data, error } = await c.admin.auth.admin.getUserById(uid);
  if (error || !data.user) return false;
  return data.user.email?.toLowerCase() === email.toLowerCase() && estaVerificado(data.user.app_metadata);
}

/** Marca el correo como verificado. Solo si la cuenta sigue teniendo ese mismo correo. */
export async function marcarCorreoVerificado(uid: string, email: string): Promise<boolean> {
  const c = clientesAuth();
  if (!c) return false;
  const { data, error } = await c.admin.auth.admin.getUserById(uid);
  if (error || !data.user || data.user.email?.toLowerCase() !== email.toLowerCase()) return false;
  if (estaVerificado(data.user.app_metadata)) return true;
  const r = await c.admin.auth.admin.updateUserById(uid, {
    app_metadata: { ...(data.user.app_metadata ?? {}), [MARCA_VERIFICADO]: true },
  });
  return !r.error;
}
