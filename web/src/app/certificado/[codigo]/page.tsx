// Página pública de verificación e impresión de certificado.
import type { Metadata } from "next";
import Link from "next/link";
import { ImprimirBtn } from "@/components/ImprimirBtn";
import { Logo } from "@/components/Logo";
import { Sitio } from "@/components/Sitio";
import { verificarCertificado } from "@/lib/certificado";
import { gruposDe } from "@/lib/contenido";

export const metadata: Metadata = { title: "Certificado verificable" };
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
            <span className="estado ok">{cert.esEjemplo ? "vista previa de ejemplo" : "certificado verificado"}</span>
            <span className="aviso" style={{ marginLeft: ".6rem" }}>ID: <code className="ref">{cert.idVerificacion}</code></span>
          </div>
          <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
            <ImprimirBtn />
            {!cert.esEjemplo && (
              <a className="btn" href={linkedinUrl} target="_blank" rel="noopener noreferrer">
                Añadir a LinkedIn
              </a>
            )}
            <Link className="btn" href="/cuenta">Mi cuenta</Link>
          </div>
        </div>

        <article className="cert-hoja">
          <div className="cert-borde">
            <header className="cert-cabecera">
              <div className="cert-marca">
                <Logo size={42} />
                <div>
                  <b>IA en Producción</b>
                  <span>Formación técnica en ingeniería de IA</span>
                </div>
              </div>
              <div className="cert-sello">
                <span>VERIFICADO</span>
                <code>{cert.idVerificacion}</code>
              </div>
            </header>

            <div className="cert-cuerpo">
              <p className="cert-pre">Certifica que</p>
              <h1 className="cert-nombre">{cert.nombre}</h1>
              <p className="cert-texto">
                completó el 100 % de los manuales técnicos, prácticas de código y las <b>{cert.quizzes} autoevaluaciones</b> de los{" "}
                <b>{cert.modulos} módulos</b> del curso:
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
              <div>
                <span className="cert-etiqueta">Fecha de emisión</span>
                <b>{fechaTexto}</b>
              </div>
              <div>
                <span className="cert-etiqueta">Evaluación</span>
                <b>{cert.lecciones} unidades · {cert.quizzes} autoevaluaciones aprobadas</b>
              </div>
              <div>
                <span className="cert-etiqueta">Verificación pública</span>
                <code className="ref">iaenproduccion.vercel.app/certificado/{cert.esEjemplo ? "ejemplo" : "..."}</code>
              </div>
            </footer>
          </div>
        </article>
      </div>
    </Sitio>
  );
}
