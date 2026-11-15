// Panel mínimo del dueño: activar accesos a mano (transferencias, cortesías), revocarlos y ver los pedidos.
import type { Metadata } from "next";
import { revalidatePath } from "next/cache";
import { notFound } from "next/navigation";
import { Sitio } from "@/components/Sitio";
import { conceder, vigente } from "@/lib/acceso";
import { esAdmin, getUsuario } from "@/lib/auth";
import { curso, cursos } from "@/lib/contenido";
import { PLANES, esPlan, formatoMonto } from "@/lib/planes";
import { store } from "@/lib/store";

export const metadata: Metadata = { title: "Admin", robots: { index: false } };
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

const corta = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString("es-CO") : "—");

export default async function Admin() {
  if (!esAdmin(await getUsuario())) notFound();
  const [accesos, pedidos] = await Promise.all([store.accesosRecientes(100), store.pedidosRecientes(100)]);

  return (
    <Sitio>
      <div className="pagina ancha">
        <h1>Administración</h1>

        <h2>Activar un acceso a mano</h2>
        <form className="form caja" action={activar}>
          <label>Correo de la cuenta (la persona debe haberse registrado antes)<input type="email" name="email" required /></label>
          <label>Plan
            <select name="plan" defaultValue="anual">
              {Object.values(PLANES).map((p) => <option key={p.id} value={p.id}>{p.nombre} · {p.resumen}</option>)}
            </select>
          </label>
          <label>Curso (solo para el plan por curso)
            <select name="curso" defaultValue="">
              <option value="">—</option>
              {cursos.map((c) => <option key={c.id} value={c.id}>{c.titulo}</option>)}
            </select>
          </label>
          <button className="btn primary">Activar</button>
        </form>

        <h2>Accesos recientes</h2>
        <div className="caja table-scroll">
          <table className="tabla">
            <thead><tr><th>Cuenta</th><th>Plan</th><th>Alcance</th><th>Vence</th><th>Origen</th><th>Estado</th><th /></tr></thead>
            <tbody>
              {accesos.map((a) => (
                <tr key={a.id}>
                  <td>{a.email ?? a.userId}</td><td>{PLANES[a.plan]?.nombre ?? a.plan}</td><td>{a.alcance}</td>
                  <td>{corta(a.hasta)}</td><td>{a.origen}</td>
                  <td><span className={"estado " + (vigente(a) ? "ok" : "no")}>{a.estado === "revocado" ? "revocado" : vigente(a) ? "activo" : "vencido"}</span></td>
                  <td>{a.estado === "activo" && <form action={revocar}><input type="hidden" name="id" value={a.id} /><button className="link-btn">revocar</button></form>}</td>
                </tr>
              ))}
              {accesos.length === 0 && <tr><td colSpan={7} className="muted">Sin accesos todavía.</td></tr>}
            </tbody>
          </table>
        </div>

        <h2>Pedidos recientes</h2>
        <div className="caja table-scroll">
          <table className="tabla">
            <thead><tr><th>Fecha</th><th>Cuenta</th><th>Plan</th><th>Monto</th><th>Pasarela</th><th>Estado</th><th>Ref.</th></tr></thead>
            <tbody>
              {pedidos.map((p) => (
                <tr key={p.id}>
                  <td>{corta(p.creado)}</td><td>{p.email}</td><td>{p.plan}{p.curso ? ` · ${p.curso}` : ""}</td>
                  <td>{formatoMonto(p.monto, p.moneda)}</td><td>{p.proveedor}</td>
                  <td><span className={"estado " + (p.estado === "pagado" ? "ok" : p.estado === "pendiente" ? "pend" : "no")}>{p.estado}</span></td>
                  <td className="mono">{p.refProveedor ?? "—"}</td>
                </tr>
              ))}
              {pedidos.length === 0 && <tr><td colSpan={7} className="muted">Sin pedidos todavía.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </Sitio>
  );
}
