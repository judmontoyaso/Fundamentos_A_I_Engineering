// Guarda si una lección está hecha. Solo para lecciones que la persona puede leer.
import { NextResponse } from "next/server";
import { puedeLeer } from "@/lib/acceso";
import { getUsuario } from "@/lib/auth";
import { item } from "@/lib/contenido";
import { store } from "@/lib/store";

export async function POST(req: Request) {
  const usuario = await getUsuario();
  if (!usuario) return NextResponse.json({ error: "sin sesión" }, { status: 401 });
  const body = (await req.json().catch(() => null)) as { id?: unknown; hecho?: unknown } | null;
  const it = typeof body?.id === "string" ? item(body.id) : null;
  if (!it || typeof body?.hecho !== "boolean") return NextResponse.json({ error: "petición inválida" }, { status: 400 });
  if (!(await puedeLeer(usuario, it))) return NextResponse.json({ error: "sin acceso" }, { status: 403 });
  await store.marcar(usuario.id, it.id, body.hecho);
  return NextResponse.json({ ok: true });
}
