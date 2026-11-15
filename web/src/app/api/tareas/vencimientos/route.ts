// Tarea programada: avisa por correo a quienes se les vence el acceso en N días.
//
// La app no tiene reloj propio; la llama un programador externo (n8n, cron de Vercel, GitHub Actions...)
// UNA VEZ AL DÍA:
//     POST /api/tareas/vencimientos            Authorization: Bearer <TAREAS_SECRET>
//     POST /api/tareas/vencimientos?dias=7     (por defecto avisa a 3 días)
// Cada llamada cubre los accesos que vencen dentro del día número N contado desde hoy (UTC), así que con una
// llamada diaria cada acceso recibe un solo aviso. Llamarla dos veces el mismo día lo repite.
import { timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";
import { cubre, vigente } from "@/lib/acceso";
import { curso } from "@/lib/contenido";
import { correoActivo, enviarCorreo, urlSitio } from "@/lib/correo";
import { PLANES } from "@/lib/planes";
import { store } from "@/lib/store";

export const dynamic = "force-dynamic";

function autorizado(req: Request): boolean {
  const secreto = process.env.TAREAS_SECRET;
  if (!secreto) return false; // sin secreto configurado la tarea no existe
  const a = Buffer.from(req.headers.get("authorization") ?? "");
  const b = Buffer.from(`Bearer ${secreto}`);
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function POST(req: Request) {
  if (!autorizado(req)) return new NextResponse(null, { status: 404 });
  if (!correoActivo) return NextResponse.json({ ok: false, motivo: "correo sin configurar" }, { status: 503 });

  const dias = Math.min(30, Math.max(1, Number(new URL(req.url).searchParams.get("dias")) || 3));
  const inicio = new Date();
  inicio.setUTCHours(0, 0, 0, 0);
  inicio.setUTCDate(inicio.getUTCDate() + dias);
  const fin = new Date(inicio.getTime() + 86_400_000);

  const porVencer = await store.accesosPorVencer(inicio.toISOString(), fin.toISOString());
  const base = urlSitio();
  let enviados = 0;
  let omitidos = 0;

  for (const a of porVencer) {
    // Si ya renovó (tiene otro acceso vigente que cubre lo mismo y vence después), no hay nada que avisar.
    const otros = await store.accesos(a.userId);
    const renovado = otros.some((o) => o.id !== a.id && vigente(o) && (o.alcance === "todo" || cubre(o, a.alcance)) && (o.hasta === null || o.hasta > a.hasta!));
    if (!a.email || renovado) {
      omitidos += 1;
      continue;
    }
    const que = a.alcance === "todo" ? `tu plan ${PLANES[a.plan].nombre.toLowerCase()}` : `tu acceso a «${curso(a.alcance)?.titulo ?? a.alcance}»`;
    const fecha = new Date(a.hasta!).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });
    const enlace = base ? `${base}/#planes` : "";
    const ok = await enviarCorreo({
      para: a.email,
      asunto: `Tu acceso vence el ${fecha}`,
      texto: `Hola.\n\n${que[0].toUpperCase()}${que.slice(1)} vence el ${fecha}. No se renueva solo: si quieres seguir, renuévalo cuando quieras${enlace ? ` en ${enlace}` : ""}.\nTu progreso y tus certificados se conservan aunque venza.\n`,
      html: `<div style="font-family:system-ui,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#111827">
        <h1 style="font-size:20px;margin:0 0 16px">Tu acceso vence el ${fecha}</h1>
        <p style="line-height:1.55">${que[0].toUpperCase()}${que.slice(1).replace(/[&<>]/g, "")} vence el ${fecha}. No se renueva solo: si quieres seguir, renuévalo cuando quieras.</p>
        <p style="line-height:1.55">Tu progreso y tus certificados se conservan aunque venza.</p>
        ${enlace ? `<p style="margin:22px 0"><a href="${enlace}" style="background:#111827;color:#fff;text-decoration:none;padding:11px 18px;border-radius:8px;display:inline-block">Renovar</a></p>` : ""}
      </div>`,
    });
    if (ok) enviados += 1;
    else omitidos += 1;
  }

  return NextResponse.json({ ok: true, dias, revisados: porVencer.length, enviados, omitidos });
}
