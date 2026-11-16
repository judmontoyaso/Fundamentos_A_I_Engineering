// Configuración pública y canónica del sitio compartida entre metadata, SEO/GEO, certificados y correos.
export const NOMBRE_SITIO = process.env.NEXT_PUBLIC_NOMBRE_SITIO ?? "IA en Producción";
export const CONTACTO_SITIO = (process.env.NEXT_PUBLIC_CONTACTO ?? "").trim();

/** URL pública sin barra final. Prioriza SITIO_URL -> NEXT_PUBLIC_SITIO_URL -> VERCEL_PROJECT_PRODUCTION_URL -> localhost. */
export function urlSitioPublico(): string {
  const fija = (process.env.SITIO_URL ?? process.env.NEXT_PUBLIC_SITIO_URL ?? "").trim().replace(/\/$/, "");
  if (fija) return fija;
  const vercel = (process.env.VERCEL_PROJECT_PRODUCTION_URL ?? "").trim().replace(/\/$/, "");
  if (vercel) return `https://${vercel}`;
  return "http://localhost:3000";
}
