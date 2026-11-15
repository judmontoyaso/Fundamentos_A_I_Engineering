// Store sobre la API de Supabase, con la clave service role (solo servidor) y un esquema propio.
// Las tablas se crean una vez con db/supabase.sql, y el esquema debe estar en "Exposed schemas" de la API.
import "server-only";
import { createClient } from "@supabase/supabase-js";
import { aAcceso, aCupon, aPedido } from "./filas";
import type { Store } from "./store";

type Res<T> = PromiseLike<{ data: T | null; error: { message: string; code?: string } | null }>;

export function supabase(url: string, claveServicio: string, esquema: string): Store {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const db = createClient<any, any, any>(url, claveServicio, {
    db: { schema: esquema },
    auth: { persistSession: false, autoRefreshToken: false },
    global: { fetch: (input, init) => fetch(input, { ...init, cache: "no-store" }) },
  });

  async function q<T>(p: Res<T>): Promise<T> {
    const { data, error } = await p;
    if (error) {
      const pista = error.code === "PGRST106" || error.code === "42P01" || error.code === "PGRST205"
        ? ` — ¿ejecutaste db/supabase.sql y expusiste el esquema "${esquema}" en la API de Supabase?` : "";
      throw new Error(`Supabase: ${error.message}${pista}`);
    }
    return data as T;
  }
  type Filas = Record<string, any>[]; // eslint-disable-line @typescript-eslint/no-explicit-any

  return {
    async registrarUsuario(u) {
      await q(db.from("usuarios").upsert({ id: u.id, email: u.email, nombre: u.nombre ?? null }, { onConflict: "id" }));
    },
    async usuarioPorEmail(email) {
      const r = await q<Filas>(db.from("usuarios").select("id, email, nombre").eq("email", email.toLowerCase()).order("creado").limit(1));
      return r[0] ? { id: r[0].id, email: r[0].email, nombre: r[0].nombre ?? undefined } : null;
    },
    async usuariosRecientes(n) {
      const us = await q<Filas>(db.from("usuarios").select("*").order("creado", { ascending: false }).limit(n));
      const ids = us.map((u) => u.id as string);
      const prog = ids.length ? await q<Filas>(db.from("progreso").select("user_id").eq("hecho", true).in("user_id", ids)) : [];
      const conteo = new Map<string, number>();
      for (const p of prog) conteo.set(p.user_id, (conteo.get(p.user_id) ?? 0) + 1);
      return us.map((u) => ({
        id: String(u.id),
        email: String(u.email),
        nombre: u.nombre ?? null,
        creado: new Date(u.creado).toISOString(),
        unidadesHechas: conteo.get(u.id) ?? 0,
      }));
    },
    async eliminarUsuario(id) {
      await q(db.from("accesos").update({ estado: "revocado" }).eq("user_id", id));
      await q(db.from("progreso").delete().eq("user_id", id));
      await q(db.from("etiquetas").delete().eq("user_id", id));
      await q(db.from("usuarios").delete().eq("id", id));
    },
    async usuariosPorEmail(email) {
      const r = await q<Filas>(db.from("usuarios").select("id, email, nombre").eq("email", email.toLowerCase()).order("creado"));
      return r.map((x) => ({ id: x.id, email: x.email, nombre: x.nombre ?? undefined }));
    },
    async accesosPorVencer(desde, hasta) {
      const filas = await q<Filas>(db.from("accesos").select("*").eq("estado", "activo").gte("hasta", desde).lt("hasta", hasta));
      if (!filas.length) return [];
      const us = await q<Filas>(db.from("usuarios").select("id, email").in("id", [...new Set(filas.map((f) => f.user_id))]));
      const correo = new Map(us.map((u) => [u.id, u.email as string]));
      return filas.map((f) => ({ ...aAcceso(f), email: correo.get(f.user_id) ?? null }));
    },
    async progreso(userId) {
      const r = await q<Filas>(db.from("progreso").select("item_id, hecho").eq("user_id", userId));
      return Object.fromEntries(r.map((x) => [x.item_id, x.hecho]));
    },
    async marcar(userId, itemId, hecho) {
      await q(db.from("progreso").upsert({ user_id: userId, item_id: itemId, hecho, actualizado: new Date().toISOString() },
        { onConflict: "user_id,item_id" }));
    },
    async etiquetas(userId, nbId) {
      const r = await q<Filas>(db.from("etiquetas").select("item_id, label, nota").eq("user_id", userId).eq("nb_id", nbId));
      return Object.fromEntries(r.map((x) => [x.item_id, { label: x.label, nota: x.nota }]));
    },
    async etiquetar(userId, nbId, itemId, label, nota) {
      await q(db.from("etiquetas").upsert(
        { user_id: userId, nb_id: nbId, item_id: itemId, label, nota, actualizado: new Date().toISOString() },
        { onConflict: "user_id,nb_id,item_id" }));
    },
    async accesos(userId) {
      return (await q<Filas>(db.from("accesos").select("*").eq("user_id", userId).order("creado", { ascending: false }))).map(aAcceso);
    },
    async crearAcceso(a) {
      await q(db.from("accesos").insert({
        id: a.id, user_id: a.userId, plan: a.plan, alcance: a.alcance, estado: a.estado, hasta: a.hasta,
        origen: a.origen, pedido_id: a.pedidoId, creado: a.creado,
      }));
    },
    async revocarAcceso(id) {
      await q(db.from("accesos").update({ estado: "revocado" }).eq("id", id));
    },
    async revocarPorPedido(pedidoId) {
      await q(db.from("accesos").update({ estado: "revocado" }).eq("pedido_id", pedidoId));
    },
    async accesosRecientes(n) {
      const filas = await q<Filas>(db.from("accesos").select("*").order("creado", { ascending: false }).limit(n));
      const ids = [...new Set(filas.map((f) => f.user_id))];
      const us = ids.length ? await q<Filas>(db.from("usuarios").select("id, email").in("id", ids)) : [];
      const email = new Map(us.map((u) => [u.id, u.email as string]));
      return filas.map((f) => ({ ...aAcceso(f), email: email.get(f.user_id) ?? null }));
    },
    async crearPedido(p) {
      await q(db.from("pedidos").insert({
        id: p.id, user_id: p.userId, email: p.email, plan: p.plan, curso: p.curso, monto: p.monto, moneda: p.moneda,
        proveedor: p.proveedor, estado: p.estado, ref_proveedor: p.refProveedor, creado: p.creado,
      }));
    },
    async pedido(id) {
      const r = await q<Filas>(db.from("pedidos").select("*").eq("id", id).limit(1));
      return r[0] ? aPedido(r[0]) : null;
    },
    async transicionPedido(id, desde, a, ref) {
      const cambio = ref ? { estado: a, ref_proveedor: ref } : { estado: a };
      const r = await q<Filas>(db.from("pedidos").update(cambio).eq("id", id).in("estado", desde).select("id"));
      return r.length > 0;
    },
    async pedidosRecientes(n) {
      return (await q<Filas>(db.from("pedidos").select("*").order("creado", { ascending: false }).limit(n))).map(aPedido);
    },
    async cupon(codigo) {
      const r = await q<Filas>(db.from("cupones").select("*").eq("codigo", codigo.trim().toUpperCase()).limit(1));
      return r[0] ? aCupon(r[0]) : null;
    },
    async cupones() {
      return (await q<Filas>(db.from("cupones").select("*").order("creado", { ascending: false }))).map(aCupon);
    },
    async guardarCupon(c) {
      await q(db.from("cupones").upsert({
        codigo: c.codigo.trim().toUpperCase(),
        porcentaje: c.porcentaje,
        plan: c.plan,
        curso: c.curso,
        usos_max: c.usosMax,
        activo: c.activo,
      }, { onConflict: "codigo" }));
    },
    async usarCupon(codigo) {
      const actual = await this.cupon(codigo);
      if (!actual || !actual.activo || (actual.usosMax !== null && actual.usos >= actual.usosMax)) return false;
      await q(db.from("cupones").update({ usos: actual.usos + 1 }).eq("codigo", actual.codigo));
      return true;
    },
    async eliminarCupon(codigo) {
      await q(db.from("cupones").delete().eq("codigo", codigo.trim().toUpperCase()));
    },
  };
}
