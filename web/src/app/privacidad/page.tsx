// BORRADOR: debe revisarlo el titular antes de vender. Falta identificar al responsable del tratamiento
// (nombre o razón social, identificación, domicilio) como exige la Ley 1581 de 2012 en Colombia.
import type { Metadata } from "next";
import { Sitio } from "@/components/Sitio";
import { CONTACTO_SITIO, NOMBRE_SITIO } from "@/lib/sitio";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

export const metadata: Metadata = {
  title: "Política de privacidad",
  description: `Qué datos recopilamos, proveedores de infraestructura (Auth0, Supabase, Resend, Vercel, pasarelas) y cómo ejercer tus derechos en ${NOMBRE_SITIO}.`,
  alternates: { canonical: "/privacidad" },
};
const CONTACTO = CONTACTO_SITIO || "el correo de soporte (pendiente de configurar)";
const TITULAR = process.env.NEXT_PUBLIC_TITULAR_LEGAL?.trim();

export default function Privacidad() {
  return (
    <Sitio>
      <div className="pagina md">
        <h1>Política de privacidad</h1>
        <p className="muted">Última actualización: 16 de noviembre de 2026</p>

        <h2>Qué datos guardamos</h2>
        <ul>
          <li><b>Cuenta y acceso:</b> tu correo y tu nombre al registrarte con Google (mediante Auth0) o con correo y contraseña (gestionados de forma cifrada por Supabase Auth; nunca guardamos tu contraseña en texto plano).</li>
          <li><b>Estudio:</b> qué lecciones marcaste como leídas, tus autoevaluaciones aprobadas y las etiquetas que pongas en los ejercicios de anotación.</li>
          <li><b>Compras:</b> el plan, el monto, la fecha, la pasarela usada y la referencia del pago. No recibimos ni guardamos los datos de tu tarjeta o cuenta bancaria: los procesa la pasarela.</li>
        </ul>

        <h2>Para qué los usamos</h2>
        <p>Para darte acceso a lo que compraste, guardar tu progreso, atender solicitudes de soporte y cumplir obligaciones contables y legales. No vendemos tus datos ni los usamos para publicidad de terceros.</p>

        <h2>Con quién se comparten</h2>
        <p>Solo con los proveedores indispensables para operar la plataforma: Auth0 (inicio de sesión con Google), Supabase (autenticación por correo y base de datos), Resend (envío de correos transaccionales de verificación y recuperación), Vercel (alojamiento web) y la pasarela de pago que elijas al comprar. Cada proveedor trata los datos conforme a su propia política de privacidad.</p>

        <h2>Cookies</h2>
        <p>Usamos una cookie de sesión para mantenerte dentro de tu cuenta y guardamos en tu navegador tu preferencia de tema claro u oscuro. No usamos cookies publicitarias.</p>

        <h2>Tus derechos</h2>
        <p>Puedes pedir conocer, corregir o eliminar tus datos, y cerrar tu cuenta, escribiendo a {CONTACTO} desde el correo registrado. Los registros de compra pueden conservarse el tiempo que exija la ley. Tratamos tus datos conforme a la Ley 1581 de 2012 de protección de datos personales de Colombia, y si consideras que no atendimos bien tu solicitud puedes acudir a la Superintendencia de Industria y Comercio.</p>

        <h2>Responsable del tratamiento</h2>
        {TITULAR ? (
          <p>Responsable del tratamiento de datos personales: {TITULAR}. Correo de atención: {CONTACTO}.</p>
        ) : (
          <p className="aviso-pendiente">
            [PENDIENTE antes de vender en producción: publicar aquí el nombre o razón social, documento/NIT y
            domicilio del responsable del tratamiento de datos personales conforme a la Ley 1581 de 2012 (Colombia)
            y normativa equivalente.]
          </p>
        )}
      </div>
    </Sitio>
  );
}
