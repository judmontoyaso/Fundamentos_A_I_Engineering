# Web del curso

La versión que se vende: página de venta, cuentas, pagos y lector con el contenido protegido en el servidor.
Un solo proyecto Next.js (App Router). El contenido no vive aquí: se compila desde las carpetas `modulo-*` y
`curso-*` de la raíz del repositorio cada vez que arrancas o construyes.

## Probarla en local, sin configurar nada

```bash
npm install
```

```bash
STORE=archivo npm run dev
```

Sin Auth0 la app entra en **modo desarrollo**: login de prueba sin contraseña, un "pago simulado" que aprueba
la compra sin cobrar, y los datos en `.data/store.json`. Nada de eso existe en producción.
`STORE=archivo` fuerza el almacenamiento local aunque `.env.local` tenga las claves de Supabase.

## Cómo está organizada

| Ruta | Qué hace |
|---|---|
| `scripts/build-content.mjs` | Convierte manuales, ejercicios, scripts y autoevaluaciones a `src/content/` (no se versiona). Ahí se define qué lecciones son gratis (`GRATIS`). |
| `src/lib/auth.ts` | `getUsuario()`: Auth0 en producción, login de prueba en desarrollo. |
| `src/lib/acceso.ts` | Reglas: quién puede leer qué, conceder y revocar accesos. |
| `src/lib/planes.ts` | Los tres planes y sus precios. |
| `src/lib/store.ts` | Persistencia: Supabase, Postgres directo o archivo local. |
| `src/lib/pagos/` | Una pasarela por archivo, detrás de la interfaz `Proveedor`. |
| `src/app/leer/[id]` | El lector. Si no hay acceso, el HTML de la lección no se envía. |
| `src/app/admin` | Activar o revocar accesos a mano y ver pedidos. |

Los planes mensual y anual son **pagos únicos por un periodo** (30 y 365 días); no hay cobro recurrente.
Renovar es volver a comprar, y el nuevo periodo se suma al vigente.

## Puesta en producción

### 1. Base de datos (Supabase)

1. SQL Editor → pega `db/supabase.sql` → Run. Crea el esquema `curso` con sus tablas.
2. Project Settings → Data API → Exposed schemas → añade `curso`.
3. Variables: `NEXT_PUBLIC_SUPABASE_URL` y `SERVICE_ROLE` (o `SUPABASE_SERVICE_ROLE_KEY`).

La clave service role solo se usa en el servidor. Las tablas tienen RLS sin políticas, así que la clave pública
no puede leerlas. Alternativa: definir `DATABASE_URL` con la cadena de conexión de Postgres; en ese caso las
tablas se crean solas en el esquema por defecto.

### 2. Cuentas (Auth0)

1. Crea una aplicación de tipo **Regular Web Application**.
2. Allowed Callback URLs: `https://TU-DOMINIO/auth/callback` (y `http://localhost:3000/auth/callback` para probar).
3. Allowed Logout URLs: `https://TU-DOMINIO` (y `http://localhost:3000`).
4. Variables: `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`, `AUTH0_SECRET` (`openssl rand -hex 32`) y `APP_BASE_URL`.

Pon tu correo en `ADMIN_EMAILS` para ver `/admin`. El correo debe estar verificado en Auth0.

### 3. Precios

Las pasarelas locales cobran en moneda local. Define `PAGOS_MONEDA=COP` y el monto de cada plan en pesos:
`PRECIO_MENSUAL`, `PRECIO_ANUAL`, `PRECIO_CURSO`. La página muestra el precio de referencia en USD y el monto
exacto antes de pagar.

### 4. Pasarelas

Se activa cada una al definir sus variables; si hay varias, el comprador elige.

- **Mercado Pago** (Checkout Pro): `MP_ACCESS_TOKEN` y `MP_WEBHOOK_SECRET`.
  Webhook: `https://TU-DOMINIO/api/webhooks/mercadopago`, evento "Pagos".
- **Wompi** (Web Checkout, solo COP): `WOMPI_PUBLIC_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`.
  URL de eventos: `https://TU-DOMINIO/api/webhooks/wompi`.
- **Transferencia**: `PAGO_MANUAL_INSTRUCCIONES` con el texto a mostrar; activas el acceso desde `/admin`.

El aviso de la pasarela nunca se toma como verdad: solo aporta el id del pago, y el estado, el monto y la
moneda se consultan a la pasarela antes de activar nada. Prueba primero con las credenciales de prueba de cada una.

Para añadir otra pasarela (por ejemplo Lemon Squeezy): un archivo en `src/lib/pagos/` que implemente
`Proveedor` y una línea en la lista `TODOS` de `src/lib/pagos/index.ts`.

### 5. Despliegue (Vercel)

1. Importa el repositorio y pon **Root Directory** = `web`.
2. Copia las variables de `.env.example` con sus valores.
3. Despliega. El paso `prebuild` compila el contenido desde la raíz del repositorio.

## Pendiente antes de cobrar

- Revisar `src/app/terminos` y `src/app/privacidad`: son borradores y les falta el nombre e identificación del vendedor.
- Hacer un pago real de prueba con cada pasarela: las integraciones de Mercado Pago y Wompi están escritas
  según su documentación, pero no se han ejecutado contra cuentas reales.
