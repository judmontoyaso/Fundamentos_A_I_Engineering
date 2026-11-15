// Página de venta.
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { Sitio } from "@/components/Sitio";
import { cursos, grupos, gruposDe, itemsDe } from "@/lib/contenido";
import { PLANES } from "@/lib/planes";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

const DESCRIPCION: Record<string, string> = {
  "ai-engineering":
    "De un demo a software de verdad. Construyes un buscador de hojas de vida de principio a fin: extracción validada con esquemas, embeddings, RAG híbrido, agentes con herramientas, observabilidad y guardrails.",
  evals: "¿Cómo sabes, con evidencia, si un cambio mejoró o empeoró tu sistema? Análisis de errores, etiquetado, datos sintéticos, LLM como juez calibrado y evals en CI.",
  "ai-search": "¿Qué está fallando en tu RAG y qué cambio lo arregla? Cada módulo mide primero (Recall@k, MRR, NDCG), prueba una técnica y verifica si los números se mueven.",
  agentes: "¿Cómo construyes un agente que opera sobre sistemas reales sin salirse de presupuesto ni corromper datos? Contratos poka-yoke, máquinas de estado, checkpoints, MCP, subagentes, aprobación humana y evaluación de trayectorias.",
};

const ETAPA: Record<string, string> = {
  "ai-engineering": "Etapa 1 · Construir el sistema",
  evals: "Etapa 2 · Medir con rigor",
  "ai-search": "Etapa 3 · Optimizar la recuperación",
  agentes: "Etapa 4 · Orquestar agentes en producción",
};

const ORDEN = ["ai-engineering", "evals", "ai-search", "agentes"];
const limpio = (g: string) => g.replace(/^Módulo\s+\d+\s*[·:\-–—]\s*/i, "");

export default function Inicio() {
  const lista = [...cursos].sort((a, b) => ORDEN.indexOf(a.id) - ORDEN.indexOf(b.id));
  const items = grupos.flatMap((g) => g.items);
  const modulos = cursos.reduce((n, c) => n + c.modulos, 0);
  const quizzes = items.filter((i) => i.tipo === "quiz").length;
  const primero = itemsDe("ai-engineering").find((i) => i.id.endsWith("m1-manual"))?.id ?? itemsDe(lista[0].id)[0].id;

  return (
    <Sitio>
      <section className="hero">
        <div className="ancho">
          <div className="hero-grid">
            <div>
              <span className="eyebrow">Ingeniería de IA aplicada · En español</span>
              <h1>Lleva sistemas con LLMs del notebook a producción</h1>
              <p className="lead">
                Cuatro cursos técnicos escritos para leerse despacio y ejecutarse en tu máquina. Sin relleno ni recetas
                mágicas: construyes una arquitectura real, la mides con métricas reproducibles, optimizas su recuperación,
                despliegas agentes con control de estado y obtienes un certificado verificable por cada curso.
              </p>
              <div className="acciones">
                <Link className="btn primary grande" href={`/leer/${primero}`}>Leer el primer módulo gratis</Link>
                <Link className="btn grande" href="#cursos">Explorar el temario</Link>
              </div>
            </div>

            <aside className="hero-panel" aria-label="Vista previa de arquitectura y métricas del curso">
              <div className="hero-panel-top">
                <span className="dot ok" />
                <code>traza · busquedas_cv_prod</code>
                <span className="badge-mono">p95 640 ms · $0.0018/req</span>
              </div>
              <div className="hero-steps">
                <div className="hero-step">
                  <span className="k">01 · Ingesta</span>
                  <b>Pydantic + JSON Schema</b>
                  <span className="v ok">100% válido</span>
                </div>
                <div className="hero-step">
                  <span className="k">02 · Hybrid RAG</span>
                  <b>BM25 + Embeddings + RRF</b>
                  <span className="v ok">Recall@5 0.89</span>
                </div>
                <div className="hero-step">
                  <span className="k">03 · Reranker</span>
                  <b>Cross-encoder + filtros SQL</b>
                  <span className="v ok">NDCG@5 +18%</span>
                </div>
                <div className="hero-step">
                  <span className="k">04 · Evals CI</span>
                  <b>Juez calibrado (TPR 0.94 / TNR 0.92)</b>
                  <span className="v ok">38/38 tests</span>
                </div>
              </div>
              <div className="hero-panel-foot">
                <span>Proyecto transversal en Python · Código 100 % descargable</span>
              </div>
            </aside>
          </div>

          <div className="cifras">
            <div><b>{cursos.length}</b><span>cursos completos</span></div>
            <div><b>{modulos}</b><span>módulos técnicos</span></div>
            <div><b>{quizzes}</b><span>autoevaluaciones corregidas</span></div>
            <div><b>Certificado</b><span>verificable con enlace público</span></div>
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <h2>Cómo está hecho cada módulo</h2>
          <p className="sub">No son notas sueltas ni diapositivas. Cada módulo tiene cuatro piezas que se leen en orden.</p>
          <div className="rejilla">
            <div className="tarjeta"><span className="num">01 · Manual</span><h3>El criterio de ingeniería</h3>
              <p>Qué problema resuelve cada técnica, cómo funciona por dentro, cuánto cuesta en latencia y dólares, y cuándo no usarla.</p></div>
            <div className="tarjeta"><span className="num">02 · Código</span><h3>Scripts completos en Python</h3>
              <p>El código de cada lección de principio a fin. Lo lees en la web y lo descargas para correrlo en local con tu propia API key.</p></div>
            <div className="tarjeta"><span className="num">03 · Ejercicios</span><h3>Retos con solución</h3>
              <p>Problemas que te obligan a modificar el sistema, medir el impacto y comparar alternativas. Con solución comentada.</p></div>
            <div className="tarjeta"><span className="num">04 · Autoevaluación</span><h3>Progreso y certificación</h3>
              <p>Preguntas que ponen a prueba tu diagnóstico técnico. Al completar todos los módulos y evaluaciones, desbloqueas tu certificado.</p></div>
          </div>
        </div>
      </section>

      <section className="seccion" id="cursos">
        <div className="ancho">
          <h2>Ruta completa: construir, medir y optimizar</h2>
          <p className="sub">Puedes tomar cada curso por separado o seguir la ruta completa de principio a fin.</p>
          <div className="rejilla">
            {lista.map((c, k) => (
              <div className="tarjeta" key={c.id}>
                <span className="num">{ETAPA[c.id] ?? `Curso ${k + 1}`} · {c.modulos} módulos</span>
                <h3>{c.titulo}</h3>
                <p>{DESCRIPCION[c.id] ?? ""}</p>
                <ol className="temario">
                  {gruposDe(c.id).filter((g) => g.grupo !== "Inicio").map((g, i) => (
                    <li key={g.grupo} data-n={String(i + 1).padStart(2, "0")}>{limpio(g.grupo)}</li>
                  ))}
                </ol>
                <div className="pie">
                  <Link className="btn" href={`/leer/${itemsDe(c.id)[0].id}`}>Ver la muestra gratis</Link>
                  <Link className="btn" href={`/comprar?plan=curso&curso=${c.id}`}>Comprar · {PLANES.curso.usd} USD</Link>
                </div>
              </div>
            ))}
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
                certificado con código criptográfico único, URL pública de verificación para reclutadores o empresas,
                botón para añadir a LinkedIn y versión lista para imprimir en PDF.
              </p>
              <div style={{ display: "flex", gap: ".6rem", flexWrap: "wrap" }}>
                <Link className="btn primary" href="/certificado/ejemplo">Ver certificado de ejemplo</Link>
                <Link className="btn" href="#planes">Elegir un plan</Link>
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

      <section className="seccion" id="planes">
        <div className="ancho">
          <h2>Planes</h2>
          <p className="sub">
            Precios de referencia en dólares. El cobro se hace en moneda local al cambio del día, y ves el monto exacto
            antes de pagar. Ningún plan se renueva solo.
          </p>
          <div className="rejilla">
            <div className="tarjeta plan">
              <h3>{PLANES.mensual.nombre}</h3>
              <div className="precio">{PLANES.mensual.usd} USD <small>/ 30 días</small></div>
              <ul>
                <li>Los cuatro cursos completos</li>
                <li>Código descargable y certificados verificables</li>
                <li>Renuevas solo si quieres seguir</li>
              </ul>
              <div className="pie"><Link className="btn" href="/comprar?plan=mensual">Elegir mensual</Link></div>
            </div>
            <div className="tarjeta plan destacado">
              <span className="etiqueta">Dos meses de ahorro</span>
              <h3>{PLANES.anual.nombre}</h3>
              <div className="precio">{PLANES.anual.usd} USD <small>/ año</small></div>
              <ul>
                <li>Los cuatro cursos completos</li>
                <li>Código descargable y certificados verificables</li>
                <li>Todo el contenido nuevo durante el año</li>
              </ul>
              <div className="pie"><Link className="btn primary" href="/comprar?plan=anual">Elegir anual</Link></div>
            </div>
            <div className="tarjeta plan">
              <h3>{PLANES.curso.nombre}</h3>
              <div className="precio">{PLANES.curso.usd} USD <small>/ pago único</small></div>
              <ul>
                <li>El curso que elijas, para siempre</li>
                <li>Su código descargable y certificado verificable</li>
                <li>Sus actualizaciones incluidas</li>
              </ul>
              <div className="pie"><Link className="btn" href="/comprar?plan=curso">Elegir un curso</Link></div>
            </div>
          </div>
        </div>
      </section>

      <section className="seccion faq" id="preguntas">
        <div className="ancho">
          <h2>Preguntas frecuentes</h2>
          <details><summary>¿Qué necesito saber antes de empezar?</summary>
            <p>Python a nivel intermedio y haber usado alguna API. No hace falta experiencia previa con modelos de lenguaje ni con machine learning.</p></details>
          <details><summary>¿Puedo entrar con Google o con correo y contraseña?</summary>
            <p>Sí. Puedes iniciar sesión con 1 clic usando tu cuenta de Google o crear una cuenta directa con tu correo y contraseña sin salir de la plataforma.</p></details>
          <details><summary>¿Cómo funciona el certificado?</summary>
            <p>Al marcar como completadas todas las lecciones y autoevaluaciones de un curso, aparece el botón «Ver certificado» en tu cuenta con un enlace público de verificación y opción de descarga en PDF o LinkedIn.</p></details>
          <details><summary>¿Necesito pagar una API de un proveedor de modelos?</summary>
            <p>Para correr los ejemplos con LLM sí necesitas una API key propia (OpenAI, Anthropic, Google u OpenRouter) o un modelo local con Ollama. Ese costo va aparte y cada lección indica cuánto es aproximadamente.</p></details>
          <details><summary>¿Los planes se renuevan automáticamente?</summary>
            <p>No. El plan mensual y el anual son pagos únicos por un periodo de acceso. Cuando termina, decides si renuevas.</p></details>
          <details><summary>¿Puedo pedir un reembolso?</summary>
            <p>Sí, dentro de los plazos de la <Link href="/terminos">política de reembolso</Link>.</p></details>
        </div>
      </section>
    </Sitio>
  );
}
