// Página pública de verificación, descarga PDF en alta definición e impresión de certificado.
import type { Metadata } from "next";
import { NOMBRE_SITIO, urlSitioPublico } from "@/lib/sitio";
import { BadgeCheck } from "lucide-react";
import Link from "next/link";
import QRCode from "qrcode";
import { CertEscala } from "@/components/CertEscala";
import { ImprimirBtn } from "@/components/ImprimirBtn";
import { Logo } from "@/components/Logo";
import { Sitio } from "@/components/Sitio";
import { verificarCertificado } from "@/lib/certificado";
import { gruposDe, itemsDe } from "@/lib/contenido";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ codigo: string }>;
}): Promise<Metadata> {
  const { codigo } = await params;
  const esEjemplo = codigo === "ejemplo";
  const ruta = `/certificado/${encodeURIComponent(codigo)}`;
  const titulo = esEjemplo
    ? "Ejemplo de certificado verificable"
    : "Certificado verificable de finalización";
  const descripcion =
    "Página pública para comprobar un certificado de finalización de curso de IA en Producción.";
  return {
    title: titulo,
    description: descripcion,
    alternates: { canonical: ruta },
    openGraph: {
      title: `${titulo} · ${NOMBRE_SITIO}`,
      description: descripcion,
      url: ruta,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: `${titulo} · ${NOMBRE_SITIO}`,
      description: descripcion,
    },
    robots: { index: esEjemplo, follow: true },
  };
}
export const dynamic = "force-dynamic";

const FIRMA = process.env.NEXT_PUBLIC_AUTOR?.trim() || NOMBRE_SITIO;
const limpio = (g: string) => g.replace(/^Módulo\s+\d+\s*[·:\-–—]\s*/i, "");

export default async function PaginaCertificado({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params;
  const cert = await verificarCertificado(decodeURIComponent(codigo));

  if (!cert) {
    return (
      <Sitio>
        <div className="pagina">
          <div className="caja">
            <h1>Este certificado no es válido</h1>
            <p className="muted">
              El código no corresponde a ningún certificado emitido, o la cuenta todavía no ha completado todas las
              unidades y autoevaluaciones del curso. Revisa que el enlace esté completo.
            </p>
            <p style={{ marginTop: "1rem" }}>
              <Link className="btn primary" href="/">Ir al inicio</Link>
            </p>
          </div>
        </div>
      </Sitio>
    );
  }

  const fechaTexto = new Date(`${cert.fecha}T12:00:00Z`).toLocaleDateString("es-CO", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const modulosLista = gruposDe(cert.cursoId)
    .filter((g) => g.grupo !== "Inicio")
    .map((g) => limpio(g.grupo));

  const baseUrl = urlSitioPublico().replace(/\/+$/, "");
  const ruta = `/certificado/${cert.esEjemplo ? "ejemplo" : cert.idVerificacion}`;
  const urlPublica = `${baseUrl}${ruta}`;
  const qrSvg = await QRCode.toString(urlPublica, {
    type: "svg",
    margin: 0,
    width: 96,
    color: { dark: "#14201c", light: "#00000000" },
  });

  const linkedinUrl = `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=${encodeURIComponent(
    cert.cursoTitulo,
  )}&organizationName=${encodeURIComponent(NOMBRE_SITIO)}&issueYear=${cert.fecha.slice(0, 4)}&issueMonth=${Number(
    cert.fecha.slice(5, 7),
  )}&certUrl=${encodeURIComponent(urlPublica)}&certId=${encodeURIComponent(cert.idVerificacion)}`;

  return (
    <Sitio>
      <div className="pagina ancha cert-wrap">
        <section className="cert-estado no-print" aria-label="Resultado de la verificación">
          <div className="cert-estado-texto">
            <p className={cert.esEjemplo ? "cert-veredicto ejemplo" : "cert-veredicto"}>
              <BadgeCheck size={20} aria-hidden />
              {cert.esEjemplo ? "Certificado de ejemplo" : "Certificado válido"}
            </p>
            <p className="cert-resumen">
              {cert.esEjemplo
                ? "Así se ve el certificado que recibes al terminar un curso. Los reales llevan el nombre de quien lo completó y un código único."
                : `${cert.nombre} completó el curso ${cert.cursoTitulo} de ${NOMBRE_SITIO} el ${fechaTexto}.`}
            </p>
          </div>
          <div className="cert-acciones">
            <ImprimirBtn idCertificado={cert.idVerificacion} celebrar={!cert.esEjemplo} url={urlPublica} />
            {!cert.esEjemplo && (
              <a className="btn" href={linkedinUrl} target="_blank" rel="noopener noreferrer">
                Añadir a LinkedIn
              </a>
            )}
          </div>
        </section>

        <CertEscala>
          <article id="certificado-diploma" className="cert-hoja" aria-label={`Certificado de ${cert.nombre}`}>
            <div className="cert-marco">
              <header className="cert-cabecera">
                <div className="cert-marca">
                  <Logo size={46} />
                  <div>
                    <b>{NOMBRE_SITIO}</b>
                    <span>Formación profesional en IA</span>
                  </div>
                </div>
                <p className="cert-numero">
                  Certificado n.º
                  <code>{cert.idVerificacion}</code>
                </p>
              </header>

              <div className="cert-cuerpo">
                <p className="cert-tipo">Certificado de finalización</p>
                <p className="cert-otorgado">otorgado a</p>
                <h1 className="cert-nombre">{cert.nombre}</h1>
                <p className="cert-por">por completar el curso</p>
                <h2 className="cert-curso">{cert.cursoTitulo}</h2>
                <p className="cert-detalle">
                  {cert.modulos} módulos, {cert.lecciones} unidades de estudio y {cert.quizzes} autoevaluaciones aprobadas
                </p>
              </div>

              <footer className="cert-pie">
                <div className="cert-firma">
                  <span className="cert-firma-trazo">{FIRMA}</span>
                  <span className="cert-linea" />
                  <span className="cert-pie-etq">Dirección académica, {NOMBRE_SITIO}</span>
                </div>

                <div className="cert-sello" aria-hidden="true">
                  <svg viewBox="0 0 120 120" width="112" height="112">
                    <defs>
                      <path id="cert-arco" d="M60,60 m-44,0 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0" />
                    </defs>
                    <circle cx="60" cy="60" r="57" fill="none" stroke="#0f5f52" strokeWidth="1.5" />
                    <circle cx="60" cy="60" r="33" fill="none" stroke="#0f5f52" strokeWidth="1" />
                    <text fontSize="9" fill="#0f5f52" fontFamily="IBM Plex Sans, sans-serif" fontWeight="600">
                      <textPath href="#cert-arco" textLength="268" lengthAdjust="spacing">IA EN PRODUCCIÓN · CERTIFICADO VERIFICABLE ·</textPath>
                    </text>
                    <path d="M47 61 l9 9 l18 -19" fill="none" stroke="#0f5f52" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>

                <div className="cert-fecha">
                  <span className="cert-fecha-valor">{fechaTexto}</span>
                  <span className="cert-linea" />
                  <span className="cert-pie-etq">Fecha de expedición</span>
                </div>

                <div className="cert-verifica">
                  <div className="cert-qr" dangerouslySetInnerHTML={{ __html: qrSvg }} />
                  <div>
                    <span className="cert-pie-etq">Verifica este certificado en</span>
                    <span className="cert-dominio">{baseUrl.replace(/^https?:\/\//, "")}/certificado/</span>
                    <code>{cert.esEjemplo ? "ejemplo" : cert.idVerificacion}</code>
                  </div>
                </div>
              </footer>
            </div>
          </article>
        </CertEscala>

        <section className="cert-info">
          <div>
            <h2>Qué cubre este curso</h2>
            <ol className="cert-modulos">
              {modulosLista.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ol>
          </div>
          <div>
            <h2>Cómo se comprueba</h2>
            <p>
              Esta página se genera en el momento a partir del progreso real de la cuenta en {NOMBRE_SITIO}. Si la
              cuenta no hubiera completado todas las unidades y autoevaluaciones del curso, aquí aparecería que el
              certificado no es válido.
            </p>
            <p>
              El código <code>{cert.idVerificacion}</code> identifica a esta persona y este curso, y no se puede generar
              sin acceso al servidor.
            </p>
            {cert.esEjemplo ? (
              <Link className="btn primary" href="/#planes">Ver planes</Link>
            ) : (
              <Link className="btn" href={`/leer/${itemsDe(cert.cursoId)[0]?.id ?? ""}`}>Ver el curso</Link>
            )}
          </div>
        </section>
      </div>
    </Sitio>
  );
}
