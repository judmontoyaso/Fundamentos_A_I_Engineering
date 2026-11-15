// Avisos de las pasarelas. El aviso solo trae una referencia: el estado se vuelve a consultar a la pasarela.
import { NextResponse } from "next/server";
import { aplicarPago, proveedor } from "@/lib/pagos";

export async function POST(req: Request, { params }: { params: Promise<{ proveedor: string }> }) {
  const p = proveedor((await params).proveedor);
  if (!p) return new NextResponse(null, { status: 404 });
  const cuerpo = await req.text();
  const ref = await p.refDeWebhook(req, cuerpo);
  if (!ref) return NextResponse.json({ ok: true, ignorado: true }); // aviso de otro tipo, o firma inválida
  try {
    await aplicarPago(p.id, ref);
  } catch (e) {
    console.error(`[webhook ${p.id}]`, e);
    return NextResponse.json({ ok: false }, { status: 500 }); // la pasarela reintenta
  }
  return NextResponse.json({ ok: true });
}
