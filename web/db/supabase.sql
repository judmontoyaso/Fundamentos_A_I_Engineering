-- Tablas del curso en Supabase, en un esquema propio ("curso") para no mezclarse con otros proyectos.
--
-- Cómo aplicarlo (una sola vez):
--   1. Supabase → SQL Editor → pega este archivo completo → Run.
--   2. Supabase → Project Settings → Data API → "Exposed schemas" → añade  curso  → Save.
--
-- La app entra solo con la clave service role, desde el servidor. Las tablas tienen RLS activado y
-- ninguna política, así que la clave pública (publishable/anon) no puede leer ni escribir nada aquí.
-- Si cambias el nombre del esquema, define SUPABASE_SCHEMA con el mismo nombre en las variables de entorno.

create schema if not exists curso;

create table if not exists curso.usuarios (
  id      text primary key,                       -- id del proveedor de identidad (Auth0: "auth0|...")
  email   text not null,
  nombre  text,
  creado  timestamptz not null default now()
);
create index if not exists usuarios_email on curso.usuarios (email);

create table if not exists curso.progreso (
  user_id     text not null,
  item_id     text not null,                      -- id de la lección, p. ej. "m3-manual"
  hecho       boolean not null,
  actualizado timestamptz not null default now(),
  primary key (user_id, item_id)
);

create table if not exists curso.etiquetas (
  user_id     text not null,
  nb_id       text not null,                      -- tarea de anotación
  item_id     text not null,
  label       boolean not null,
  nota        text not null default '',
  actualizado timestamptz not null default now(),
  primary key (user_id, nb_id, item_id)
);

create table if not exists curso.pedidos (
  id            text primary key,                 -- también es la referencia que se envía a la pasarela
  user_id       text not null,
  email         text not null,
  plan          text not null check (plan in ('mensual', 'anual', 'curso', 'vitalicio')),
  curso         text,
  monto         numeric not null,
  moneda        text not null,
  proveedor     text not null,
  estado        text not null check (estado in ('pendiente', 'pagado', 'rechazado', 'reembolsado')),
  ref_proveedor text,
  creado        timestamptz not null default now()
);
create index if not exists pedidos_user on curso.pedidos (user_id);

create table if not exists curso.accesos (
  id        text primary key,
  user_id   text not null,
  plan      text not null check (plan in ('mensual', 'anual', 'curso', 'vitalicio')),
  alcance   text not null,                        -- 'todo' o el id de un curso
  estado    text not null check (estado in ('activo', 'revocado')),
  hasta     timestamptz,                          -- null = sin vencimiento
  origen    text not null,                        -- pasarela, o 'manual:<admin>'
  pedido_id text references curso.pedidos (id),
  creado    timestamptz not null default now()
);
create index if not exists accesos_user on curso.accesos (user_id);
create index if not exists accesos_pedido on curso.accesos (pedido_id);

create table if not exists curso.cupones (
  codigo     text primary key,
  porcentaje integer not null check (porcentaje >= 1 and porcentaje <= 100),
  plan       text check (plan in ('mensual', 'anual', 'curso', 'vitalicio')),
  curso      text,
  usos_max   integer,
  usos       integer not null default 0,
  activo     boolean not null default true,
  creado     timestamptz not null default now()
);

alter table curso.usuarios  enable row level security;
alter table curso.progreso  enable row level security;
alter table curso.etiquetas enable row level security;
alter table curso.pedidos   enable row level security;
alter table curso.accesos   enable row level security;
alter table curso.cupones   enable row level security;

-- Política explícita de bloqueo para roles cliente: el acceso ocurre únicamente desde el servidor con service_role.
drop policy if exists solo_servidor on curso.usuarios;
create policy solo_servidor on curso.usuarios for all to anon, authenticated using (false) with check (false);
drop policy if exists solo_servidor on curso.progreso;
create policy solo_servidor on curso.progreso for all to anon, authenticated using (false) with check (false);
drop policy if exists solo_servidor on curso.etiquetas;
create policy solo_servidor on curso.etiquetas for all to anon, authenticated using (false) with check (false);
drop policy if exists solo_servidor on curso.pedidos;
create policy solo_servidor on curso.pedidos for all to anon, authenticated using (false) with check (false);
drop policy if exists solo_servidor on curso.accesos;
create policy solo_servidor on curso.accesos for all to anon, authenticated using (false) with check (false);
drop policy if exists solo_servidor on curso.cupones;
create policy solo_servidor on curso.cupones for all to anon, authenticated using (false) with check (false);

-- Solo el rol de servicio (el servidor de la app) entra a este esquema.
revoke all on schema curso from anon, authenticated;
revoke all on all tables in schema curso from anon, authenticated;
grant usage on schema curso to service_role;
grant all on all tables in schema curso to service_role;
alter default privileges in schema curso grant all on tables to service_role;

-- El esquema "curso" se expone a la Data API desde el panel (paso 2 de arriba), no desde aquí.
-- Antes este archivo ejecutaba  alter role authenticator set pgrst.db_schemas = 'public, graphql_public, curso'
-- y eso REEMPLAZA la lista completa: en un proyecto compartido deja sin API a los esquemas de los otros productos.
notify pgrst, 'reload config';
notify pgrst, 'reload schema';
