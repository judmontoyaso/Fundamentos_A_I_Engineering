// Página pública de verificación, descarga PDF en alta definición e impresión de certificado.
import type { Metadata } from "next";
import Link from "next/link";
import QRCode from "qrcode";
import { ImprimirBtn } from "@/components/ImprimirBtn";
import { Logo } from "@/components/Logo";
import { Sitio } from "@/components/Sitio";
import { verificarCertificado } from "@/lib/certificado";
import { gruposDe } from "@/lib/contenido";

export const metadata: Metadata = { title: "Certificado verificable · IA en Producción" };
export const dynamic = "force-dynamic";

const limpio = (g: string) => g.replace(/^Módulo\s+\d+\s*[·:\-–—]\s*/i, "");

export default async function PaginaCertificado({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params;
  const cert = await verificarCertificado(decodeURIComponent(codigo));

  if (!cert) {
    return (
      <Sitio>
        <div className="pagina">
          <div className="caja">
            <h1>Certificado no válido</h1>
            <p className="muted">
              No pudimos verificar este código de certificado o el curso aún no tiene todas sus lecciones y
              autoevaluaciones completadas.
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

  const urlPublica = `https://iaenproduccion.vercel.app/certificado/${encodeURIComponent(codigo)}`;
  const qrSvg = await QRCode.toString(urlPublica, {
    type: "svg",
    margin: 1,
    width: 96,
    color: { dark: "#0f172a", light: "#ffffff" },
  });

  const linkedinUrl = `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=${encodeURIComponent(
    cert.cursoTitulo,
  )}&organizationName=${encodeURIComponent("IA en Producción")}&certUrl=${encodeURIComponent(
    urlPublica,
  )}&certId=${encodeURIComponent(cert.idVerificacion)}`;

  return (
    <Sitio>
      <div className="pagina ancha cert-wrap">
        <div className="cert-bar no-print">
          <div>
            <span className="estado ok">
              {cert.esEjemplo ? "vista previa de ejemplo" : "credencial verificada criptográficamente"}
            </span>
            <span className="aviso" style={{ marginLeft: ".6rem" }}>
              ID: <code className="ref">{cert.idVerificacion}</code>
            </span>
          </div>
          <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap", alignItems: "center" }}>
            <ImprimirBtn idCertificado={cert.idVerificacion} celebrar={!cert.esEjemplo} />
            {!cert.esEjemplo && (
              <a className="btn" href={linkedinUrl} target="_blank" rel="noopener noreferrer">
                Añadir a LinkedIn
              </a>
            )}
            <Link className="btn" href="/cuenta">Mi cuenta</Link>
          </div>
        </div>

        <article id="certificado-diploma" className="cert-hoja">
          <div className="cert-borde">
            <div className="cert-esquina tl" aria-hidden="true" />
            <div className="cert-esquina tr" aria-hidden="true" />
            <div className="cert-esquina bl" aria-hidden="true" />
            <div className="cert-esquina br" aria-hidden="true" />

            <header className="cert-cabecera">
              <div className="cert-marca">
                <Logo size={54} />
                <div>
                  <span className="cert-inst">ACADEMIA DE INGENIERÍA APLICADA</span>
                  <b>IA en Producción</b>
                  <span>Formación profesional en sistemas de IA, RAG, Evals y Agentes</span>
                </div>
              </div>

              <div className="cert-sello-box">
                <div className="cert-medalla" aria-hidden="true">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M12 2L14.8 4.5L18.5 4.2L19.6 7.8L22.5 10.2L21 13.7L22 17.3L18.5 18.8L16.5 22L12.8 21.2L9.2 22L7.2 18.8L3.7 17.3L4.7 13.7L3.2 10.2L6.1 7.8L7.2 4.2L10.9 4.5L12 2Z"
                      stroke="currentColor"
                      strokeWidth="1.6"
                    />
                    <path d="M8.5 12.2L10.9 14.6L15.8 9.7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="cert-sello">
                  <span>CREDENCIAL OFICIAL VERIFICADA</span>
                  <code>{cert.idVerificacion}</code>
                </div>
              </div>
            </header>

            <div className="cert-cuerpo">
              <p className="cert-pre">Por medio del presente diploma se certifica que</p>
              <h1 className="cert-nombre">{cert.nombre}</h1>
              <div className="cert-divisor" aria-hidden="true" />
              <p className="cert-texto">
                ha completado satisfactoriamente el <b>100 %</b> de los manuales de arquitectura, laboratorios de
                código ejecutable y las <b>{cert.quizzes} evaluaciones técnicas</b> de los{" "}
                <b>{cert.modulos} módulos</b> del programa:
              </p>
              <h2 className="cert-curso">{cert.cursoTitulo}</h2>

              <div className="cert-temas">
                {modulosLista.map((m, i) => (
                  <span key={m} className="cert-chip">
                    <b>{String(i + 1).padStart(2, "0")}</b> {m}
                  </span>
                ))}
              </div>
            </div>

            <footer className="cert-pie">
              <div className="cert-firma-bloque">
                <div className="cert-firma-trazo">IA en Producción · Dirección Académica</div>
                <div className="cert-firma-linea" />
                <span className="cert-etiqueta">Dirección Académica e Ingeniería</span>
                <b>Comité Técnico · IA en Producción</b>
              </div>

              <div className="cert-meta-bloque">
                <div>
                  <span className="cert-etiqueta">Fecha de emisión</span>
                  <b>{fechaTexto}</b>
                </div>
                <div style={{ marginTop: ".65rem" }}>
                  <span className="cert-etiqueta">Rigor académico</span>
                  <b>{cert.lecciones} unidades · {cert.quizzes} exámenes aprobados (100 %)</b>
                </div>
              </div>

              <div className="cert-qr-bloque">
                <div
                  className="cert-qr-svg"
                  dangerouslySetInnerHTML={{ __html: qrSvg }}
                  title="Escanea para verificar autenticidad"
                />
                <div>
                  <span className="cert-etiqueta">Verificación criptográfica (HMAC)</span>
                  <b style={{ display: "block", fontSize: ".8rem" }}>Escanea el QR o visita:</b>
                  <code className="ref" style={{ fontSize: ".72rem" }}>
                    iaenproduccion.vercel.app/certificado/{cert.esEjemplo ? "ejemplo" : cert.idVerificacion}
                  </code>
                </div>
              </div>
            </footer>
          </div>
        </article>
      </div>
    </Sitio>
  );
}
