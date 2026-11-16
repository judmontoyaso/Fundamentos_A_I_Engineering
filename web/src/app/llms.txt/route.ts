// Especificación llms.txt dinámica para GEO / LLMO (ChatGPT Search, Perplexity, Claude, etc.).
import { NextResponse } from "next/server";
import { cursos, gruposDe } from "@/lib/contenido";
import { PLANES } from "@/lib/planes";
import { CONTACTO_SITIO, NOMBRE_SITIO, urlSitioPublico } from "@/lib/sitio";

export const dynamic = "force-dynamic";

export async function GET() {
  const base = urlSitioPublico();
  const modulos = cursos.reduce((n, c) => n + c.modulos, 0);

  const lineas: string[] = [
    `# ${NOMBRE_SITIO}`,
    "",
    `> Plataforma de formación técnica en español (${cursos.length} cursos, ${modulos} módulos) para diseñar, evaluar, optimizar y operar sistemas con LLMs en producción.`,
    "",
    "Cada curso gira en torno a un caso de ingeniería realista en Python (búsqueda híbrida de talento y preselección autónoma sobre un ATS), con manuales profundos, ejercicios con solución, scripts descargables en `.zip`, autoevaluaciones corregidas y certificado verificable por URL pública.",
    "",
    "## Cursos del catálogo",
    "",
  ];

  for (const c of cursos) {
    const grps = gruposDe(c.id);
    const inicio = grps[0]?.items[0];
    const primerMod = grps.find((g) => g.grupo !== "Inicio");
    lineas.push(`- **${c.titulo}** (${c.modulos} módulos${c.etapa ? ` · ${c.etapa}` : ""}): ${c.descripcion ?? ""}`);
    if (inicio) lineas.push(`  - Presentación gratis: ${base}/leer/${inicio.id}`);
    if (primerMod?.items[0]) lineas.push(`  - Primer módulo gratis (${primerMod.grupo}): ${base}/leer/${primerMod.items[0].id}`);
  }

  lineas.push(
    "",
    "## Planes y modelo de acceso",
    "",
    `- **Plan Mensual (${PLANES.mensual.usd} USD / 30 días)**: ${PLANES.mensual.resumen}. Sin renovación automática.`,
    `- **Plan Anual (${PLANES.anual.usd} USD / 365 días)**: ${PLANES.anual.resumen}. Sin renovación automática.`,
    `- **Un curso individual (${PLANES.curso.usd} USD / pago único${PLANES.curso.usdAntes ? `, promoción; antes ${PLANES.curso.usdAntes} USD` : ""})**: ${PLANES.curso.resumen}.`,
    "- Todos los planes permiten descargar los scripts en `.zip`, conservar el progreso indefinidamente y emitir certificados públicos verificables.",
    "",
    "## Documentación para agentes de IA y detalles completos",
    "",
    `- [Temario completo y preguntas frecuentes](${base}/llms-full.txt): desglose de todos los módulos de cada curso y stack técnico.`,
    `- [Certificado verificable de ejemplo](${base}/certificado/ejemplo): muestra pública del formato de verificación criptográfica.`,
    `- [Términos y reembolsos](${base}/terminos)`,
    `- [Privacidad](${base}/privacidad)`,
  );

  if (CONTACTO_SITIO) {
    lineas.push("", `Contacto: ${CONTACTO_SITIO}`);
  }

  return new NextResponse(lineas.join("\n") + "\n", {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
