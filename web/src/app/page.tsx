// Página de venta principal (landing escalable a N cursos, SEO/GEO/AEO y JSON-LD).
import Image from "next/image";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { Sitio } from "@/components/Sitio";
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
      a: "Sí. Puedes iniciar sesión con 1 clic usando tu cuenta de Google o crear una cuenta directa con correo y contraseña y recuperación por email.",
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
        <div className="ancho">
          <div className="hero-grid">
            <div>
              <span className="eyebrow">Ingeniería de IA aplicada · En español</span>
              <h1>Lleva sistemas con LLMs del notebook a producción</h1>
              <p className="lead">
                Rutas de ingeniería en Python escritas para leerse despacio y ejecutarse en tu máquina. Sin relleno ni
                recetas mágicas: construyes arquitecturas reales, las mides con evaluaciones reproducibles, optimizas
                su recuperación, despliegas agentes con control de estado y obtienes un certificado verificable por
                cada curso.
              </p>
              <div className="acciones">
                <Link className="btn primary grande" href={`/leer/${primero}`}>
                  Leer el primer módulo gratis
                </Link>
                <Link className="btn grande" href="#cursos">
                  Explorar el catálogo ({lista.length} cursos)
                </Link>
              </div>
            </div>

            <aside className="hero-panel" aria-label="Vista previa de arquitectura del proyecto guía">
              <div className="hero-panel-top">
                <span className="dot ok" />
                <code>proyecto_guia · reclutamiento_rag</code>
                <span className="badge-mono">Python · Pytest · Local/API</span>
              </div>
              <div className="hero-steps">
                <div className="hero-step">
                  <span className="k">01 · Ingesta</span>
                  <b>Pydantic + JSON Schema</b>
                  <span className="v ok">Salida validada</span>
                </div>
                <div className="hero-step">
                  <span className="k">02 · Hybrid RAG</span>
                  <b>BM25 + Embeddings + RRF</b>
                  <span className="v ok">Recall@k · MRR</span>
                </div>
                <div className="hero-step">
                  <span className="k">03 · Reranker</span>
                  <b>Cross-encoder + filtros SQL</b>
                  <span className="v ok">nDCG@k medido</span>
                </div>
                <div className="hero-step">
                  <span className="k">04 · Evals CI</span>
                  <b>Juez calibrado (TPR / TNR)</b>
                  <span className="v ok">Regresiones en CI</span>
                </div>
                <div className="hero-step">
                  <span className="k">05 · Agente MCP</span>
                  <b>Checkpoints + HITL + Defensa</b>
                  <span className="v ok">pass^k verificable</span>
                </div>
              </div>
              <div className="hero-panel-foot">
                <span>Arquitectura de referencia del currículo · Infografías y código .zip descargables</span>
              </div>
            </aside>
          </div>

          <div className="cifras">
            <div>
              <b>{lista.length}</b>
              <span>cursos técnicos en el catálogo</span>
            </div>
            <div>
              <b>{modulos}</b>
              <span>módulos con infografías y código</span>
            </div>
            <div>
              <b>{quizzes}</b>
              <span>autoevaluaciones corregidas</span>
            </div>
            <div>
              <b>Certificado</b>
              <span>verificable con enlace público</span>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <h2>Cómo está hecho cada módulo</h2>
          <p className="sub">
            No son notas sueltas ni diapositivas. Cada módulo tiene cuatro piezas que se leen y ejecutan en orden.
          </p>
          <div className="rejilla">
            <div className="tarjeta">
              <span className="num">01 · Manual + Infografías</span>
              <h3>El criterio de ingeniería</h3>
              <p>
                Qué problema resuelve cada técnica, diagramas de arquitectura, cuánto cuesta en latencia y dólares, y
                cuándo conviene evitarla.
              </p>
            </div>
            <div className="tarjeta">
              <span className="num">02 · Código en Python</span>
              <h3>Laboratorios ejecutables en .zip</h3>
              <p>
                Lees el código completo en la web y descargas el paquete .zip del curso para correrlo en tu máquina,
                sin bloqueo de notebooks en la nube.
              </p>
            </div>
            <div className="tarjeta">
              <span className="num">03 · Ejercicios</span>
              <h3>Retos con solución comentada</h3>
              <p>
                Problemas que te obligan a modificar el sistema, medir el impacto con métricas reales y comparar
                alternativas.
              </p>
            </div>
            <div className="tarjeta">
              <span className="num">04 · Autoevaluación</span>
              <h3>Progreso y certificación</h3>
              <p>
                Preguntas de diagnóstico técnico para validar criterio. Al completar un curso, desbloqueas su
                certificado verificable.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion" id="cursos">
        <div className="ancho">
          <h2>Catálogo de especialización: de fundamentos a agentes en producción</h2>
          <p className="sub">
            Puedes tomar cada curso por separado o seguir la ruta progresiva completa sobre sistemas reales en Python.
          </p>
          <div className="rejilla-cursos">
            {lista.map((c, k) => {
              const primeroCurso = itemsDe(c.id)[0];
              const subgrupos = gruposDe(c.id).filter((g) => g.grupo !== "Inicio");
              return (
                <div className="tarjeta tarjeta-curso" key={c.id}>
                  {c.infografia && (
                    <Link href={`/leer/${primeroCurso.id}`} className="curso-thumb">
                      <Image
                        src={c.infografia}
                        alt={`Arquitectura del curso ${c.titulo}`}
                        width={1280}
                        height={720}
                        sizes="(max-width: 820px) 100vw, 50vw"
                        unoptimized={c.infografia.endsWith(".svg")}
                      />
                    </Link>
                  )}
                  <span className="num">
                    {c.etapa ?? `Curso ${k + 1}`} · {c.modulos} módulos
                  </span>
                  <h3>{c.titulo}</h3>
                  <p>{c.descripcion ?? ""}</p>
                  <ol className="temario">
                    {subgrupos.map((g, i) => (
                      <li key={g.grupo} data-n={String(i + 1).padStart(2, "0")}>
                        {limpio(g.grupo)}
                      </li>
                    ))}
                  </ol>
                  <div className="pie">
                    <Link className="btn primary" href={`/leer/${primeroCurso.id}`}>
                      Leer muestra gratis
                    </Link>
                    <Link className="btn" href={`/comprar?plan=curso&curso=${c.id}`}>
                      Comprar · {PLANES.curso.usdAntes && <s className="tachado">{PLANES.curso.usdAntes}</s>} {PLANES.curso.usd} USD
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="seccion" id="ruta">
        <div className="ancho">
          <h2>Resumen rápido del currículo</h2>
          <p className="sub">Comparativa directa para elegir por dónde empezar según lo que estás construyendo hoy.</p>
          <div className="table-scroll">
            <table className="ruta-tabla">
              <thead>
                <tr>
                  <th>Curso</th>
                  <th>Etapa</th>
                  <th>Módulos</th>
                  <th>Qué dominas en la práctica</th>
                  <th>Acceso gratuito</th>
                </tr>
              </thead>
              <tbody>
                {lista.map((c, k) => (
                  <tr key={c.id}>
                    <td>
                      <b>{c.titulo}</b>
                    </td>
                    <td>{c.etapa ?? `Etapa ${k + 1}`}</td>
                    <td>{c.modulos}</td>
                    <td>{c.descripcion ?? ""}</td>
                    <td>
                      <Link href={`/leer/${itemsDe(c.id)[0].id}`}>Módulo inicial</Link> ·{" "}
                      <a href={`/descargar/${c.id}?muestra=1`}>Muestra .zip</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <div className="caja cert-promo">
            <div>
              <span className="etiqueta">Incluido en todos los planes</span>
              <h2 style={{ margin: ".5rem 0 .4rem" }}>Certificado verificable al finalizar cada curso</h2>
              <p className="muted" style={{ maxWidth: "56ch", margin: "0 0 1rem" }}>
                Cuando completas el 100 % de las lecciones y autoevaluaciones de un curso, tu cuenta genera un
                certificado con código único, URL pública de verificación para reclutadores o empresas, botón para
                añadir a LinkedIn y descarga en PDF en alta definición.
              </p>
              <div style={{ display: "flex", gap: ".6rem", flexWrap: "wrap" }}>
                <Link className="btn primary" href="/certificado/ejemplo">
                  Ver certificado de ejemplo
                </Link>
                <Link className="btn" href="#planes">
                  Elegir un plan
                </Link>
              </div>
            </div>
            <div className="cert-mini">
              <div className="cert-mini-top">
                <Logo size={32} />
                <code>IAP-AGENTES-PROD2026</code>
              </div>
              <b>Agentes en producción: herramientas, estado y control</b>
              <span>9 módulos · 9 autoevaluaciones aprobadas · Verificación pública activa</span>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <div className="eeat-box">
            <span className="etiqueta">Estándar técnico y reproducibilidad</span>
            <h2 style={{ margin: 0 }}>Escrito como documentación de producción, no como diapositivas</h2>
            <p className="muted" style={{ margin: 0, maxWidth: "70ch" }}>
              Cada módulo separa fundamentos, código ejecutable, ejercicios con solución y autoevaluación de criterio.
              Los paquetes descargables incluyen datos sintéticos y modos deterministas locales para verificar flujos,
              pruebas automatizadas (`pytest`) y contratos antes de gastar presupuesto en llamadas reales a modelos.
            </p>
            <div className="eeat-meta">
              {AUTOR_PUBLICO && (
                <span>
                  Autoría y curaduría técnica: <b>{AUTOR_PUBLICO}</b>
                </span>
              )}
              <span>Actualización continua del catálogo</span>
              <span>Código fuente Python descargable por curso</span>
              <span>
                <Link href="/llms.txt">Índice técnico llms.txt</Link>
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion" id="planes">
        <div className="ancho">
          <h2>Planes</h2>
          <p className="sub">
            Precios de referencia en dólares. Con Mercado Pago el cobro se hace en pesos colombianos y ves el total
            exacto antes de pagar. Ningún plan se renueva solo.
          </p>
          <div className="rejilla">
            <div className="tarjeta plan">
              <h3>{PLANES.mensual.nombre}</h3>
              <div className="precio">
                {PLANES.mensual.usd} USD <small>/ 30 días</small>
              </div>
              <ul>
                <li>
                  Acceso completo a los {lista.length} cursos ({modulos} módulos)
                </li>
                <li>Código descargable (.zip), infografías y certificados verificables</li>
                <li>Renuevas solo si quieres continuar</li>
              </ul>
              <div className="pie">
                <Link className="btn" href="/comprar?plan=mensual">
                  Elegir mensual
                </Link>
              </div>
            </div>
            <div className="tarjeta plan destacado">
              <span className="etiqueta">Dos meses de ahorro</span>
              <h3>{PLANES.anual.nombre}</h3>
              <div className="precio">
                {PLANES.anual.usd} USD <small>/ año</small>
              </div>
              <ul>
                <li>
                  Todo el catálogo actual ({lista.length} cursos, {modulos} módulos)
                </li>
                <li>Acceso automático a nuevos cursos y actualizaciones durante el año</li>
                <li>Código descargable (.zip), infografías y certificados verificables</li>
              </ul>
              <div className="pie">
                <Link className="btn primary" href="/comprar?plan=anual">
                  Elegir anual
                </Link>
              </div>
            </div>
            <div className="tarjeta plan">
              {PLANES.curso.usdAntes && <span className="etiqueta">Promoción de lanzamiento</span>}
              <h3>{PLANES.curso.nombre}</h3>
              <div className="precio">
                {PLANES.curso.usdAntes && <s className="tachado">{PLANES.curso.usdAntes}</s>} {PLANES.curso.usd} USD <small>/ pago único</small>
              </div>
              <ul>
                <li>El curso que elijas, sin fecha de vencimiento</li>
                <li>Su paquete .zip descargable y certificado verificable</li>
                <li>Actualizaciones de ese curso incluidas</li>
              </ul>
              <div className="pie">
                <Link className="btn" href="/comprar?plan=curso">
                  Elegir un curso
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion faq" id="preguntas">
        <div className="ancho">
          <h2>Preguntas frecuentes</h2>
          {faqs.map((f) => (
            <details key={f.q}>
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </section>
    </Sitio>
  );
}
