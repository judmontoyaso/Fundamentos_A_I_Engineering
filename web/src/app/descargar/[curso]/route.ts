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
  1. Python 3.11 o superior.
  2. Crea un entorno:        python -m venv .venv
     y actívalo:             .venv\\Scripts\\activate   (Windows)   |   source .venv/bin/activate   (macOS / Linux)
  3. Instala dependencias:   pip install -r <carpeta del módulo>/code/requirements.txt
     (algunos cursos tienen un requirements.txt único en la raíz).
  4. Define tu API key como variable de entorno (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY u OPENROUTER_API_KEY).
  5. Ejecuta los scripts en orden desde la carpeta code/ de cada módulo:   python 01_....py

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
