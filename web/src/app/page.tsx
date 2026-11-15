// Página de venta.
import Link from "next/link";
import { Sitio } from "@/components/Sitio";
import { cursos, grupos, gruposDe, itemsDe } from "@/lib/contenido";
import { PLANES } from "@/lib/planes";

export const dynamic = "force-dynamic"; // la cabecera depende de la sesión

const DESCRIPCION: Record<string, string> = {
  "ai-engineering":
    "De un demo a software de verdad. Construyes un buscador de hojas de vida: extracción validada, embeddings, RAG híbrido, agentes, observabilidad y guardrails.",
  evals: "¿Cómo sabes, con evidencia, si un cambio mejoró o empeoró tu sistema? Análisis de errores, datos sintéticos, LLM como juez y evals en CI.",
  "ai-search": "¿Qué está fallando en tu RAG y qué cambio lo arregla? Cada módulo mide primero, prueba una técnica y mira si los números se mueven.",
};

const ORDEN = ["ai-engineering", "evals", "ai-search"];
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
          <span className="eyebrow">Curso-manual en español</span>
          <h1>AI Engineering, del demo a producción</h1>
          <p className="lead">
            Tres cursos escritos para leerse despacio y correrse de verdad. Cada idea viene con su porqué, sus
            compromisos reales, el código completo y ejercicios con solución. Todo alrededor de un mismo proyecto que
            crece módulo a módulo.
          </p>
          <div className="acciones">
            <Link className="btn primary grande" href={`/leer/${primero}`}>Leer el primer módulo gratis</Link>
            <Link className="btn grande" href="#planes">Ver planes</Link>
          </div>
          <div className="cifras">
            <div><b>{cursos.length}</b><span>cursos</span></div>
            <div><b>{modulos}</b><span>módulos</span></div>
            <div><b>{quizzes}</b><span>autoevaluaciones corregidas</span></div>
            <div><b>100 %</b><span>código descargable</span></div>
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="ancho">
          <h2>Cómo está hecho cada módulo</h2>
          <p className="sub">No son notas sueltas ni diapositivas. Cada módulo tiene cuatro piezas que se leen en orden.</p>
          <div className="rejilla">
            <div className="tarjeta"><span className="num">01 · Manual</span><h3>El texto principal</h3>
              <p>La explicación completa: qué problema resuelve cada técnica, cómo funciona por dentro y cuándo no usarla.</p></div>
            <div className="tarjeta"><span className="num">02 · Código</span><h3>Scripts completos</h3>
              <p>El código de cada lección, de principio a fin. Lo lees en la web y lo descargas para correrlo con tu propia API key.</p></div>
            <div className="tarjeta"><span className="num">03 · Ejercicios</span><h3>Con solución</h3>
              <p>Problemas que te obligan a modificar el sistema, no a repetir el ejemplo. La solución está al final de cada uno.</p></div>
            <div className="tarjeta"><span className="num">04 · Autoevaluación</span><h3>Corregida al momento</h3>
              <p>Preguntas que explican por qué cada respuesta es correcta o no. Tu progreso queda guardado en tu cuenta.</p></div>
          </div>
        </div>
      </section>

      <section className="seccion" id="cursos">
        <div className="ancho">
          <h2>Los tres cursos</h2>
          <p className="sub">Se pueden leer por separado, pero están pensados en este orden: construir, medir, mejorar.</p>
          <div className="rejilla">
            {lista.map((c, k) => (
              <div className="tarjeta" key={c.id}>
                <span className="num">Curso {k + 1} · {c.modulos} módulos</span>
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
              <ul><li>Los tres cursos completos</li><li>Código descargable</li><li>Renuevas solo si quieres seguir</li></ul>
              <div className="pie"><Link className="btn" href="/comprar?plan=mensual">Elegir mensual</Link></div>
            </div>
            <div className="tarjeta plan destacado">
              <span className="etiqueta">Dos meses de ahorro</span>
              <h3>{PLANES.anual.nombre}</h3>
              <div className="precio">{PLANES.anual.usd} USD <small>/ año</small></div>
              <ul><li>Los tres cursos completos</li><li>Código descargable</li><li>Todo el contenido nuevo durante el año</li></ul>
              <div className="pie"><Link className="btn primary" href="/comprar?plan=anual">Elegir anual</Link></div>
            </div>
            <div className="tarjeta plan">
              <h3>{PLANES.curso.nombre}</h3>
              <div className="precio">{PLANES.curso.usd} USD <small>/ pago único</small></div>
              <ul><li>El curso que elijas, para siempre</li><li>Su código descargable</li><li>Sus actualizaciones incluidas</li></ul>
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
          <details><summary>¿El código se ejecuta en la web?</summary>
            <p>No. Lees el código en la web y lo descargas para correrlo en tu máquina. Así ves los resultados con tu propio entorno y tu propia cuenta del proveedor.</p></details>
          <details><summary>¿Necesito pagar una API de un proveedor de modelos?</summary>
            <p>Para correr los ejemplos con LLM sí necesitas una API key propia (OpenAI, Anthropic, Google u OpenRouter) o un modelo local con Ollama. Ese costo va aparte y cada lección indica cuánto es aproximadamente.</p></details>
          <details><summary>¿Los planes se renuevan automáticamente?</summary>
            <p>No. El plan mensual y el anual son pagos únicos por un periodo de acceso. Cuando termina, decides si renuevas.</p></details>
          <details><summary>¿Hay videos?</summary>
            <p>Esta primera versión es texto, código y ejercicios. El contenido grabado llegará en una versión posterior.</p></details>
          <details><summary>¿Puedo pedir un reembolso?</summary>
            <p>Sí, dentro de los plazos de la <Link href="/terminos">política de reembolso</Link>.</p></details>
        </div>
      </section>
    </Sitio>
  );
}
