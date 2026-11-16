// Validación compartida de contraseñas nuevas y verificación gratuita contra brechas (HIBP k-Anonymity).
import "server-only";
import { createHash } from "node:crypto";

export const MIN_CLAVE = 8;
export const MAX_CLAVE = 200;

const TIMEOUT_HIBP_MS = 2500;

/**
 * Consulta HaveIBeenPwned (Pwned Passwords v3, k-Anonymity SHA-1) sin enviar la contraseña ni el hash completo.
 * Solo viajan los 5 primeros caracteres hex del SHA-1 con padding habilitado.
 * Si el servicio externo falla o expira el timeout, devuelve `false` (fail-open) para no bloquear registros legítimos.
 */
export async function esClaveFiltrada(password: string): Promise<boolean> {
  const hash = createHash("sha1").update(password, "utf8").digest("hex").toUpperCase();
  const prefijo = hash.slice(0, 5);
  const sufijo = hash.slice(5);
  try {
    const res = await fetch(`https://api.pwnedpasswords.com/range/${prefijo}`, {
      headers: {
        "Add-Padding": "true",
        "User-Agent": "ia-en-produccion-auth-check",
      },
      signal: AbortSignal.timeout(TIMEOUT_HIBP_MS),
      cache: "no-store",
    });
    if (!res.ok) return false;
    const cuerpo = await res.text();
    for (const linea of cuerpo.split(/\r?\n/)) {
      const sep = linea.indexOf(":");
      if (sep === -1) continue;
      if (linea.slice(0, sep) === sufijo) {
        return Number(linea.slice(sep + 1)) > 0;
      }
    }
    return false;
  } catch {
    return false;
  }
}

/** Valida longitud mínima/máxima y brechas públicas para altas o cambios de contraseña. Devuelve error o `null`. */
export async function validarClaveNueva(password: string): Promise<string | null> {
  if (password.length < MIN_CLAVE || password.length > MAX_CLAVE) {
    return `La contraseña debe tener entre ${MIN_CLAVE} y ${MAX_CLAVE} caracteres.`;
  }
  if (!password.trim()) {
    return "La contraseña no puede contener solo espacios.";
  }
  if (await esClaveFiltrada(password)) {
    return "Esa contraseña apareció en filtraciones públicas de datos. Elige otra más segura.";
  }
  return null;
}
