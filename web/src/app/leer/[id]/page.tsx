// El lector. Decide en el servidor si esta persona puede ver la lección; si no, el contenido ni se envía.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Anotar } from "@/components/Anotar";
import { Pie } from "@/components/Pie";
import { Prosa } from "@/components/Prosa";
import { Quiz } from "@/components/Quiz";
import { Shell } from "@/components/Shell";
import { cursosAbiertos } from "@/lib/acceso";
import { getUsuario, urlEntrar } from "@/lib/auth";
import { curso, cursos, gruposDe, item, itemsDe } from "@/lib/contenido";
import { NOMBRE_SITIO, urlSitioPublico } from "@/lib/sitio";
import { store } from "@/lib/store";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ id: string }> };

function extractoTexto(html?: string): string {
  if (!html) return "";
  const limpio = html
    .replace(/<h1[^>]*>[\s\S]*?<\/h1>/i, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return limpio.slice(0, 158) + (limpio.length > 158 ? "…" : "");
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const it = item(id);
  if (!it) return { robots: { index: false, follow: false } };
  const c = curso(it.curso);
  const grupo = gruposDe(it.curso).find((g) => g.items.some((x) => x.id === it.id))?.grupo;
  const titulo = grupo && grupo !== "Inicio" ? `${it.titulo} · ${grupo}` : `${it.titulo} · ${c?.titulo ?? NOMBRE_SITIO}`;
  const desc = it.gratis
    ? extractoTexto(it.html) || `Muestra gratuita del curso ${c?.titulo ?? NOMBRE_SITIO}.`
    : `Lección del curso ${c?.titulo ?? NOMBRE_SITIO}.`;
  return {
    title: titulo,
    description: desc,
    alternates: { canonical: `/leer/${encodeURIComponent(id)}` },
    openGraph: {
      title: titulo,
      description: desc,
      type: "article",
      url: `/leer/${encodeURIComponent(id)}`,
    },
    robots: it.gratis ? { index: true, follow: true } : { index: false, follow: true },
  };
}

export default async function Leer({ params }: Props) {
  const { id } = await params;
  const it = item(id);
  if (!it) notFound();

  const usuario = await getUsuario();
  const abierto = (await cursosAbiertos(usuario, [it.curso])).has(it.curso);
  const permitido = it.gratis || abierto;
  const progreso = usuario ? await store.progreso(usuario.id) : {};

  const cActual = curso(it.curso);
  const grupos = gruposDe(it.curso);
  const grupoActual = grupos.find((g) => g.items.some((x) => x.id === id))?.grupo;
  const plano = itemsDe(it.curso);
  const pos = plano.findIndex((x) => x.id === id);
  const prev = plano[pos - 1];
  const next = plano[pos + 1];
  const entrar = urlEntrar(`/leer/${id}`);
  const inicios = Object.fromEntries(cursos.map((c) => [c.id, itemsDe(c.id)[0]?.id ?? ""]));
  const hecho = Boolean(progreso[id]);

  let cuerpo: React.ReactNode;
  if (!permitido) {
    cuerpo = (
      <div className="muro">
        <div className="candado" aria-hidden>🔒</div>
        <h1>{grupoActual && grupoActual !== "Inicio" ? grupoActual : it.titulo}</h1>
        <p>
          Esta lección forma parte del contenido de pago.{" "}
          {usuario ? "Tu cuenta todavía no tiene un plan que incluya este curso." : "Elige un plan o entra con tu cuenta si ya lo compraste."}
        </p>
        <div className="acciones">
          <Link className="btn primary" href="/#planes">Ver planes</Link>
          {!usuario && <a className="btn" href={entrar}>Ya tengo cuenta</a>}
          <Link className="btn" href={`/leer/${inicios[it.curso]}`}>Leer la muestra gratis</Link>
        </div>
      </div>
    );
  } else if (it.tipo === "quiz") {
    cuerpo = <Quiz key={id} id={id} preguntas={it.preguntas ?? []} hecho={hecho} conSesion={Boolean(usuario)} prev={prev} next={next} />;
  } else if (it.tipo === "anotar" && it.tarea) {
    cuerpo = usuario ? (
      <Anotar key={id} id={id} tarea={it.tarea} iniciales={await store.etiquetas(usuario.id, id)} hecho={hecho} prev={prev} next={next} />
    ) : (
      <div className="muro"><h1>{it.tarea.titulo}</h1><p>Entra con tu cuenta para guardar tus etiquetas.</p>
        <div className="acciones"><a className="btn primary" href={entrar}>Entrar</a></div></div>
    );
  } else {
    cuerpo = (
      <>
        <Prosa html={it.html ?? ""} />
        <Pie key={id} id={id} hecho={hecho} conSesion={Boolean(usuario)} urlEntrar={entrar} prev={prev} next={next} />
      </>
    );
  }

  const base = urlSitioPublico();
  const breadcrumb = it.gratis
    ? {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: NOMBRE_SITIO, item: `${base}/` },
          { "@type": "ListItem", position: 2, name: cActual?.titulo ?? it.curso, item: `${base}/leer/${inicios[it.curso]}` },
          { "@type": "ListItem", position: 3, name: grupoActual && grupoActual !== "Inicio" ? `${grupoActual} · ${it.titulo}` : it.titulo, item: `${base}/leer/${encodeURIComponent(id)}` },
        ],
      }
    : null;

  return (
    <Shell cursos={cursos} inicios={inicios} cursoId={it.curso} grupos={grupos} actual={id} progreso={progreso}
           abierto={abierto} email={usuario?.email ?? null} urlEntrar={entrar}>
      {breadcrumb && (
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumb) }} />
      )}
      {cuerpo}
    </Shell>
  );
}
