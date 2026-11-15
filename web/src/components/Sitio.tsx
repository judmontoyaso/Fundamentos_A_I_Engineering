// Cabecera y pie de las páginas que no son el lector.
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { esAdmin, getUsuario, urlEntrar } from "@/lib/auth";

const NOMBRE = process.env.NEXT_PUBLIC_NOMBRE_SITIO ?? "IA en Producción";
const CONTACTO = process.env.NEXT_PUBLIC_CONTACTO ?? "";

export async function Sitio({ children }: { children: React.ReactNode }) {
  const usuario = await getUsuario();
  return (
    <div className="sitio">
      <header className="sitio-top">
        <Link className="marca" href="/"><Logo size={34} />{NOMBRE}</Link>
        <nav>
          <Link href="/#cursos">Cursos</Link>
          <Link href="/#planes">Planes</Link>
          <Link href="/#preguntas">Preguntas</Link>
          {esAdmin(usuario) && <Link href="/admin">Admin</Link>}
        </nav>
        {usuario ? <Link className="btn" href="/cuenta">Mi cuenta</Link> : <a className="btn" href={urlEntrar("/cuenta")}>Entrar</a>}
      </header>
      {children}
      <footer className="sitio-pie">
        <div className="ancho">
          <span>© {new Date().getFullYear()} {NOMBRE}</span>
          <span style={{ display: "flex", gap: "1.1rem", flexWrap: "wrap" }}>
            <Link href="/terminos">Términos</Link>
            <Link href="/privacidad">Privacidad</Link>
            {CONTACTO && <a href={`mailto:${CONTACTO}`}>{CONTACTO}</a>}
          </span>
        </div>
      </footer>
    </div>
  );
}
