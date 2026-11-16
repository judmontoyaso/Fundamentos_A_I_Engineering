// Correos transaccionales (verificación de cuenta, recuperación de clave, confirmación de compra) por Resend.
// Sin RESEND_API_KEY y CORREO_REMITENTE no se envía nada: la app funciona igual, sin avisos por correo.
import "server-only";
import { CONTACTO_SITIO, NOMBRE_SITIO, urlSitioPublico } from "./sitio";
import type { Pedido } from "./tipos";

const CLAVE = process.env.RESEND_API_KEY;
const REMITENTE = process.env.CORREO_REMITENTE; // p. ej. IA en Producción <hola@tudominio.com>
const SITIO = NOMBRE_SITIO;

export const correoActivo = Boolean(CLAVE && REMITENTE);

/** URL pública del sitio para los enlaces de los correos que no nacen de una petición (p. ej. un webhook). */
export function urlSitio(): string {
  const u = urlSitioPublico();
  return u.startsWith("http://localhost") ? "" : u;
}

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

type Mensaje = { para: string; asunto: string; texto: string; html: string };

/** Envía un correo. Nunca lanza: un aviso que no sale no debe tumbar un registro ni un pago. */
export async function enviarCorreo(m: Mensaje): Promise<boolean> {
  if (!correoActivo) return false;
  try {
    const body: Record<string, unknown> = {
      from: REMITENTE,
      to: [m.para],
      subject: m.asunto,
      text: m.texto,
      html: m.html,
    };
    if (CONTACTO_SITIO) body.reply_to = CONTACTO_SITIO;
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${CLAVE}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) console.error(`[correo] ${r.status}: ${(await r.text()).slice(0, 300)}`);
    return r.ok;
  } catch (e) {
    console.error("[correo]", e);
    return false;
  }
}

function plantilla(titulo: string, parrafos: string[], boton?: { texto: string; url: string }): string {
  const cuerpo = parrafos.map((p) => `<p style="margin:0 0 14px;line-height:1.55">${p}</p>`).join("");
  const cta = boton
    ? `<p style="margin:22px 0"><a href="${esc(boton.url)}" style="background:#111827;color:#fff;text-decoration:none;padding:11px 18px;border-radius:8px;display:inline-block">${esc(boton.texto)}</a></p>
       <p style="margin:0 0 14px;font-size:13px;color:#6b7280">Si el botón no abre, copia este enlace: ${esc(boton.url)}</p>`
    : "";
  return `<div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#111827">
    <h1 style="font-size:20px;margin:0 0 16px">${esc(titulo)}</h1>${cuerpo}${cta}
    <p style="margin:24px 0 0;font-size:13px;color:#6b7280">${esc(SITIO)}${CONTACTO_SITIO ? ` · ${esc(CONTACTO_SITIO)}` : ""}</p></div>`;
}

export function enviarVerificacion(para: string, nombre: string | undefined, enlace: string): Promise<boolean> {
  const saludo = nombre ? `Hola, ${nombre}.` : "Hola.";
  return enviarCorreo({
    para,
    asunto: `Confirma tu correo en ${SITIO}`,
    texto: `${saludo}\n\nConfirma que este correo es tuyo abriendo este enlace (vale 48 horas):\n${enlace}\n\nSi no creaste una cuenta en ${SITIO}, ignora este mensaje: sin tu confirmación la cuenta queda sin verificar.`,
    html: plantilla("Confirma tu correo", [
      esc(saludo),
      "Confirma que este correo es tuyo. El enlace vale 48 horas.",
      `Si no creaste una cuenta en ${esc(SITIO)}, ignora este mensaje: sin tu confirmación la cuenta queda sin verificar.`,
    ], { texto: "Confirmar mi correo", url: enlace }),
  });
}

export function enviarRecuperacion(para: string, nombre: string | undefined, enlace: string): Promise<boolean> {
  const saludo = nombre ? `Hola, ${nombre}.` : "Hola.";
  return enviarCorreo({
    para,
    asunto: `Restablece tu contraseña en ${SITIO}`,
    texto: `${saludo}\n\nRecibimos una solicitud para cambiar la contraseña de tu cuenta.\nAbre este enlace (vale 1 hora):\n${enlace}\n\nSi no pediste cambiar tu contraseña, ignora este mensaje.`,
    html: plantilla("Restablece tu contraseña", [
      esc(saludo),
      "Recibimos una solicitud para asignar una nueva contraseña a tu cuenta. Este enlace vale 1 hora.",
      "Si no fuiste tú, puedes ignorar este mensaje con tranquilidad.",
    ], { texto: "Elegir nueva contraseña", url: enlace }),
  });
}

export function enviarConfirmacionCompra(pedido: Pedido, descripcion: string, hasta: string | null): Promise<boolean> {
  const base = urlSitio();
  const vigencia = hasta
    ? `Tu acceso está activo hasta el ${new Date(hasta).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric" })}. No se renueva solo.`
    : "Tu acceso no tiene fecha de vencimiento.";
  const monto = `${pedido.monto.toLocaleString("es-CO")} ${pedido.moneda}`;
  return enviarCorreo({
    para: pedido.email,
    asunto: `Tu compra en ${SITIO}: ${descripcion}`,
    texto: `Recibimos tu pago de ${monto} por ${descripcion}.\n${vigencia}\nReferencia del pedido: ${pedido.id}\n${base ? `\nEntra a tu cuenta: ${base}/cuenta\n` : ""}`,
    html: plantilla("Pago recibido", [
      `Recibimos tu pago de <b>${esc(monto)}</b> por <b>${esc(descripcion)}</b>.`,
      esc(vigencia),
      `Referencia del pedido: <code>${esc(pedido.id)}</code>`,
    ], base ? { texto: "Ir a mi cuenta", url: `${base}/cuenta` } : undefined),
  });
}
