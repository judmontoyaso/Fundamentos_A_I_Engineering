// Auth0 monta aquí /auth/login, /auth/logout y /auth/callback, y renueva la sesión en cada petición.
import { NextResponse, type NextRequest } from "next/server";
import { auth0 } from "@/lib/auth0";

export async function middleware(request: NextRequest) {
  return auth0 ? auth0.middleware(request) : NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|api/webhooks).*)"],
};
