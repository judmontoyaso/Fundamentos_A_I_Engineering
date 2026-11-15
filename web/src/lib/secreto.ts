// Clave del servidor con la que se firman la sesión propia, los enlaces de verificación y los certificados.
import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";

/**
 * En producción no hay valor por defecto: sin secreto configurado la función lanza un error y quien la
 * llama debe fallar cerrado (sin sesión, sin certificado). El valor fijo solo existe para desarrollo local.
 */
export function secretoServidor(): string {
  const s = process.env.AUTH0_SECRET || process.env.SESION_SECRET || process.env.SERVICE_ROLE || process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (s) return s;
  if (process.env.NODE_ENV === "production") {
    throw new Error("Falta AUTH0_SECRET (o SESION_SECRET): sin él no se pueden firmar sesiones ni certificados.");
  }
  return "dev-secret-ia-en-produccion";
}

const firma = (etiqueta: string, payload: string) =>
  createHmac("sha256", secretoServidor()).update(`${etiqueta}:${payload}`).digest("base64url");

/** Serializa y firma `datos`. La etiqueta separa los usos: un token de un tipo no sirve para otro. */
export function firmarDatos(etiqueta: string, datos: Record<string, unknown>): string {
  const payload = Buffer.from(JSON.stringify(datos), "utf8").toString("base64url");
  return `${payload}.${firma(etiqueta, payload)}`;
}

/** Devuelve los datos si la firma es válida y no han vencido (`exp` en milisegundos); si no, null. */
export function leerDatos<T extends Record<string, unknown>>(etiqueta: string, valor: string | null | undefined): T | null {
  if (!valor) return null;
  const [payload, recibida, ...resto] = valor.split(".");
  if (!payload || !recibida || resto.length) return null;
  try {
    const a = Buffer.from(firma(etiqueta, payload));
    const b = Buffer.from(recibida);
    if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
    const d = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!d || typeof d !== "object") return null;
    if (typeof d.exp === "number" && Date.now() > d.exp) return null;
    return d as T;
  } catch {
    return null; // firma mal formada, JSON inválido o secreto ausente en producción
  }
}
