// Tarea de anotación: POST guarda una etiqueta; GET descarga las del usuario como mis_etiquetas.json,
// el archivo que leen los scripts del curso (curso-evals/comun/ev_comun.py, función anotaciones()).
import { NextResponse } from "next/server";
import { puedeLeer } from "@/lib/acceso";
import { getUsuario } from "@/lib/auth";
import { item } from "@/lib/contenido";
import { store } from "@/lib/store";

export async function GET(req: Request) {
  const usuario = await getUsuario();
  if (!usuario) return NextResponse.json({ error: "sin sesión" }, { status: 401 });
  const it = item(new URL(req.url).searchParams.get("nb") ?? "");
  if (!it || it.tipo !== "anotar") return NextResponse.json({ error: "tarea desconocida" }, { status: 404 });
  if (!(await puedeLeer(usuario, it))) return NextResponse.json({ error: "sin acceso" }, { status: 403 });
  const etiquetas = await store.etiquetas(usuario.id, it.id);
  return new NextResponse(JSON.stringify({ nb: it.id, etiquetas }, null, 1), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Disposition": 'attachment; filename="mis_etiquetas.json"',
      "Cache-Control": "private, no-store",
    },
  });
}

export async function POST(req: Request) {
  const usuario = await getUsuario();
  if (!usuario) return NextResponse.json({ error: "sin sesión" }, { status: 401 });
  const b = (await req.json().catch(() => null)) as { nb?: unknown; item?: unknown; label?: unknown; nota?: unknown } | null;
  const it = typeof b?.nb === "string" ? item(b.nb) : null;
  if (!it || it.tipo !== "anotar" || !it.tarea || typeof b?.label !== "boolean" || typeof b.item !== "string")
    return NextResponse.json({ error: "petición inválida" }, { status: 400 });
  if (!it.tarea.items.some((x) => x.id === b.item)) return NextResponse.json({ error: "ítem desconocido" }, { status: 400 });
  if (!(await puedeLeer(usuario, it))) return NextResponse.json({ error: "sin acceso" }, { status: 403 });
  const nota = typeof b.nota === "string" ? b.nota.trim().slice(0, 500) : "";
  await store.etiquetar(usuario.id, it.id, b.item, b.label, nota);
  return NextResponse.json({ ok: true });
}
