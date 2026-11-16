// Página de venta principal (landing escalable a N cursos, SEO/GEO/AEO y JSON-LD).
import Image from "next/image";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { Sitio } from "@/components/Sitio";
import { Preguntas } from "@/components/Preguntas";
import { Traza } from "@/components/Traza";
import { cursos, grupos, gruposDe, itemsDe } from "@/lib/contenido";
import { PLANES } from "@/lib/planes";
import { NOMBRE_SITIO, urlSitioPublico } from "@/lib/sitio";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

const AUTOR_PUBLICO = process.env.NEXT_PUBLIC_AUTOR?.trim();
const limpio = (g: string) => g.replace(/^Módulo\s+\d+\s*[·:\-–—]\s*/i, "");

export default function Inicio() {
  const lista = [...cursos].sort((a, b) => (a.orden ?? 99) - (b.orden ?? 99));
  const items = grupos.flatMap((g) => g.items);
  const modulos = lista.reduce((n, c) => n + c.modulos, 0);
  const quizzes = items.filter((i) => i.tipo === "quiz").length;
  const primero =
    itemsDe(lista[0].id).find((i) => i.id.endsWith("m1-manual"))?.id ?? itemsDe(lista[0].id)[0].id;

  const rutaOrdenada = lista.map((c, idx) => `${idx + 1}) ${c.titulo}`).join(", ");
  const faqs = [
    {
      q: "¿Qué necesito saber antes de empezar?",
      a: "Python a nivel intermedio y haber usado alguna API REST. No hace falta experiencia previa con modelos de lenguaje ni con machine learning.",
    },
    {
      q: `¿En qué orden conviene hacer los ${lista.length} cursos?`,
      a: `Si empiezas desde cero con LLMs en producción, te conviene seguir la secuencia recomendada del catálogo: ${rutaOrdenada}. Si ya tienes un sistema RAG o agente operando, puedes entrar directo al curso del área que necesitas reforzar.`,
    },
    {
      q: "¿Puedo entrar con Google o con correo y contraseña?",
      a: "Sí. Puedes entrar con tu cuenta de Google o crear una cuenta con correo y contraseña. Si olvidas la contraseña, la recuperas por correo.",
    },
    {
      q: "¿Cómo funcionan los laboratorios y las descargas .zip?",
      a: "Cada módulo incluye scripts completos en Python listos para leer en la web y descargar en un paquete .zip por curso (con sus dependencias y archivo LEEME.txt). Puedes descargar una muestra gratis del primer módulo de cada curso sin comprar.",
    },
    {
      q: "¿Necesito pagar una API de un proveedor de modelos?",
      a: "El código con llamadas a LLMs usa OpenAI (OPENAI_API_KEY) o cualquier API compatible mediante OPENAI_BASE_URL. Además, el curso de Agentes en producción incluye un modelo simulado determinista y varios módulos de Fundamentos corren en local con costo cero de tokens.",
    },
    {
      q: "¿Cómo funciona el certificado?",
      a: "Al aprobar todas las autoevaluaciones y completar las lecciones de un curso, tu cuenta habilita un certificado verificable con código único, enlace público y descarga en PDF lista para LinkedIn.",
    },
    {
      q: "¿Los planes se renuevan automáticamente o tienen reembolso?",
      a: "Ningún plan se renueva solo: el mensual (30 días) y el anual (365 días) son pagos únicos por periodo. También puedes solicitar reembolso dentro de los plazos publicados en Términos y reembolsos.",
    },
  ];

  const baseUrl = urlSitioPublico().replace(/\/+$/, "");
  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "EducationalOrganization",
        "@id": `${baseUrl}/#org`,
        name: NOMBRE_SITIO,
        url: baseUrl,
        description:
          "Plataforma de formación técnica en español sobre ingeniería de sistemas con LLMs en producción: arquitectura RAG, evaluaciones automatizadas, búsqueda híbrida y agentes con control de estado.",
      },
      {
        "@type": "WebSite",
        "@id": `${baseUrl}/#website`,
        url: baseUrl,
        name: NOMBRE_SITIO,
        inLanguage: "es",
        publisher: { "@id": `${baseUrl}/#org` },
      },
      {
        "@type": "ItemList",
        "@id": `${baseUrl}/#catalogo`,
        name: "Catálogo de cursos de IA en Producción",
        numberOfItems: lista.length,
        itemListElement: lista.map((c, idx) => {
          const muestra = itemsDe(c.id)[0];
          return {
            "@type": "ListItem",
            position: idx + 1,
            item: {
              "@type": "Course",
              name: c.titulo,
              description: c.descripcion ?? c.etapa ?? `Curso técnico de ${c.modulos} módulos en Python.`,
              url: `${baseUrl}/leer/${muestra.id}`,
              inLanguage: "es",
              provider: { "@id": `${baseUrl}/#org` },
              offers: {
                "@type": "Offer",
                category: "Pago único por curso",
                price: String(PLANES.curso.usd),
                priceCurrency: "USD",
                availability: "https://schema.org/InStock",
                url: `${baseUrl}/comprar?plan=curso&curso=${c.id}`,
              },
            },
          };
        }),
      },
      {
        "@type": "FAQPage",
        mainEntity: faqs.map((f) => ({
          "@type": "Question",
          name: f.q,
          acceptedAnswer: {
            "@type": "Answer",
            text: f.a,
          },
        })),
      },
    ],
  };

  return (
    <Sitio>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />

      <section className="hero">
        <div className="ancho hero-grid">
          <div className="hero-texto">
            <h1>Lleva sistemas con LLMs del notebook a producción</h1>
            <p className="lead">
              Cursos de ingeniería de IA en español, escritos para leerse con calma y ejecutarse en tu máquina. Cada
              técnica llega con su código en Python, su costo en tokens y dólares, y una forma de medir si funcionó.
            </p>
            <div className="acciones">
              <Link className="btn primary grande" href={`/leer/${primero}`}>
                Leer el primer módulo gratis
              </Link>
              <Link className="btn grande" href="#cursos">
                Ver los {lista.length} cursos
              </Link>
            </div>
            <p className="hero-nota">
              {lista.length} cursos, {modulos} módulos y {quizzes} autoevaluaciones. Certificado verificable al terminar
              cada curso.
            </p>
          </div>
          <Traza />
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <div className="cabecera-seccion">
            <h2>Cómo se estudia un módulo</h2>
            <p>
              Cuatro partes, en este orden. Nada de diapositivas: documentación que explica el porqué, código que puedes
              romper y preguntas que miden el criterio, no la memoria.
            </p>
          </div>
          <ol className="pasos-modulo">
            <li>
              <h3>Manual</h3>
              <p>Qué problema resuelve cada técnica, cuánto cuesta en latencia y dólares, y cuándo no usarla. Con diagramas.</p>
            </li>
            <li>
              <h3>Código</h3>
              <p>Los scripts completos, para leer en la web y descargar en un .zip que corre en tu máquina con tu API key.</p>
            </li>
            <li>
              <h3>Ejercicios</h3>
              <p>Cambios al sistema que te obligan a medir el impacto y comparar alternativas. Con la solución comentada.</p>
            </li>
            <li>
              <h3>Autoevaluación</h3>
              <p>Preguntas de diagnóstico que se corrigen al momento y explican por qué. Aprobarlas cuenta para el certificado.</p>
            </li>
          </ol>
        </div>
      </section>

      <section className="seccion" id="cursos">
        <div className="ancho">
          <div className="cabecera-seccion">
            <h2>La ruta, en cuatro cursos</h2>
            <p>
              Sobre el mismo sistema de reclutamiento: primero lo construyes, después aprendes a medirlo, luego mejoras
              su búsqueda y al final lo conviertes en un agente que opera con control. Cada curso se puede tomar solo.
            </p>
          </div>
          <ol className="ruta">
            {lista.map((c, k) => {
              const primeroCurso = itemsDe(c.id)[0];
              const subgrupos = gruposDe(c.id).filter((g) => g.grupo !== "Inicio");
              return (
                <li className="ruta-curso" key={c.id}>
                  <div className="ruta-marca" aria-hidden="true">{k + 1}</div>
                  <div className="ruta-cuerpo">
                    <p className="ruta-etapa">{(c.etapa ?? `Etapa ${k + 1}`).replace(/^Etapa \d+\s*·\s*/, "")}</p>
                    <h3>{c.titulo}</h3>
                    <p className="ruta-desc">{c.descripcion ?? ""}</p>
                    <details className="ruta-temario">
                      <summary>Ver los {c.modulos} módulos</summary>
                      <ol>
                        {subgrupos.map((g) => (
                          <li key={g.grupo}>{limpio(g.grupo)}</li>
                        ))}
                      </ol>
                    </details>
                    <div className="ruta-acciones">
                      <Link className="btn primary" href={`/leer/${primeroCurso.id}`}>
                        Leer la muestra gratis
                      </Link>
                      <Link className="btn" href={`/comprar?plan=curso&curso=${c.id}`}>
                        Comprar por {PLANES.curso.usd} USD
                        {PLANES.curso.usdAntes && <s className="tachado"> {PLANES.curso.usdAntes}</s>}
                      </Link>
                    </div>
                  </div>
                  {c.infografia && (
                    <Link href={`/leer/${primeroCurso.id}`} className="ruta-imagen" tabIndex={-1} aria-hidden="true">
                      <Image
                        src={c.infografia}
                        alt=""
                        width={1280}
                        height={720}
                        sizes="(max-width: 860px) 100vw, 40vw"
                        unoptimized={c.infografia.endsWith(".svg")}
                      />
                    </Link>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      <section className="seccion seccion-cert">
        <div className="ancho cert-promo">
          <div>
            <h2>Un certificado que cualquiera puede comprobar</h2>
            <p>
              Al terminar las lecciones y aprobar las autoevaluaciones de un curso, tu cuenta genera un certificado con
              código único y una página pública de verificación. Lo descargas en PDF o lo añades a LinkedIn.
            </p>
            <Link className="btn" href="/certificado/ejemplo">
              Ver un certificado de ejemplo
            </Link>
          </div>
          <Link href="/certificado/ejemplo" className="cert-mini" aria-label="Certificado de ejemplo">
            <span className="cert-mini-sello"><Logo size={30} /></span>
            <span className="cert-mini-pre">Se certifica que</span>
            <b className="cert-mini-nombre">Tu nombre</b>
            <span className="cert-mini-texto">completó el curso</span>
            <b className="cert-mini-curso">Agentes en producción: herramientas, estado y control</b>
            <code className="cert-mini-codigo">IAP-AGENTES-7F3A91C2</code>
          </Link>
        </div>
      </section>

      <section className="seccion" id="planes">
        <div className="ancho">
          <div className="cabecera-seccion">
            <h2>Planes</h2>
            <p>
              Precios en dólares. Con Mercado Pago pagas en pesos colombianos y ves el total exacto antes de confirmar.
              Ningún plan se renueva solo.
            </p>
          </div>
          <div className="planes">
            <div className="plan">
              <h3>{PLANES.mensual.nombre}</h3>
              <p className="precio">
                {PLANES.mensual.usd} <span>USD por 30 días</span>
              </p>
              <ul>
                <li>Los {lista.length} cursos completos</li>
                <li>Código descargable y certificados</li>
                <li>Renuevas solo si quieres seguir</li>
              </ul>
              <Link className="btn" href="/comprar?plan=mensual">
                Elegir mensual
              </Link>
            </div>
            <div className="plan plan-destacado">
              <p className="plan-nota">Dos meses gratis frente al mensual</p>
              <h3>{PLANES.anual.nombre}</h3>
              <p className="precio">
                {PLANES.anual.usd} <span>USD por un año</span>
              </p>
              <ul>
                <li>Los {lista.length} cursos y los que se publiquen en el año</li>
                <li>Actualizaciones de todo el contenido</li>
                <li>Código descargable y certificados</li>
              </ul>
              <Link className="btn primary" href="/comprar?plan=anual">
                Elegir anual
              </Link>
            </div>
            <div className="plan">
              {PLANES.curso.usdAntes && <p className="plan-nota plan-promo">Precio de lanzamiento</p>}
              <h3>{PLANES.curso.nombre}</h3>
              <p className="precio">
                {PLANES.curso.usd} <span>USD, pago único</span>
                {PLANES.curso.usdAntes && <s className="tachado">{PLANES.curso.usdAntes} USD</s>}
              </p>
              <ul>
                <li>El curso que elijas, sin vencimiento</li>
                <li>Su código descargable y su certificado</li>
                <li>Las actualizaciones de ese curso</li>
              </ul>
              <Link className="btn" href="/comprar?plan=curso">
                Elegir un curso
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion" id="preguntas">
        <div className="ancho faq">
          <h2>Preguntas frecuentes</h2>
          <div>
            <Preguntas items={faqs} />
            {AUTOR_PUBLICO && <p className="faq-autor">Contenido escrito y revisado por {AUTOR_PUBLICO}.</p>}
          </div>
        </div>
      </section>
    </Sitio>
  );
}
