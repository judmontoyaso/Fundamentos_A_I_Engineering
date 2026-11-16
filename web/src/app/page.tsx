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
      a: "Que programes en Python con cierta soltura y que hayas consumido alguna API. No hace falta que hayas trabajado antes con modelos de lenguaje ni con machine learning, porque eso se aprende en el primer curso.",
    },
    {
      q: `¿En qué orden conviene hacer los ${lista.length} cursos?`,
      a: `Si estás empezando con modelos de lenguaje, lo mejor es seguirlos en este orden: ${rutaOrdenada}. Si ya tienes un RAG o un agente funcionando, puedes ir directo al curso del tema que quieras reforzar.`,
    },
    {
      q: "¿Puedo entrar con Google o con correo y contraseña?",
      a: "Sí, puedes usar tu cuenta de Google o registrarte con correo y contraseña. Si algún día olvidas la contraseña, te llega un enlace al correo para crear una nueva.",
    },
    {
      q: "¿Cómo funcionan los laboratorios y las descargas .zip?",
      a: "Cada módulo trae sus scripts en Python. Los puedes leer en la página o bajar el curso completo en un .zip, que incluye las dependencias y un archivo LEEME con las instrucciones para correrlo. La muestra gratuita de cada curso también se puede descargar sin comprar nada.",
    },
    {
      q: "¿Necesito pagar una API de un proveedor de modelos?",
      a: "Para las partes que llaman a un modelo necesitas una API key de OpenAI o de otro proveedor compatible. Aun así, buena parte del material funciona sin ella, porque el curso de agentes trae un modelo simulado y varios módulos de Fundamentos corren en tu computador sin gastar tokens.",
    },
    {
      q: "¿Cómo funciona el certificado?",
      a: "Cuando terminas todas las lecciones de un curso y apruebas sus autoevaluaciones, el certificado aparece en Mi cuenta. Lleva un código único y una página pública donde cualquiera puede comprobarlo, y lo puedes descargar en PDF o agregar a LinkedIn.",
    },
    {
      q: "¿Los planes se renuevan solos? ¿Hay reembolso?",
      a: "No se renuevan. El mensual y el anual se pagan una sola vez por el tiempo que eliges, y cuando se vencen simplemente dejas de tener acceso hasta que vuelvas a comprar. Las condiciones para pedir un reembolso están en Términos y reembolsos.",
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
            <h1>Aprende a construir sistemas con LLMs que funcionen fuera del notebook</h1>
            <p className="lead">
              Son cuatro cursos en español que siguen un mismo proyecto de principio a fin, un buscador de candidatos
              para procesos de selección. Lo vas armando en Python desde tu propio computador y, a medida que avanzas,
              aprendes a evaluarlo, a mejorar lo que encuentra y a convertirlo en un agente que puedes dejar
              trabajando con tranquilidad.
            </p>
            <div className="acciones">
              <Link className="btn primary grande" href={`/leer/${primero}`}>
                Empezar con el módulo gratuito
              </Link>
              <Link className="btn grande" href="#cursos">
                Ver los cursos
              </Link>
            </div>
            <p className="hero-nota">
              El primer módulo de cada curso se puede leer gratis, sin tarjeta. En total hay {modulos} módulos y{" "}
              {quizzes} autoevaluaciones, y al terminar cada curso recibes un certificado que se puede verificar en
              línea.
            </p>
          </div>
          <Traza />
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <div className="cabecera-seccion">
            <h2>Qué trae cada módulo</h2>
            <p>
              Todos los módulos siguen el mismo recorrido. Primero lees el manual, después corres el código, luego
              resuelves los ejercicios y al final respondes una autoevaluación corta para comprobar que entendiste.
            </p>
          </div>
          <ol className="pasos-modulo">
            <li>
              <h3>Manual</h3>
              <p>Explica qué problema resuelve cada técnica, cuánto cuesta en tiempo y en dinero, y en qué casos conviene dejarla de lado. Viene con diagramas.</p>
            </li>
            <li>
              <h3>Código</h3>
              <p>Los scripts completos en Python. Puedes leerlos en la página o descargarlos y correrlos en tu computador con tu propia API key.</p>
            </li>
            <li>
              <h3>Ejercicios</h3>
              <p>Te piden modificar el sistema y medir qué cambió. Cada uno trae la solución explicada para que la compares con la tuya.</p>
            </li>
            <li>
              <h3>Autoevaluación</h3>
              <p>Unas cinco preguntas que se corrigen en el momento y explican la respuesta. Cuando las apruebas, el módulo queda terminado.</p>
            </li>
          </ol>
        </div>
      </section>

      <section className="seccion" id="cursos">
        <div className="ancho">
          <div className="cabecera-seccion">
            <h2>Los cursos</h2>
            <p>
              Los cuatro trabajan sobre el mismo sistema de reclutamiento, así que lo que construyes en uno te sirve en
              el siguiente. Si ya tienes experiencia, también puedes comprar solo el que te interese.
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
                        Leer la muestra gratuita
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
            <h2>Certificado al terminar cada curso</h2>
            <p>
              Cuando completas las lecciones de un curso y apruebas sus autoevaluaciones, tu cuenta genera un
              certificado con un código propio. Quien lo reciba, por ejemplo alguien de recursos humanos, puede abrir el
              enlace o escanear el código QR para confirmar que es auténtico. También lo puedes descargar en PDF o
              agregar a tu perfil de LinkedIn.
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
            <h2>Precios</h2>
            <p>
              Los precios aparecen en dólares como referencia. Si pagas con Mercado Pago, el cobro se hace en pesos
              colombianos y ves el valor exacto antes de confirmar. Ningún plan se renueva automáticamente, de modo que
              no vas a encontrar cobros que no esperabas.
            </p>
          </div>
          <div className="planes">
            <div className="plan">
              <h3>{PLANES.mensual.nombre}</h3>
              <p className="precio">
                {PLANES.mensual.usd} <span>USD por 30 días</span>
              </p>
              <ul>
                <li>Acceso a los {lista.length} cursos durante 30 días</li>
                <li>El código descargable y los certificados</li>
                <li>Si quieres seguir, compras otro mes</li>
              </ul>
              <Link className="btn" href="/comprar?plan=mensual">
                Comprar un mes
              </Link>
            </div>
            <div className="plan plan-destacado">
              <p className="plan-nota">Te ahorras dos meses frente al mensual</p>
              <h3>{PLANES.anual.nombre}</h3>
              <p className="precio">
                {PLANES.anual.usd} <span>USD por un año</span>
              </p>
              <ul>
                <li>Acceso a los {lista.length} cursos durante un año</li>
                <li>Los cursos nuevos que salgan en ese tiempo</li>
                <li>El código descargable y los certificados</li>
              </ul>
              <Link className="btn primary" href="/comprar?plan=anual">
                Comprar un año
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
                <li>El curso que elijas, sin fecha de vencimiento</li>
                <li>Su código y su certificado</li>
                <li>Las actualizaciones futuras de ese curso</li>
              </ul>
              <Link className="btn" href="/comprar?plan=curso">
                Elegir el curso
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
