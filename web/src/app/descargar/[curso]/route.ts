// Descarga del código de un curso como .zip.
// - Curso completo: solo para quien tiene acceso a ese curso.
// - ?muestra=1: empaqueta únicamente el módulo inicial gratuito (+ comun/_base/requirements) para probar en local antes de comprar.
import { strToU8, zipSync } from "fflate";
import { NextResponse } from "next/server";
import { cursosAbiertos } from "@/lib/acceso";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso } from "@/lib/contenido";

const LEEME = (titulo: string, esMuestra: boolean) => `${titulo}${esMuestra ? " (Muestra inicial gratuita)" : ""}
${"=".repeat(titulo.length + (esMuestra ? 27 : 0))}

Código del curso, tal como aparece en las lecciones.

Cómo correrlo
  1. Python 3.10 o superior.
  2. Crea un entorno:        python -m venv .venv
     y actívalo:             .venv\\Scripts\\activate   (Windows)   |   source .venv/bin/activate   (macOS / Linux)
  3. Instala dependencias:   pip install -r requirements.txt     (está en esta misma carpeta)
  4. Define tu API key en la terminal si el script llama a OpenAI:
        macOS / Linux:          export OPENAI_API_KEY=sk-...
        Windows (PowerShell):   $env:OPENAI_API_KEY = "sk-..."
     (Nota: en «Agentes en Producción» todos los scripts traen ModeloSimulado sin costo de API por defecto.)
     Si prefieres archivo .env en esta carpeta, lanza los scripts con:   dotenv run -- python <ruta del script>
  5. Ejecuta los scripts de cada módulo en orden:   python modulo-XX-.../code/NN_....py

Qué hay en la carpeta
  modulo-XX-.../code/   los scripts de cada módulo
  comun/                utilidades y datasets compartidos por los módulos (si el curso los tiene)
  _base/                scripts de otros cursos reutilizados; se importan solos (si aplica)
  salida/               la crean los scripts (por ej. mis_etiquetas.json de Curso 2 Módulo 4)

Las llamadas a modelos reales se cobran en tu cuenta del proveedor. Cada lección indica si corre 100 % en local.
Este material es para tu uso personal: no lo redistribuyas.
`;

export async function GET(req: Request, { params }: { params: Promise<{ curso: string }> }) {
  const c = curso((await params).curso);
  if (!c) return new NextResponse("Curso no encontrado", { status: 404 });

  const url = new URL(req.url);
  const esMuestra = url.searchParams.get("muestra") === "1";

  if (!esMuestra) {
    const usuario = await getUsuario();
    const origen = url.origin;
    if (!usuario) return NextResponse.redirect(new URL(urlEntrar(`/descargar/${c.id}`), origen));
    if (!(await cursosAbiertos(usuario, [c.id])).has(c.id)) return NextResponse.redirect(new URL("/#planes", origen));
  }

  const archivos = (await import("@/content/code")).default[c.id] ?? {};
  const carpeta = esMuestra ? `curso-${c.id}-muestra` : `curso-${c.id}`;
  const modulosTop = [...new Set(Object.keys(archivos).map((r) => r.split("/")[0]).filter((s) => /^modulo-\d+-/.test(s)))].sort();
  const primerModulo = modulosTop[0] ?? "";

  const entradas: Record<string, Uint8Array> = { [`${carpeta}/LEEME.txt`]: strToU8(LEEME(c.titulo, esMuestra)) };
  for (const [ruta, texto] of Object.entries(archivos)) {
    if (esMuestra) {
      const raiz = ruta.split("/")[0];
      const permitido =
        ruta === "requirements.txt" ||
        raiz === "comun" ||
        raiz === "_base" ||
        (primerModulo && raiz === primerModulo);
      if (!permitido) continue;
    }
    entradas[`${carpeta}/${ruta}`] = strToU8(texto);
  }

  const zip = zipSync(entradas, { level: 6 });

  return new NextResponse(Buffer.from(zip), {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="${carpeta}.zip"`,
      "Cache-Control": esMuestra ? "public, max-age=3600" : "private, no-store",
    },
  });
}
