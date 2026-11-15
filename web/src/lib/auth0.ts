// Cliente de Auth0. Sin las cuatro variables de entorno no hay cliente: en desarrollo la app
// cae al "login de desarrollo" (src/lib/auth.ts) y en producción simplemente no hay sesión.
// No fijamos un único appBaseUrl estático para que el SDK tome el host real de la petición
// (localhost, iaenproduccion.vercel.app, dominio propio, etc.) y la cookie __txn_ siempre coincida.
import { Auth0Client } from "@auth0/nextjs-auth0/server";

export const auth0Activo = Boolean(
  process.env.AUTH0_DOMAIN && process.env.AUTH0_CLIENT_ID && process.env.AUTH0_CLIENT_SECRET && process.env.AUTH0_SECRET,
);

delete process.env.APP_BASE_URL;
export const auth0 = auth0Activo ? new Auth0Client() : null;
