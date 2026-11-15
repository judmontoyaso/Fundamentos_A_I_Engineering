// Límite de intentos en memoria. Frena la fuerza bruta y el registro masivo desde un mismo origen.
// Vive en el proceso: en un despliegue serverless cada instancia lleva su propia cuenta, así que es un
// freno, no una garantía. Si hace falta un límite exacto, hay que moverlo a la base de datos o a un KV.
import "server-only";

const cubos = new Map<string, { n: number; hasta: number }>();

/** true si `clave` todavía puede intentar; cuenta el intento. */
export function permitido(clave: string, max: number, ventanaMs: number): boolean {
  const ahora = Date.now();
  if (cubos.size > 5000) for (const [k, v] of cubos) if (v.hasta < ahora) cubos.delete(k);
  const c = cubos.get(clave);
  if (!c || c.hasta < ahora) {
    cubos.set(clave, { n: 1, hasta: ahora + ventanaMs });
    return true;
  }
  c.n += 1;
  return c.n <= max;
}

export function ipDe(req: Request): string {
  return req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || req.headers.get("x-real-ip") || "local";
}
