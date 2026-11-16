// Reglas de rastreo para buscadores clásicos y motores generativos (SEO / AEO / GEO).
import type { MetadataRoute } from "next";
import { urlSitioPublico } from "@/lib/sitio";

const PRIVADO = [
  "/api/",
  "/admin",
  "/cuenta",
  "/comprar",
  "/pago/",
  "/entrar",
  "/recuperar",
  "/verificar",
  "/descargar/",
  "/dev/",
];

const PERMITIDO = ["/", "/leer/", "/certificado/ejemplo", "/terminos", "/privacidad", "/llms.txt", "/llms-full.txt"];

export default function robots(): MetadataRoute.Robots {
  const base = urlSitioPublico();
  return {
    rules: [
      {
        userAgent: "*",
        allow: PERMITIDO,
        disallow: PRIVADO,
      },
      {
        userAgent: ["OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot", "Google-Extended", "Applebot-Extended"],
        allow: PERMITIDO,
        disallow: PRIVADO,
      },
    ],
    sitemap: `${base}/sitemap.xml`,
    host: base,
  };
}
