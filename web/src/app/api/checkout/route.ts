// Crea el pedido y envía al comprador a la pasarela elegida.
import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso } from "@/lib/contenido";
import { proveedor, urlBase } from "@/lib/pagos";
import { MONEDA, PLANES, esPlan, montoDe } from "@/lib/planes";
import { store } from "@/lib/store";
import type { Pedido } from "@/lib/tipos";

export async function POST(req: Request) {
  const base = urlBase(req);
  const form = await req.formData();
  const plan = form.get("plan");
  const cursoId = String(form.get("curso") ?? "");
  const volver = `/comprar?plan=${encodeURIComponent(String(plan ?? ""))}${cursoId ? `&curso=${encodeURIComponent(cursoId)}` : ""}`;

  const usuario = await getUsuario();
  if (!usuario) return NextResponse.redirect(new URL(urlEntrar(volver), base), 303);

  const p = proveedor(String(form.get("proveedor") ?? ""));
  const error = (m: string) => NextResponse.redirect(new URL(`${volver}&error=${encodeURIComponent(m)}`, base), 303);
  if (!esPlan(plan)) return NextResponse.redirect(new URL("/#planes", base), 303);
  if (plan === "curso" && !curso(cursoId)) return error("Elige un curso.");
  if (!p) return error("Ese medio de pago no está disponible.");
  const esUsd = p.id === "lemonsqueezy";
  const monedaPedido = esUsd ? "USD" : MONEDA;
  const monto = esUsd ? PLANES[plan].usd : montoDe(plan);
  if (monto === null) return error("El precio de este plan aún no está configurado.");

  const pedido: Pedido = {
    id: randomUUID(), userId: usuario.id, email: usuario.email, plan, curso: plan === "curso" ? cursoId : null,
    monto, moneda: monedaPedido, proveedor: p.id, estado: "pendiente", refProveedor: null, creado: new Date().toISOString(),
  };
  await store.crearPedido(pedido);

  const sitio = process.env.NEXT_PUBLIC_NOMBRE_SITIO ?? "IA en Producción";
  const titulo = plan === "curso" ? `Curso: ${curso(cursoId)!.titulo}` : `Plan ${PLANES[plan].nombre.toLowerCase()} · ${sitio}`;
  try {
    const url = await p.crearCheckout(pedido, titulo, base);
    return NextResponse.redirect(new URL(url, base), 303);
  } catch (e) {
    console.error(`[checkout ${p.id}]`, e);
    return error("No se pudo iniciar el pago. Intenta de nuevo o usa otro medio.");
  }
}
