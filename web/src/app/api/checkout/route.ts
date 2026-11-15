// Crea el pedido, aplica cupones (incluido acceso 100 % gratuito sin pasarela) o envía al comprador a la pasarela elegida.
import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";
import { confirmarPedido } from "@/lib/acceso";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso } from "@/lib/contenido";
import { aplicarDescuento, validarCupon } from "@/lib/cupones";
import { proveedor, urlBase } from "@/lib/pagos";
import { MONEDA, PLANES, esPlan, montoDe } from "@/lib/planes";
import { store } from "@/lib/store";
import type { Pedido } from "@/lib/tipos";

export async function POST(req: Request) {
  const base = urlBase(req);
  const form = await req.formData();
  const plan = form.get("plan");
  const cursoId = String(form.get("curso") ?? "");
  const codigoCupon = String(form.get("cupon") ?? "").trim().toUpperCase();
  const volver = `/comprar?plan=${encodeURIComponent(String(plan ?? ""))}${cursoId ? `&curso=${encodeURIComponent(cursoId)}` : ""}${codigoCupon ? `&cupon=${encodeURIComponent(codigoCupon)}` : ""}`;

  const usuario = await getUsuario();
  if (!usuario) return NextResponse.redirect(new URL(urlEntrar(volver), base), 303);

  const error = (m: string) => NextResponse.redirect(new URL(`${volver}&error=${encodeURIComponent(m)}`, base), 303);
  if (!esPlan(plan)) return NextResponse.redirect(new URL("/#planes", base), 303);
  if (plan === "curso" && !curso(cursoId)) return error("Elige un curso.");

  // Validar cupón si fue enviado
  let porcentajeDescuento = 0;
  if (codigoCupon) {
    const val = await validarCupon(codigoCupon, plan, plan === "curso" ? cursoId : null);
    if (!val.ok) return error(val.error);
    porcentajeDescuento = val.porcentaje;
  }

  // Caso 1: Cupón de 100 % de descuento (acceso inmediato sin pasar por pasarela)
  if (porcentajeDescuento >= 100) {
    const consumido = await store.usarCupon(codigoCupon);
    if (!consumido) return error("Este cupón acaba de agotarse o ya no está activo.");
    const pedido: Pedido = {
      id: randomUUID(),
      userId: usuario.id,
      email: usuario.email,
      plan,
      curso: plan === "curso" ? cursoId : null,
      monto: 0,
      moneda: MONEDA,
      proveedor: `cupon:${codigoCupon}`,
      estado: "pendiente",
      refProveedor: codigoCupon,
      creado: new Date().toISOString(),
    };
    await store.crearPedido(pedido);
    await confirmarPedido(pedido, codigoCupon);
    return NextResponse.redirect(new URL(`/pago/resultado?pedido=${pedido.id}`, base), 303);
  }

  // Caso 2: Cobro en pasarela (con o sin descuento parcial)
  const p = proveedor(String(form.get("proveedor") ?? ""));
  if (!p) return error("Ese medio de pago no está disponible.");
  const esUsd = p.id === "lemonsqueezy";
  const monedaPedido = esUsd ? "USD" : MONEDA;
  const montoBase = esUsd ? PLANES[plan].usd : montoDe(plan);
  if (montoBase === null) return error("El precio de este plan aún no está configurado.");
  const monto = aplicarDescuento(montoBase, porcentajeDescuento);

  if (codigoCupon && porcentajeDescuento > 0) {
    const consumido = await store.usarCupon(codigoCupon);
    if (!consumido) return error("Este cupón ya no está disponible.");
  }

  const pedido: Pedido = {
    id: randomUUID(),
    userId: usuario.id,
    email: usuario.email,
    plan,
    curso: plan === "curso" ? cursoId : null,
    monto,
    moneda: monedaPedido,
    proveedor: p.id,
    estado: "pendiente",
    refProveedor: codigoCupon || null,
    creado: new Date().toISOString(),
  };
  await store.crearPedido(pedido);

  const sitio = process.env.NEXT_PUBLIC_NOMBRE_SITIO ?? "IA en Producción";
  const baseTitulo = plan === "curso" ? `Curso: ${curso(cursoId)!.titulo}` : `Plan ${PLANES[plan].nombre.toLowerCase()} · ${sitio}`;
  const titulo = porcentajeDescuento > 0 ? `${baseTitulo} (-${porcentajeDescuento}% cupón ${codigoCupon})` : baseTitulo;
  try {
    const url = await p.crearCheckout(pedido, titulo, base);
    return NextResponse.redirect(new URL(url, base), 303);
  } catch (e) {
    console.error(`[checkout ${p.id}]`, e);
    return error("No se pudo iniciar el pago. Intenta de nuevo o usa otro medio.");
  }
}
