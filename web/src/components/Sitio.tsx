// Cabecera y pie de las páginas que no son el lector.
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { MenuMovil } from "@/components/MenuMovil";
import { TemaBtn } from "@/components/TemaBtn";
import { esAdmin, getUsuario, urlEntrar, urlSalir } from "@/lib/auth";
import { CONTACTO_SITIO, NOMBRE_SITIO } from "@/lib/sitio";

export async function Sitio({ children }: { children: React.ReactNode }) {
  const usuario = await getUsuario();
  return (
    <div className="sitio">
      <a className="skip-link" href="#contenido">Saltar al contenido</a>
      <header className="sitio-top">
        <Link className="marca" href="/"><Logo size={34} priority />{NOMBRE_SITIO}</Link>
        <nav aria-label="Navegación principal">
          <Link href="/#cursos">Cursos</Link>
          <Link href="/#planes">Planes</Link>
          <Link href="/#preguntas">Preguntas</Link>
          {esAdmin(usuario) && <Link href="/admin">Admin</Link>}
        </nav>
        <TemaBtn />
        <span className="solo-ancho">
          {usuario ? (
            <>
              <Link className="btn" href="/cuenta">Mi cuenta</Link>
              <a className="salir-link" href={urlSalir()}>Cerrar sesión</a>
            </>
          ) : (
            <a className="btn" href={urlEntrar("/cuenta")}>Entrar</a>
          )}
        </span>
        <MenuMovil
          enlaces={[
            { href: "/#cursos", texto: "Cursos" },
            { href: "/#planes", texto: "Planes" },
            { href: "/#preguntas", texto: "Preguntas" },
            ...(esAdmin(usuario) ? [{ href: "/admin", texto: "Admin" }] : []),
          ]}
          cuenta={usuario ? { href: "/cuenta", texto: "Mi cuenta" } : { href: urlEntrar("/cuenta"), texto: "Entrar" }}
          salir={usuario ? urlSalir() : undefined}
        />
      </header>
      <main id="contenido" className="sitio-main">{children}</main>
      <footer className="sitio-pie">
        <div className="ancho">
          <span style={{ display: "flex", alignItems: "center", gap: ".55rem" }}>
            <Logo size={22} /> © {new Date().getFullYear()} {NOMBRE_SITIO}
          </span>
          <span style={{ display: "flex", gap: "1.1rem", flexWrap: "wrap" }}>
            <Link href="/certificado/ejemplo">Certificado de ejemplo</Link>
            <Link href="/llms.txt">llms.txt</Link>
            <Link href="/terminos">Términos</Link>
            <Link href="/privacidad">Privacidad</Link>
            {CONTACTO_SITIO && <a href={`mailto:${CONTACTO_SITIO}`}>{CONTACTO_SITIO}</a>}
          </span>
        </div>
      </footer>
    </div>
  );
}
