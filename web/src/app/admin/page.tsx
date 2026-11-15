// Panel completo de administración: gestionar usuarios (ver progreso, activar accesos, expulsar/eliminar),
// gestionar cupones de descuento (incluidos cupones 100 % gratis por curso/mes/plan), accesos y pedidos.
import type { Metadata } from "next";
import { revalidatePath } from "next/cache";
import { notFound } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { conceder, vigente } from "@/lib/acceso";
import { esAdmin, getUsuario } from "@/lib/auth";
import { curso, cursos } from "@/lib/contenido";
import { PLANES, esPlan, formatoMonto } from "@/lib/planes";
import { store } from "@/lib/store";
import type { PlanId } from "@/lib/tipos";

export const metadata: Metadata = { title: "Admin · IA en Producción", robots: { index: false } };
export const dynamic = "force-dynamic";

async function soloAdmin() {
  const u = await getUsuario();
  if (!esAdmin(u)) throw new Error("no autorizado");
  return u!;
}

async function activar(form: FormData) {
  "use server";
  const admin = await soloAdmin();
  const plan = form.get("plan");
  const cursoId = String(form.get("curso") ?? "");
  const destino = await store.usuarioPorEmail(String(form.get("email") ?? "").trim());
  if (!destino || !esPlan(plan) || (plan === "curso" && !curso(cursoId))) return;
  await conceder({ userId: destino.id, plan, curso: plan === "curso" ? cursoId : null, origen: `manual:${admin.email}` });
  revalidatePath("/admin");
}

async function revocar(form: FormData) {
  "use server";
  await soloAdmin();
  await store.revocarAcceso(String(form.get("id") ?? ""));
  revalidatePath("/admin");
}

async function expulsarUsuario(form: FormData) {
  "use server";
  const admin = await soloAdmin();
  const id = String(form.get("id") ?? "");
  if (!id || id === admin.id) return; // Evita que el admin se elimine a sí mismo
  await store.eliminarUsuario(id);
  revalidatePath("/admin");
}

async function crearCuponAction(form: FormData) {
  "use server";
  await soloAdmin();
  const codigo = String(form.get("codigo") ?? "").trim().toUpperCase().replace(/[^A-Z0-9_-]/g, "");
  const porcentaje = Math.min(100, Math.max(1, Number(form.get("porcentaje") ?? 100)));
  const planRaw = String(form.get("plan") ?? "");
  const cursoRaw = String(form.get("curso") ?? "");
  const usosMaxRaw = String(form.get("usosMax") ?? "").trim();

  if (!codigo) return;
  const plan: PlanId | null = esPlan(planRaw) ? planRaw : null;
  const cursoId = plan === "curso" && curso(cursoRaw) ? cursoRaw : null;
  const usosMax = usosMaxRaw && Number(usosMaxRaw) > 0 ? Math.round(Number(usosMaxRaw)) : null;

  await store.guardarCupon({
    codigo,
    porcentaje,
    plan,
    curso: cursoId,
    usosMax,
    activo: true,
  });
  revalidatePath("/admin");
}

async function borrarCuponAction(form: FormData) {
  "use server";
  await soloAdmin();
  const codigo = String(form.get("codigo") ?? "");
  if (codigo) await store.eliminarCupon(codigo);
  revalidatePath("/admin");
}

async function cancelarPedidoAction(form: FormData) {
  "use server";
  await soloAdmin();
  const id = String(form.get("id") ?? "");
  if (id) await store.transicionPedido(id, ["pendiente"], "rechazado", null);
  revalidatePath("/admin");
}

const corta = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString("es-CO") : "—");

export default async function Admin() {
  const adminActual = await getUsuario();
  if (!esAdmin(adminActual)) notFound();

  const [usuarios, cupones, accesos, pedidos] = await Promise.all([
    store.usuariosRecientes(100),
    store.cupones(),
    store.accesosRecientes(100),
    store.pedidosRecientes(100),
  ]);

  return (
    <Sitio>
      <div className="pagina ancha">
        <h1>Administración</h1>
        <p className="muted">
          Sesión activa como <b>{adminActual!.email}</b>. Desde aquí administras usuarios, cupones de descuento/becas,
          accesos y pedidos.
        </p>

        {/* 1. USUARIOS REGISTRADOS */}
        <h2>Usuarios registrados ({usuarios.length})</h2>
        <div className="caja table-scroll">
          <table className="tabla">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Registro</th>
                <th>Avance</th>
                <th>Rol</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => {
                const esElMismo = u.id === adminActual!.id;
                return (
                  <tr key={u.id}>
                    <td><b>{u.nombre ?? "—"}</b></td>
                    <td>{u.email}</td>
                    <td>{corta(u.creado)}</td>
                    <td><span className="mono">{u.unidadesHechas}</span> unidades</td>
                    <td>
                      {esAdmin({ ...u, nombre: u.nombre ?? undefined, verificado: true }) ? (
                        <span className="estado ok">admin</span>
                      ) : (
                        <span className="aviso">estudiante</span>
                      )}
                    </td>
                    <td>
                      {!esElMismo ? (
                        <form action={expulsarUsuario}>
                          <input type="hidden" name="id" value={u.id} />
                          <button className="link-btn" style={{ color: "var(--err)" }}>
                            sacar / eliminar
                          </button>
                        </form>
                      ) : (
                        <span className="aviso">tú</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {usuarios.length === 0 && (
                <tr><td colSpan={6} className="muted">Sin usuarios registrados todavía.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* 2. CUPONES DE DESCUENTO Y BECAS */}
        <h2>Cupones de descuento y pases gratis ({cupones.length})</h2>
        <div className="caja">
          <form className="form" action={crearCuponAction}>
            <div style={{ display: "grid", gap: ".8rem", gridTemplateColumns: "repeat(auto-fit, minmax(12rem, 1fr))" }}>
              <label>
                Código del cupón
                <input
                  type="text"
                  name="codigo"
                  placeholder="Ej. BECAMES100"
                  required
                  style={{ textTransform: "uppercase", fontFamily: "'IBM Plex Mono', monospace" }}
                />
              </label>
              <label>
                Descuento (% · usa 100 para gratis)
                <input type="number" name="porcentaje" min={1} max={100} defaultValue={100} required />
              </label>
              <label>
                Plan aplicable
                <select name="plan" defaultValue="">
                  <option value="">Cualquier plan</option>
                  {Object.values(PLANES).map((p) => (
                    <option key={p.id} value={p.id}>{p.nombre} ({p.resumen})</option>
                  ))}
                </select>
              </label>
              <label>
                Curso (solo si eliges «Un curso»)
                <select name="curso" defaultValue="">
                  <option value="">Cualquier curso</option>
                  {cursos.map((c) => <option key={c.id} value={c.id}>{c.titulo}</option>)}
                </select>
              </label>
              <label>
                Límite de usos (vacío = ilimitado)
                <input type="number" name="usosMax" min={1} placeholder="Ilimitado" />
              </label>
            </div>
            <button className="btn primary" type="submit">Guardar cupón</button>
          </form>
        </div>

        <div className="caja table-scroll">
          <table className="tabla">
            <thead>
              <tr>
                <th>Código</th>
                <th>Descuento</th>
                <th>Alcance</th>
                <th>Usos</th>
                <th>Link directo de canje</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {cupones.map((c) => {
                const planLink = c.plan ?? "mensual";
                const cursoQuery = c.curso ? `&curso=${c.curso}` : planLink === "curso" ? "&curso=agentes" : "";
                const linkCanje = `/comprar?plan=${planLink}${cursoQuery}&cupon=${c.codigo}`;
                return (
                  <tr key={c.codigo}>
                    <td><code className="ref" style={{ fontWeight: 700 }}>{c.codigo}</code></td>
                    <td>
                      <span className={"estado " + (c.porcentaje >= 100 ? "ok" : "pend")}>
                        {c.porcentaje >= 100 ? "100 % GRATIS" : `-${c.porcentaje} %`}
                      </span>
                    </td>
                    <td>
                      {c.plan ? PLANES[c.plan]?.nombre ?? c.plan : "Todos los planes"}
                      {c.curso ? ` · ${c.curso}` : ""}
                    </td>
                    <td className="mono">{c.usos}{c.usosMax !== null ? ` / ${c.usosMax}` : " / ∞"}</td>
                    <td><a href={linkCanje} className="mono" style={{ fontSize: ".78rem" }}>{linkCanje}</a></td>
                    <td>
                      <form action={borrarCuponAction}>
                        <input type="hidden" name="codigo" value={c.codigo} />
                        <button className="link-btn" style={{ color: "var(--err)" }}>eliminar</button>
                      </form>
                    </td>
                  </tr>
                );
              })}
              {cupones.length === 0 && <tr><td colSpan={6} className="muted">Sin cupones creados.</td></tr>}
            </tbody>
          </table>
        </div>

        {/* 3. ACTIVAR ACCESO DIRECTO A UN CORREO */}
        <h2>Activar un acceso directo a un usuario</h2>
        <form className="form caja" action={activar}>
          <div style={{ display: "grid", gap: ".8rem", gridTemplateColumns: "repeat(auto-fit, minmax(14rem, 1fr))" }}>
            <label>
              Correo de la cuenta registrada
              <input type="email" name="email" placeholder="usuario@correo.com" required />
            </label>
            <label>
              Plan
              <select name="plan" defaultValue="anual">
                {Object.values(PLANES).map((p) => <option key={p.id} value={p.id}>{p.nombre} · {p.resumen}</option>)}
              </select>
            </label>
            <label>
              Curso (solo para el plan «Un curso»)
              <select name="curso" defaultValue="">
                <option value="">—</option>
                {cursos.map((c) => <option key={c.id} value={c.id}>{c.titulo}</option>)}
              </select>
            </label>
          </div>
          <button className="btn primary">Conceder acceso</button>
        </form>

        {/* 4. ACCESOS RECIENTES */}
        <h2>Accesos recientes</h2>
        <div className="caja table-scroll">
          <table className="tabla">
            <thead><tr><th>Cuenta</th><th>Plan</th><th>Alcance</th><th>Vence</th><th>Origen</th><th>Estado</th><th /></tr></thead>
            <tbody>
              {accesos.map((a) => (
                <tr key={a.id}>
                  <td>{a.email ?? a.userId}</td>
                  <td>{PLANES[a.plan]?.nombre ?? a.plan}</td>
                  <td>{a.alcance}</td>
                  <td>{corta(a.hasta)}</td>
                  <td>{a.origen}</td>
                  <td>
                    <span className={"estado " + (vigente(a) ? "ok" : "no")}>
                      {a.estado === "revocado" ? "revocado" : vigente(a) ? "activo" : "vencido"}
                    </span>
                  </td>
                  <td>
                    {a.estado === "activo" && (
                      <form action={revocar}>
                        <input type="hidden" name="id" value={a.id} />
                        <button className="link-btn">revocar</button>
                      </form>
                    )}
                  </td>
                </tr>
              ))}
              {accesos.length === 0 && <tr><td colSpan={7} className="muted">Sin accesos todavía.</td></tr>}
            </tbody>
          </table>
        </div>

        {/* 5. PEDIDOS RECIENTES */}
        <h2>Pedidos recientes</h2>
        <div className="caja table-scroll">
          <table className="tabla">
            <thead><tr><th>Fecha</th><th>Cuenta</th><th>Plan</th><th>Monto</th><th>Pasarela</th><th>Estado</th><th>Ref.</th><th /></tr></thead>
            <tbody>
              {pedidos.map((p) => (
                <tr key={p.id}>
                  <td>{corta(p.creado)}</td>
                  <td>{p.email}</td>
                  <td>{p.plan}{p.curso ? ` · ${p.curso}` : ""}</td>
                  <td>{formatoMonto(p.monto, p.moneda)}</td>
                  <td>{p.proveedor}</td>
                  <td>
                    <span className={"estado " + (p.estado === "pagado" ? "ok" : p.estado === "pendiente" ? "pend" : "no")}>
                      {p.estado}
                    </span>
                  </td>
                  <td className="mono">{p.refProveedor ?? "—"}</td>
                  <td>
                    {p.estado === "pendiente" && (
                      <form action={cancelarPedidoAction}>
                        <input type="hidden" name="id" value={p.id} />
                        <button className="link-btn">cancelar</button>
                      </form>
                    )}
                  </td>
                </tr>
              ))}
              {pedidos.length === 0 && <tr><td colSpan={8} className="muted">Sin pedidos todavía.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </Sitio>
  );
}
