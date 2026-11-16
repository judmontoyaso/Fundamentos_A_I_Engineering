// BORRADOR: texto base para arrancar. Debe revisarlo el titular (y, si es posible, un abogado) antes de vender:
// faltan la razón social o nombre del vendedor, su identificación y la ley aplicable exacta.
import type { Metadata } from "next";
import { Sitio } from "@/components/Sitio";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

import { CONTACTO_SITIO, NOMBRE_SITIO } from "@/lib/sitio";

export const metadata: Metadata = {
  title: "Términos y reembolsos",
  description: `Condiciones de compra, licencias de uso individual, garantía de reembolso y datos del titular en ${NOMBRE_SITIO}.`,
  alternates: { canonical: "/terminos" },
};
const CONTACTO = CONTACTO_SITIO || "el correo de soporte (pendiente de configurar)";
const TITULAR = process.env.NEXT_PUBLIC_TITULAR_LEGAL?.trim();

export default function Terminos() {
  return (
    <Sitio>
      <div className="pagina md">
        <h1>Términos de uso y política de reembolso</h1>
        <p className="muted">Última actualización: 16 de noviembre de 2026</p>

        <h2>Qué compras</h2>
        <p>Acceso personal en línea a los cursos de este sitio: lecciones, ejercicios, autoevaluaciones y el código descargable. El plan mensual da acceso por 30 días, el anual por 365 días, y la compra de un curso da acceso a ese curso sin fecha de vencimiento mientras el sitio esté en funcionamiento.</p>

        <h2>Renovación</h2>
        <p>Ningún plan se renueva ni se cobra de forma automática. Cuando tu periodo termina, el acceso de pago se cierra y puedes comprar un nuevo periodo si quieres continuar. Tu progreso se conserva.</p>

        <h2>Uso permitido</h2>
        <p>La cuenta es personal e intransferible. Puedes usar el código en tus propios proyectos, incluidos los comerciales. No puedes revender, redistribuir ni publicar las lecciones o el paquete de código como material de formación.</p>

        <h2>Costos de terceros</h2>
        <p>Los ejemplos que llaman a modelos de lenguaje se ejecutan con tu propia cuenta del proveedor que elijas. Esos costos no están incluidos y no los controlamos.</p>

        <h2>Reembolsos</h2>
        <p>Puedes pedir el reembolso completo dentro de los 7 días siguientes a la compra escribiendo a {CONTACTO} desde el correo de tu cuenta. Al reembolsar se retira el acceso asociado a ese pago. Pasado ese plazo no hay reembolsos parciales por tiempo no usado. Esta política no limita los derechos que te da la ley. En Colombia aplica el Estatuto del Consumidor (Ley 1480 de 2011), incluido el derecho de retracto en compras por internet, y si compras desde otro país conservas los derechos que te reconozca su legislación.</p>

        <h2>Contenido y garantías</h2>
        <p>El material es educativo. Los proveedores, modelos, precios y librerías cambian con frecuencia: actualizamos el contenido, pero no garantizamos que cada ejemplo funcione sin ajustes con versiones futuras de herramientas de terceros.</p>

        <h2>Contacto</h2>
        <p>Dudas sobre tu compra o tu cuenta: {CONTACTO}.</p>

        <h2>Titular del servicio</h2>
        {TITULAR ? (
          <p>Responsable comercial y legal: {TITULAR}. Contacto: {CONTACTO}.</p>
        ) : (
          <p className="aviso-pendiente">
            [PENDIENTE antes de vender en producción: publicar aquí el nombre completo o razón social del titular,
            NIT o documento de identificación, domicilio y jurisdicción aplicable conforme a la normativa del país.]
          </p>
        )}
      </div>
    </Sitio>
  );
}
