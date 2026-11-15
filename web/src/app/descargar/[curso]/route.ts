// Descarga del código de un curso como .zip. Solo para quien tiene acceso completo a ese curso.
import { strToU8, zipSync } from "fflate";
import { NextResponse } from "next/server";
import { cursosAbiertos } from "@/lib/acceso";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso } from "@/lib/contenido";

const LEEME = (titulo: string) => `${titulo}
${"=".repeat(titulo.length)}

Código del curso, tal como aparece en las lecciones.

Cómo correrlo
  1. Python 3.10 o superior.
  2. Crea un entorno:        python -m venv .venv
     y actívalo:             .venv\\Scripts\\activate   (Windows)   |   source .venv/bin/activate   (macOS / Linux)
  3. Instala dependencias:   pip install -r requirements.txt     (está en esta misma carpeta)
  4. Define tu API key en la terminal donde vas a ejecutar los scripts (no leen el archivo .env por sí solos):
        macOS / Linux:          export OPENAI_API_KEY=sk-...
        Windows (PowerShell):   $env:OPENAI_API_KEY = "sk-..."
     Si prefieres un archivo .env en esta carpeta, lanza los scripts desde aquí con:   dotenv run -- python <ruta del script>
  5. Ejecuta los scripts de cada módulo en orden:   python modulo-01-.../code/01_....py

Qué hay en la carpeta
  modulo-XX-.../code/   los scripts de cada módulo
  comun/                código y datos que comparten los módulos (si el curso los tiene)
  _base/                scripts de otros cursos que este reutiliza; se importan solos, no hay que tocarlos
  salida/               la crean los scripts: resultados, trazas y cachés de tus corridas

Las llamadas a los modelos se cobran en tu cuenta del proveedor. Cada lección indica el costo aproximado.
Este material es para tu uso personal: no lo redistribuyas.
`;

export async function GET(req: Request, { params }: { params: Promise<{ curso: string }> }) {
  const c = curso((await params).curso);
  if (!c) return new NextResponse("Curso no encontrado", { status: 404 });
  const usuario = await getUsuario();
  const origen = new URL(req.url).origin;
  if (!usuario) return NextResponse.redirect(new URL(urlEntrar(`/descargar/${c.id}`), origen));
  if (!(await cursosAbiertos(usuario, [c.id])).has(c.id)) return NextResponse.redirect(new URL("/#planes", origen));

  const archivos = (await import("@/content/code")).default[c.id] ?? {};
  const carpeta = `curso-${c.id}`;
  const entradas: Record<string, Uint8Array> = { [`${carpeta}/LEEME.txt`]: strToU8(LEEME(c.titulo)) };
  for (const [ruta, texto] of Object.entries(archivos)) entradas[`${carpeta}/${ruta}`] = strToU8(texto);
  const zip = zipSync(entradas, { level: 6 });

  return new NextResponse(Buffer.from(zip), {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="${carpeta}.zip"`,
      "Cache-Control": "private, no-store",
    },
  });
}
