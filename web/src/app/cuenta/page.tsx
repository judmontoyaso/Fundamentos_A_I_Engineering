// Mi cuenta: qué acceso tengo, cuánto he avanzado, mis certificados y cómo salir.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { cubre, vigente } from "@/lib/acceso";
import { esAdmin, getUsuario, urlEntrar, urlSalir } from "@/lib/auth";
import { cursoCompletado, emitirCodigoCertificado } from "@/lib/certificado";
import { curso, cursos, itemsDe } from "@/lib/contenido";
import { PLANES } from "@/lib/planes";
import { store } from "@/lib/store";

export const metadata: Metadata = { title: "Mi cuenta" };
export const dynamic = "force-dynamic";

const fecha = (iso: string) => new Date(iso).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });

export default async function Cuenta() {
  const usuario = await getUsuario();
  if (!usuario) redirect(urlEntrar("/cuenta"));
  const [accesos, progreso] = await Promise.all([store.accesos(usuario.id), store.progreso(usuario.id)]);
  const activos = accesos.filter((a) => vigente(a));
  const admin = esAdmin(usuario);

  return (
    <Sitio>
      <div className="pagina">
        <h1>Mi cuenta</h1>
        <p className="muted">{usuario.email}{admin ? " · administrador" : ""}</p>

        <h2>Mis cursos y certificados</h2>
        {cursos.map((c) => {
          const lecciones = itemsDe(c.id);
          const hechas = lecciones.filter((i) => progreso[i.id]).length;
          const abierto = admin || activos.some((a) => cubre(a, c.id));
          const sigue = lecciones.find((i) => !progreso[i.id] && (abierto || i.gratis)) ?? lecciones[0];
          const completo = cursoCompletado(c.id, progreso);
          const certCodigo = completo ? emitirCodigoCertificado(usuario, c.id) : null;
          return (
            <div className="caja fila" key={c.id}>
              <div>
                <b>{c.titulo}</b>
                <div className="aviso">
                  {hechas} de {lecciones.length} lecciones · {abierto ? "acceso completo" : "solo la muestra gratis"}
                  {completo ? " · ¡curso completado!" : ""}
                </div>
              </div>
              <span style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
                <Link className="btn primary" href={`/leer/${sigue.id}`}>{completo ? "Repasar" : hechas ? "Continuar" : "Empezar"}</Link>
                {certCodigo && (
                  <Link className="btn" href={`/certificado/${encodeURIComponent(certCodigo)}`}>
                    Ver certificado
                  </Link>
                )}
                {abierto ? <a className="btn" href={`/descargar/${c.id}`}>Descargar código</a>
                  : <Link className="btn" href={`/comprar?plan=curso&curso=${c.id}`}>Comprar</Link>}
              </span>
            </div>
          );
        })}

        <h2>Perfil para certificados</h2>
        <div className="caja">
          <form className="form" method="post" action="/api/cuenta/nombre">
            <label>
              Nombre completo (tal como aparecerá en tus certificados)
              <input
                type="text"
                name="nombre"
                defaultValue={usuario.nombre ?? ""}
                placeholder="Ej. Ana María Gómez"
                required
                minLength={2}
                maxLength={80}
              />
            </label>
            <button type="submit" className="btn">Guardar nombre</button>
          </form>
        </div>

        <h2>Mi acceso</h2>
        {accesos.length === 0 ? (
          <div className="caja">Aún no tienes un plan. <Link href="/#planes">Ver planes</Link></div>
        ) : accesos.map((a) => (
          <div className="caja fila" key={a.id}>
            <div>
              <b>{PLANES[a.plan].nombre}{a.alcance !== "todo" ? ` · ${curso(a.alcance)?.titulo ?? a.alcance}` : ""}</b>
              <div className="aviso">
                Desde el {fecha(a.creado)} · {a.hasta ? `${new Date(a.hasta) > new Date() ? "vence" : "venció"} el ${fecha(a.hasta)}` : "sin vencimiento"}
              </div>
            </div>
            <span className={"estado " + (vigente(a) ? "ok" : "no")}>
              {a.estado === "revocado" ? "revocado" : vigente(a) ? "activo" : "vencido"}
            </span>
          </div>
        ))}
        {accesos.length > 0 && <p><Link className="btn" href="/#planes">Renovar o ampliar</Link></p>}

        <h2>Sesión</h2>
        <a className="btn" href={urlSalir()}>Cerrar sesión</a>
      </div>
    </Sitio>
  );
}
