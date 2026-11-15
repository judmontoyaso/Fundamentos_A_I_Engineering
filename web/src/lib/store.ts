// Persistencia. Tres implementaciones con la misma interfaz; se elige por variables de entorno:
//   - Postgres directo, si existe DATABASE_URL. Las tablas se crean solas la primera vez (ver esquema.ts).
//   - Supabase por su API, si existen la URL y la clave service role (ver store-supabase.ts y db/supabase.sql).
//   - Un archivo JSON en .data/ (desarrollo local, o STORE=archivo). No sirve para producción.
import "server-only";
import fs from "node:fs";
import path from "node:path";
import postgres from "postgres";
import { ESQUEMA } from "./esquema";
import { aAcceso, aPedido } from "./filas";
import { supabase } from "./store-supabase";
import type { Acceso, EstadoPedido, Etiquetas, Pedido, Progreso, Usuario } from "./tipos";

export interface Store {
  registrarUsuario(u: Usuario): Promise<void>;
  usuarioPorEmail(email: string): Promise<{ id: string; email: string; nombre?: string } | null>;
  progreso(userId: string): Promise<Progreso>;
  marcar(userId: string, itemId: string, hecho: boolean): Promise<void>;
  etiquetas(userId: string, nbId: string): Promise<Etiquetas>;
  etiquetar(userId: string, nbId: string, itemId: string, label: boolean, nota: string): Promise<void>;
  accesos(userId: string): Promise<Acceso[]>;
  crearAcceso(a: Acceso): Promise<void>;
  revocarAcceso(id: string): Promise<void>;
  revocarPorPedido(pedidoId: string): Promise<void>;
  accesosRecientes(n: number): Promise<(Acceso & { email: string | null })[]>;
  crearPedido(p: Pedido): Promise<void>;
  pedido(id: string): Promise<Pedido | null>;
  /** Cambia el estado solo si el actual está en `desde`. Devuelve si hubo cambio (base de la idempotencia). */
  transicionPedido(id: string, desde: EstadoPedido[], a: EstadoPedido, refProveedor: string | null): Promise<boolean>;
  pedidosRecientes(n: number): Promise<Pedido[]>;
}

// ---------------------------------------------------------------- Postgres
function pg(url: string): Store {
  const sql = postgres(url, { max: 5, prepare: false, idle_timeout: 20 });
  let listo: Promise<unknown> | null = null;
  const ok = () => (listo ??= sql.unsafe(ESQUEMA).catch((e) => { listo = null; throw e; }));
  return {
    async registrarUsuario(u) {
      await ok();
      await sql`insert into usuarios (id, email, nombre) values (${u.id}, ${u.email}, ${u.nombre ?? null})
                on conflict (id) do update set email = excluded.email, nombre = excluded.nombre`;
    },
    async usuarioPorEmail(email) {
      await ok();
      const r = await sql`select id, email, nombre from usuarios where email = ${email.toLowerCase()} order by creado limit 1`;
      return r[0] ? { id: r[0].id, email: r[0].email, nombre: r[0].nombre ?? undefined } : null;
    },
    async progreso(userId) {
      await ok();
      const r = await sql`select item_id, hecho from progreso where user_id = ${userId}`;
      return Object.fromEntries(r.map((x) => [x.item_id, x.hecho]));
    },
    async marcar(userId, itemId, hecho) {
      await ok();
      await sql`insert into progreso (user_id, item_id, hecho) values (${userId}, ${itemId}, ${hecho})
                on conflict (user_id, item_id) do update set hecho = excluded.hecho, actualizado = now()`;
    },
    async etiquetas(userId, nbId) {
      await ok();
      const r = await sql`select item_id, label, nota from etiquetas where user_id = ${userId} and nb_id = ${nbId}`;
      return Object.fromEntries(r.map((x) => [x.item_id, { label: x.label, nota: x.nota }]));
    },
    async etiquetar(userId, nbId, itemId, label, nota) {
      await ok();
      await sql`insert into etiquetas (user_id, nb_id, item_id, label, nota) values (${userId}, ${nbId}, ${itemId}, ${label}, ${nota})
                on conflict (user_id, nb_id, item_id) do update set label = excluded.label, nota = excluded.nota, actualizado = now()`;
    },
    async accesos(userId) {
      await ok();
      return (await sql`select * from accesos where user_id = ${userId} order by creado desc`).map(aAcceso);
    },
    async crearAcceso(a) {
      await ok();
      await sql`insert into accesos (id, user_id, plan, alcance, estado, hasta, origen, pedido_id)
                values (${a.id}, ${a.userId}, ${a.plan}, ${a.alcance}, ${a.estado}, ${a.hasta}, ${a.origen}, ${a.pedidoId})`;
    },
    async revocarAcceso(id) {
      await ok();
      await sql`update accesos set estado = 'revocado' where id = ${id}`;
    },
    async revocarPorPedido(pedidoId) {
      await ok();
      await sql`update accesos set estado = 'revocado' where pedido_id = ${pedidoId}`;
    },
    async accesosRecientes(n) {
      await ok();
      const r = await sql`select a.*, u.email from accesos a left join usuarios u on u.id = a.user_id order by a.creado desc limit ${n}`;
      return r.map((x) => ({ ...aAcceso(x), email: x.email ?? null }));
    },
    async crearPedido(p) {
      await ok();
      await sql`insert into pedidos (id, user_id, email, plan, curso, monto, moneda, proveedor, estado, ref_proveedor)
                values (${p.id}, ${p.userId}, ${p.email}, ${p.plan}, ${p.curso}, ${p.monto}, ${p.moneda}, ${p.proveedor}, ${p.estado}, ${p.refProveedor})`;
    },
    async pedido(id) {
      await ok();
      const r = await sql`select * from pedidos where id = ${id}`;
      return r[0] ? aPedido(r[0]) : null;
    },
    async transicionPedido(id, desde, a, ref) {
      await ok();
      const r = await sql`update pedidos set estado = ${a}, ref_proveedor = coalesce(${ref}, ref_proveedor)
                          where id = ${id} and estado in ${sql(desde)} returning id`;
      return r.length > 0;
    },
    async pedidosRecientes(n) {
      await ok();
      return (await sql`select * from pedidos order by creado desc limit ${n}`).map(aPedido);
    },
  };
}

// ---------------------------------------------------------------- Archivo (desarrollo)
type Datos = {
  usuarios: Record<string, { id: string; email: string; nombre?: string }>;
  progreso: Record<string, Progreso>;
  etiquetas: Record<string, Etiquetas>;
  accesos: Acceso[];
  pedidos: Pedido[];
};

function archivo(ruta: string): Store {
  const leer = (): Datos => {
    try {
      return JSON.parse(fs.readFileSync(ruta, "utf8"));
    } catch {
      return { usuarios: {}, progreso: {}, etiquetas: {}, accesos: [], pedidos: [] };
    }
  };
  const mutar = <T>(f: (d: Datos) => T): T => {
    const d = leer();
    const r = f(d);
    fs.mkdirSync(path.dirname(ruta), { recursive: true });
    fs.writeFileSync(ruta, JSON.stringify(d, null, 1));
    return r;
  };
  return {
    async registrarUsuario(u) { mutar((d) => { d.usuarios[u.id] = { id: u.id, email: u.email, nombre: u.nombre }; }); },
    async usuarioPorEmail(email) { return Object.values(leer().usuarios).find((u) => u.email === email.toLowerCase()) ?? null; },
    async progreso(userId) { return leer().progreso[userId] ?? {}; },
    async marcar(userId, itemId, hecho) { mutar((d) => { (d.progreso[userId] ??= {})[itemId] = hecho; }); },
    async etiquetas(userId, nbId) { return leer().etiquetas[`${userId}::${nbId}`] ?? {}; },
    async etiquetar(userId, nbId, itemId, label, nota) { mutar((d) => { (d.etiquetas[`${userId}::${nbId}`] ??= {})[itemId] = { label, nota }; }); },
    async accesos(userId) { return leer().accesos.filter((a) => a.userId === userId).reverse(); },
    async crearAcceso(a) { mutar((d) => { d.accesos.push(a); }); },
    async revocarAcceso(id) { mutar((d) => { d.accesos.forEach((a) => { if (a.id === id) a.estado = "revocado"; }); }); },
    async revocarPorPedido(pedidoId) { mutar((d) => { d.accesos.forEach((a) => { if (a.pedidoId === pedidoId) a.estado = "revocado"; }); }); },
    async accesosRecientes(n) {
      const d = leer();
      return d.accesos.slice(-n).reverse().map((a) => ({ ...a, email: d.usuarios[a.userId]?.email ?? null }));
    },
    async crearPedido(p) { mutar((d) => { d.pedidos.push(p); }); },
    async pedido(id) { return leer().pedidos.find((p) => p.id === id) ?? null; },
    async transicionPedido(id, desde, a, ref) {
      return mutar((d) => {
        const p = d.pedidos.find((x) => x.id === id);
        if (!p || !desde.includes(p.estado)) return false;
        p.estado = a;
        if (ref) p.refProveedor = ref;
        return true;
      });
    },
    async pedidosRecientes(n) { return leer().pedidos.slice(-n).reverse(); },
  };
}

function crear(): Store {
  if (process.env.STORE === "archivo") return archivo(path.join(process.cwd(), ".data", "store.json"));
  if (process.env.DATABASE_URL) return pg(process.env.DATABASE_URL);
  const url = process.env.SUPABASE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  const clave = process.env.SUPABASE_SERVICE_ROLE_KEY ?? process.env.SERVICE_ROLE;
  if (url && clave) return supabase(url, clave, process.env.SUPABASE_SCHEMA ?? "curso");
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PHASE !== "phase-production-build")
    console.warn("[store] No hay base de datos configurada: usando un archivo local, que no persiste en un despliegue real.");
  return archivo(path.join(process.cwd(), ".data", "store.json"));
}

const g = globalThis as unknown as { __store?: Store };
export const store: Store = (g.__store ??= crear());
