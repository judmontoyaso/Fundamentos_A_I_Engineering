// Mapa del sitio dinámico para buscadores: portada, certificado de ejemplo, legales y muestras gratuitas.
import type { MetadataRoute } from "next";
import { grupos } from "@/lib/contenido";
import { urlSitioPublico } from "@/lib/sitio";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = urlSitioPublico();
  const ahora = new Date();

  const estaticas: MetadataRoute.Sitemap = [
    { url: `${base}/`, lastModified: ahora, changeFrequency: "weekly", priority: 1 },
    { url: `${base}/certificado/ejemplo`, lastModified: ahora, changeFrequency: "monthly", priority: 0.6 },
    { url: `${base}/terminos`, lastModified: ahora, changeFrequency: "yearly", priority: 0.3 },
    { url: `${base}/privacidad`, lastModified: ahora, changeFrequency: "yearly", priority: 0.3 },
  ];

  const gratuitas: MetadataRoute.Sitemap = grupos
    .flatMap((g) => g.items)
    .filter((it) => it.gratis)
    .map((it) => ({
      url: `${base}/leer/${encodeURIComponent(it.id)}`,
      lastModified: ahora,
      changeFrequency: "monthly" as const,
      priority: it.id.endsWith("inicio") || it.tipo === "md" ? 0.8 : 0.6,
    }));

  return [...estaticas, ...gratuitas];
}
