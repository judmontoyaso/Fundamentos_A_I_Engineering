// Versión extendida de llms.txt con el temario módulo por módulo y preguntas frecuentes.
import { NextResponse } from "next/server";
import { cursos, gruposDe } from "@/lib/contenido";
import { NOMBRE_SITIO, urlSitioPublico } from "@/lib/sitio";

export const dynamic = "force-dynamic";

export async function GET() {
  const base = urlSitioPublico();
  const modulos = cursos.reduce((n, c) => n + c.modulos, 0);

  const out: string[] = [
    `# ${NOMBRE_SITIO} · Catálogo completo y temario (${cursos.length} cursos · ${modulos} módulos)`,
    "",
    `Sitio oficial: ${base}`,
    "",
    "## Qué aprende el estudiante",
    "- Salidas estructuradas con Pydantic y JSON Schema, embeddings, bases vectoriales (Qdrant), búsqueda híbrida BM25 + RRF y workflows con LangGraph.",
    "- Evaluación rigurosa (Evals): error analysis, datos sintéticos desde hechos, acuerdo humano Kappa de Cohen, jueces LLM calibrados con TPR/TNR y puertas en CI/CD.",
    "- Ingeniería de búsqueda e IA Search: métricas graduadas nDCG@k y MRR, query understanding, parsing/contextual retrieval, reranking, SQL/grafos, LTR, ACLs y caché semántica.",
    "- Agentes en producción: presupuestos de pasos/costo, contratos poka-yoke, máquinas de estado con checkpoints e idempotencia, poda de contexto, protocolo MCP (JSON-RPC sobre stdio), subagentes Map-Reduce, HITL, defensa contra prompt injection y evaluación pass^k.",
    "",
  ];

  for (const c of cursos) {
    out.push(`## ${c.titulo} (${c.modulos} módulos)`);
    if (c.etapa) out.push(`Etapa: ${c.etapa}`);
    if (c.descripcion) out.push(c.descripcion);
    out.push("");
    for (const g of gruposDe(c.id)) {
      if (g.grupo === "Inicio") {
        const it = g.items[0];
        if (it) out.push(`- Presentación (gratis): ${base}/leer/${it.id}`);
        continue;
      }
      const gratisTag = g.items.some((i) => i.gratis) ? " [Muestra gratis disponible]" : "";
      const primerManual = g.items[0];
      out.push(`- ${g.grupo}${gratisTag}${primerManual?.gratis ? ` → ${base}/leer/${primerManual.id}` : ""}`);
    }
    out.push("");
  }

  return new NextResponse(out.join("\n") + "\n", {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
