// Entrar y salir en modo desarrollo. Fuera de ese modo, estas rutas responden 404.
import { NextResponse } from "next/server";
import { COOKIE_DEV, modoDev, rutaSegura } from "@/lib/auth";

type Ctx = { params: Promise<{ accion: string }> };

export async function POST(req: Request, { params }: Ctx) {
  if (!modoDev || (await params).accion !== "entrar") return new NextResponse(null, { status: 404 });
  const form = await req.formData();
  const email = String(form.get("email") ?? "").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+$/.test(email)) return new NextResponse("correo inválido", { status: 400 });
  const res = NextResponse.redirect(new URL(rutaSegura(String(form.get("returnTo") ?? "")), req.url), 303);
  res.cookies.set(COOKIE_DEV, email, { httpOnly: true, sameSite: "lax", path: "/" });
  return res;
}

export async function GET(req: Request, { params }: Ctx) {
  if (!modoDev || (await params).accion !== "salir") return new NextResponse(null, { status: 404 });
  const res = NextResponse.redirect(new URL("/", req.url));
  res.cookies.delete(COOKIE_DEV);
  return res;
}
