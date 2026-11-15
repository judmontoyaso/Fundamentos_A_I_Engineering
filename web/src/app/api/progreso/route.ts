// Guarda si una lección está hecha. Solo para lecciones que la persona puede leer.
// Si es una autoevaluación (quiz), exige las respuestas y verifica en el servidor que acierte >= 80 %.
import { NextResponse } from "next/server";
import { puedeLeer } from "@/lib/acceso";
import { getUsuario } from "@/lib/auth";
import { item } from "@/lib/contenido";
import { store } from "@/lib/store";

const APROBADO = 0.8;

export async function POST(req: Request) {
  const usuario = await getUsuario();
  if (!usuario) return NextResponse.json({ error: "sin sesión" }, { status: 401 });
  const body = (await req.json().catch(() => null)) as { id?: unknown; hecho?: unknown; respuestas?: unknown } | null;
  const it = typeof body?.id === "string" ? item(body.id) : null;
  if (!it || typeof body?.hecho !== "boolean") return NextResponse.json({ error: "petición inválida" }, { status: 400 });
  if (!(await puedeLeer(usuario, it))) return NextResponse.json({ error: "sin acceso" }, { status: 403 });

  if (it.tipo === "quiz" && body.hecho && it.preguntas?.length) {
    const resp = Array.isArray(body.respuestas) ? body.respuestas : null;
    if (!resp || resp.length !== it.preguntas.length) {
      return NextResponse.json({ error: "faltan las respuestas de la autoevaluación" }, { status: 400 });
    }
    const aciertos = it.preguntas.filter((p, i) => Number(resp[i]) === p.correcta).length;
    if (aciertos / it.preguntas.length < APROBADO) {
      return NextResponse.json({ error: "no alcanza el puntaje mínimo de aprobación" }, { status: 400 });
    }
  }

  await store.marcar(usuario.id, it.id, body.hecho);
  return NextResponse.json({ ok: true });
}
