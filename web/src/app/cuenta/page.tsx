// Mi cuenta: qué acceso tengo, cuánto he avanzado, mis certificados y cómo salir.
import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { cubre, vigente } from "@/lib/acceso";
import { esAdmin, getUsuario, sesionCorreo, urlEntrar, urlSalir } from "@/lib/auth";
import { cursoCompletado, idCertificado } from "@/lib/certificado";
import { curso, cursos, itemsDe } from "@/lib/contenido";
import { correoActivo } from "@/lib/correo";
import { PLANES } from "@/lib/planes";
import { store } from "@/lib/store";

export const metadata: Metadata = { title: "Mi cuenta", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

const fecha = (iso: string) => new Date(iso).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" });

const AVISOS_CORREO: Record<string, string> = {
  verificado: "Tu correo quedó verificado.",
  "clave-actualizada": "Tu contraseña se actualizó y tu correo quedó verificado.",
  enviado: "Te enviamos el enlace de verificación. Revisa también la carpeta de spam.",
  espera: "Ya te enviamos varios enlaces. Espera una hora antes de pedir otro.",
  fallo: "No pudimos enviar el correo. Intenta de nuevo en unos minutos.",
  "sin-servicio": "El envío de correos aún no está habilitado.",
};

type Props = { searchParams: Promise<{ correo?: string }> };

export default async function Cuenta({ searchParams }: Props) {
  const usuario = await getUsuario();
  if (!usuario) redirect(urlEntrar("/cuenta"));
  const avisoCorreo = AVISOS_CORREO[(await searchParams).correo ?? ""];
  const propia = await sesionCorreo();
  const puedeReenviar = correoActivo && Boolean(propia?.id.startsWith("email|"));
  const [accesos, progreso] = await Promise.all([store.accesos(usuario.id), store.progreso(usuario.id)]);
  const activos = accesos.filter((a) => vigente(a));
  const admin = esAdmin(usuario);
  const listaCursos = [...cursos].sort((a, b) => (a.orden ?? 99) - (b.orden ?? 99));

  return (
    <Sitio>
      <div className="pagina">
        <div className="fila">
          <h1 style={{ margin: 0 }}>Mi cuenta</h1>
          <a className="btn" href={urlSalir()}>Cerrar sesión</a>
        </div>
        <p className="muted">
          {usuario.nombre ? <><b>{usuario.nombre}</b>, </> : null}
          {usuario.email}{admin ? " (administrador)" : ""}
        </p>
        {admin && (
          <div className="caja fila">
            <div>
              <b>Panel de administración</b>
              <div className="aviso">Gestiona usuarios registrados, activa o revoca accesos, crea cupones y revisa pedidos.</div>
            </div>
            <Link className="btn primary" href="/admin">Abrir /admin</Link>
          </div>
        )}

        {avisoCorreo && <div className="caja" role="status">{avisoCorreo}</div>}
        {!usuario.verificado && (
          <div className="caja fila">
            <div>
              <b>Tu correo aún no está verificado</b>
              <div className="aviso">
                Puedes estudiar y comprar con normalidad. Verificarlo une esta cuenta con tu acceso por Google
                (mismo correo) y protege tus compras si alguien más intenta registrarlo.
                {!correoActivo && " El envío automático de enlaces se habilitará en cuanto conectemos el remitente del sitio."}
              </div>
            </div>
            {puedeReenviar && (
              <form method="post" action="/api/auth/verificar">
                <input type="hidden" name="accion" value="reenviar" />
                <button className="btn" type="submit">Enviarme el enlace</button>
              </form>
            )}
          </div>
        )}

        <h2>Mis cursos y certificados</h2>
        {listaCursos.map((c, idx) => {
          const lecciones = itemsDe(c.id);
          const hechas = lecciones.filter((i) => progreso[i.id]).length;
          const pct = lecciones.length ? Math.round((hechas / lecciones.length) * 100) : 0;
          const abierto = admin || activos.some((a) => cubre(a, c.id));
          const sigue = lecciones.find((i) => !progreso[i.id] && (abierto || i.gratis)) ?? lecciones[0];
          const completo = cursoCompletado(c.id, progreso);
          const certCodigo = completo ? idCertificado(usuario.id, c.id) : null;
          return (
            <div className="caja cuenta-curso" key={c.id}>
              <div className="fila">
                <div>
                  <span className="num">Curso {idx + 1}, {c.modulos} módulos</span>
                  <div style={{ fontWeight: 600, fontSize: "1.05rem", marginTop: ".15rem" }}>{c.titulo}</div>
                  <div className="aviso">
                    {hechas} de {lecciones.length} unidades ({pct} %), {abierto ? "acceso completo" : "solo la muestra gratuita"}
                    {completo ? ". Certificado disponible" : ""}
                  </div>
                </div>
                <span style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
                  <Link className="btn primary" href={`/leer/${sigue.id}`}>{completo ? "Repasar" : hechas ? "Continuar" : "Empezar"}</Link>
                  {certCodigo && (
                    <Link className="btn done-state" href={`/certificado/${encodeURIComponent(certCodigo)}`}>
                      Ver certificado
                    </Link>
                  )}
                  {abierto ? <a className="btn" href={`/descargar/${c.id}`}>Descargar código (.zip)</a>
                    : <Link className="btn" href={`/comprar?plan=curso&curso=${c.id}`}>Comprar</Link>}
                </span>
              </div>
              <div className="bar" style={{ marginTop: ".75rem" }}>
                <span style={{ width: `${pct}%`, background: completo ? "var(--ok)" : "var(--accent)" }} />
              </div>
            </div>
          );
        })}

        <h2>Perfil para certificados</h2>
        <div className="caja">
          <form className="form" method="post" action="/api/cuenta/nombre">
            <label>
              Nombre completo (tal como aparecerá en tus certificados verificables)
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
          <div className="caja">Aún no tienes un plan activo. <Link href="/#planes">Ver planes</Link></div>
        ) : accesos.map((a) => (
          <div className="caja fila" key={a.id}>
            <div>
              <b>{PLANES[a.plan].nombre}{a.alcance !== "todo" ? `: ${curso(a.alcance)?.titulo ?? a.alcance}` : ""}</b>
              <div className="aviso">
                Desde el {fecha(a.creado)}, {a.hasta ? `${new Date(a.hasta) > new Date() ? "vence" : "venció"} el ${fecha(a.hasta)}` : "sin vencimiento"}
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
