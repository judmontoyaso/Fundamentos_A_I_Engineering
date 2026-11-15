// Login de desarrollo: existe solo cuando Auth0 no está configurado y la app no corre en producción.
import { notFound } from "next/navigation";
import { modoDev, rutaSegura } from "@/lib/auth";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

export default async function EntrarDev({ searchParams }: { searchParams: Promise<{ returnTo?: string }> }) {
  if (!modoDev) notFound();
  const returnTo = rutaSegura((await searchParams).returnTo);
  return (
    <div className="pagina">
      <h1>Entrar (modo desarrollo)</h1>
      <p className="muted">
        Auth0 no está configurado, así que la app usa un login de prueba sin contraseña. Esta pantalla no existe en producción.
      </p>
      <form className="form caja" method="post" action="/api/dev/entrar">
        <input type="hidden" name="returnTo" value={returnTo} />
        <label>Correo<input type="email" name="email" required defaultValue="prueba@ejemplo.test" /></label>
        <button className="btn primary">Entrar</button>
      </form>
    </div>
  );
}
