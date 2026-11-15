"use client";
// Marco del lector: barra lateral con el temario, barra superior con el progreso, y el contenido.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { CursoNav, GrupoNav, Progreso } from "@/lib/tipos";

type Tema = "system" | "light" | "dark";
const TEMAS: Tema[] = ["system", "light", "dark"];
const NOMBRE = process.env.NEXT_PUBLIC_NOMBRE_SITIO ?? "IA en Producción";

type Props = {
  cursos: CursoNav[];
  inicios: Record<string, string>;   // curso -> primer ítem
  cursoId: string;
  grupos: GrupoNav[];
  actual: string;
  progreso: Progreso;
  abierto: boolean;                  // el lector tiene acceso completo a este curso
  email: string | null;
  urlEntrar: string;
  children: React.ReactNode;
};

export function Shell({ cursos, inicios, cursoId, grupos, actual, progreso, abierto, email, urlEntrar, children }: Props) {
  const router = useRouter();
  const [lateral, setLateral] = useState(false);
  const [tema, setTema] = useState<Tema>("system");

  useEffect(() => {
    try {
      const t = localStorage.getItem("curso_tema");
      if (t === "light" || t === "dark") setTema(t);
    } catch { /* almacenamiento bloqueado */ }
  }, []);
  useEffect(() => { setLateral(false); }, [actual]);

  function cambiarTema() {
    const t = TEMAS[(TEMAS.indexOf(tema) + 1) % 3];
    setTema(t);
    if (t === "system") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("curso_tema", t); } catch { /* idem */ }
  }

  const items = grupos.flatMap((g) => g.items);
  const hechos = items.filter((it) => progreso[it.id]).length;
  const pct = items.length ? Math.round((hechos / items.length) * 100) : 0;
  const titulo = cursos.find((c) => c.id === cursoId)?.titulo ?? "Curso";

  return (
    <div className="app">
      <div className={"scrim" + (lateral ? " show" : "")} onClick={() => setLateral(false)} />
      <aside className={"sidebar" + (lateral ? " open" : "")}>
        <Link className="brand" href="/">
          <div className="logo">IAP</div>
          <div>
            <h1>{NOMBRE}</h1>
            <p>AI Engineering</p>
          </div>
        </Link>
        {cursos.length > 1 && (
          <label className="course-pick">
            <span>Curso</span>
            <select value={cursoId} onChange={(e) => router.push(`/leer/${inicios[e.target.value]}`)}>
              {cursos.map((c) => <option key={c.id} value={c.id}>{c.titulo}</option>)}
            </select>
          </label>
        )}
        <nav className="nav" aria-label="Temario">
          {grupos.map((g) => (
            <div className="nav-group" key={g.grupo}>
              <span className="glabel">{g.grupo}</span>
              {g.items.map((it) => (
                <Link key={it.id} href={`/leer/${it.id}`} prefetch={false}
                      className={"nav-item" + (it.id === actual ? " active" : "") + (progreso[it.id] ? " done" : "")}
                      aria-current={it.id === actual ? "page" : undefined}>
                  <span className="tick">✓</span>
                  <span>{it.titulo}</span>
                  {!abierto && !it.gratis ? <span className="kind lock" title="Incluido en los planes">🔒</span>
                    : !abierto && it.gratis ? <span className="kind">gratis</span>
                    : it.tipo === "quiz" ? <span className="kind">?</span>
                    : it.tipo === "anotar" ? <span className="kind">✎</span>
                    : it.tipo === "lab" ? <span className="kind">{"</>"}</span> : null}
                </Link>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setLateral(!lateral)} aria-label="Temario">☰</button>
          <div className="progress-wrap">
            <div className="progress-top">
              <span>{email ? `Progreso · ${titulo}` : titulo}</span>
              {email ? <span className="mono"><b>{pct}%</b> · {hechos}/{items.length}</span> : <span>Vista previa gratuita</span>}
            </div>
            <div className="bar"><span style={{ width: `${email ? pct : 0}%` }} /></div>
          </div>
          <button className="tbtn" onClick={cambiarTema} title="Cambiar tema" aria-label="Cambiar tema">
            {tema === "light" ? "☀" : tema === "dark" ? "☾" : "◐"}
          </button>
          {!abierto && <Link className="tbtn cta" href="/#planes">Ver planes</Link>}
          {email ? <Link className="tbtn" href="/cuenta">Mi cuenta</Link> : <a className="tbtn" href={urlEntrar}>Entrar</a>}
        </header>
        <div className="scroll" key={actual}>
          <div className="reader">{children}</div>
        </div>
      </main>
    </div>
  );
}
