// BORRADOR: debe revisarlo el titular antes de vender. Falta identificar al responsable del tratamiento
// (nombre o razón social, identificación, domicilio) como exige la Ley 1581 de 2012 en Colombia.
import type { Metadata } from "next";
import { Sitio } from "@/components/Sitio";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

export const metadata: Metadata = { title: "Privacidad" };
const CONTACTO = process.env.NEXT_PUBLIC_CONTACTO ?? "el correo de contacto del sitio";

export default function Privacidad() {
  return (
    <Sitio>
      <div className="pagina md">
        <h1>Política de privacidad</h1>
        <p className="muted">Última actualización: {new Date().getFullYear()}</p>

        <h2>Qué datos guardamos</h2>
        <ul>
          <li><b>Cuenta:</b> tu correo y tu nombre, que recibimos del servicio de inicio de sesión (Auth0). No vemos ni guardamos tu contraseña.</li>
          <li><b>Estudio:</b> qué lecciones marcaste como leídas, tus autoevaluaciones aprobadas y las etiquetas que pongas en los ejercicios de anotación.</li>
          <li><b>Compras:</b> el plan, el monto, la fecha, la pasarela usada y la referencia del pago. No recibimos ni guardamos los datos de tu tarjeta o cuenta bancaria: los procesa la pasarela.</li>
        </ul>

        <h2>Para qué los usamos</h2>
        <p>Para darte acceso a lo que compraste, guardar tu progreso, atender solicitudes de soporte y cumplir obligaciones contables y legales. No vendemos tus datos ni los usamos para publicidad de terceros.</p>

        <h2>Con quién se comparten</h2>
        <p>Solo con los proveedores que hacen funcionar el servicio: el de inicio de sesión (Auth0), el de alojamiento y base de datos, y la pasarela de pago que elijas al comprar. Cada uno trata los datos según su propia política.</p>

        <h2>Cookies</h2>
        <p>Usamos una cookie de sesión para mantenerte dentro de tu cuenta y guardamos en tu navegador tu preferencia de tema claro u oscuro. No usamos cookies publicitarias.</p>

        <h2>Tus derechos</h2>
        <p>Puedes pedir conocer, corregir o eliminar tus datos, y cerrar tu cuenta, escribiendo a {CONTACTO} desde el correo registrado. Los registros de compra pueden conservarse el tiempo que exija la ley.</p>
      </div>
    </Sitio>
  );
}
