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
import { cursos, gruposDe, item, itemsDe } from "@/lib/contenido";
import { store } from "@/lib/store";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const it = item((await params).id);
  if (!it) return {};
  const grupo = gruposDe(it.curso).find((g) => g.items.some((x) => x.id === it.id))?.grupo;
  return { title: grupo && grupo !== "Inicio" ? `${it.titulo} · ${grupo}` : it.titulo };
}

export default async function Leer({ params }: Props) {
  const { id } = await params;
  const it = item(id);
  if (!it) notFound();

  const usuario = await getUsuario();
  const abierto = (await cursosAbiertos(usuario, [it.curso])).has(it.curso);
  const permitido = it.gratis || abierto;
  const progreso = usuario ? await store.progreso(usuario.id) : {};

  const grupos = gruposDe(it.curso);
  const plano = itemsDe(it.curso);
  const pos = plano.findIndex((x) => x.id === id);
  const prev = plano[pos - 1];
  const next = plano[pos + 1];
  const entrar = urlEntrar(`/leer/${id}`);
  const inicios = Object.fromEntries(cursos.map((c) => [c.id, itemsDe(c.id)[0]?.id ?? ""]));
  const hecho = Boolean(progreso[id]);

  let cuerpo: React.ReactNode;
  if (!permitido) {
    const grupo = grupos.find((g) => g.items.some((x) => x.id === id))?.grupo;
    cuerpo = (
      <div className="muro">
        <div className="candado" aria-hidden>🔒</div>
        <h1>{grupo && grupo !== "Inicio" ? grupo : it.titulo}</h1>
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

  return (
    <Shell cursos={cursos} inicios={inicios} cursoId={it.curso} grupos={grupos} actual={id} progreso={progreso}
           abierto={abierto} email={usuario?.email ?? null} urlEntrar={entrar}>
      {cuerpo}
    </Shell>
  );
}
