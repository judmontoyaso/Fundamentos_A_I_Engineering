// Esquema de Postgres. La app lo aplica sola en la primera consulta (todo es "if not exists").
export const ESQUEMA = `
create table if not exists usuarios (
  id text primary key, email text not null, nombre text, creado timestamptz not null default now());
create index if not exists usuarios_email on usuarios (email);

create table if not exists progreso (
  user_id text not null, item_id text not null, hecho boolean not null,
  actualizado timestamptz not null default now(), primary key (user_id, item_id));

create table if not exists etiquetas (
  user_id text not null, nb_id text not null, item_id text not null, label boolean not null,
  nota text not null default '', actualizado timestamptz not null default now(),
  primary key (user_id, nb_id, item_id));

create table if not exists pedidos (
  id text primary key, user_id text not null, email text not null, plan text not null, curso text,
  monto numeric not null, moneda text not null, proveedor text not null, estado text not null,
  ref_proveedor text, creado timestamptz not null default now());

create table if not exists accesos (
  id text primary key, user_id text not null, plan text not null, alcance text not null, estado text not null,
  hasta timestamptz, origen text not null, pedido_id text, creado timestamptz not null default now());
create index if not exists accesos_user on accesos (user_id);

create table if not exists cupones (
  codigo text primary key, porcentaje integer not null, plan text, curso text,
  usos_max integer, usos integer not null default 0, activo boolean not null default true,
  creado timestamptz not null default now());
`;
