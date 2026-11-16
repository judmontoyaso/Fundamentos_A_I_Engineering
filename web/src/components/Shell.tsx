"use client";
// Marco del lector: barra lateral con el temario, barra superior con el progreso, y el contenido.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, CircleHelp, Code, Download, Lock, Menu, Monitor, Moon, PenLine, Sun } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Logo } from "@/components/Logo";
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
  const scrollRef = useRef<HTMLDivElement>(null);
  const avanceRef = useRef<HTMLDivElement>(null);

  // Avance de lectura de la lección actual: se escribe directo en el estilo para no re-renderizar al hacer scroll.
  useEffect(() => {
    const el = scrollRef.current;
    const barra = avanceRef.current;
    if (!el || !barra) return;
    const pintar = () => {
      const total = el.scrollHeight - el.clientHeight;
      barra.style.transform = `scaleX(${total > 0 ? Math.min(1, el.scrollTop / total) : 0})`;
    };
    pintar();
    el.addEventListener("scroll", pintar, { passive: true });
    return () => el.removeEventListener("scroll", pintar);
  }, [actual]);

  useEffect(() => {
    try {
      const t = localStorage.getItem("curso_tema");
      if (t === "light" || t === "dark") setTema(t);
    } catch { /* almacenamiento bloqueado */ }
  }, []);

  useEffect(() => {
    setLateral(false);
    document.querySelector(".nav-item.active")?.scrollIntoView({ block: "nearest" });
  }, [actual]);

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
          <Logo size={34} />
          <div>
            <h1>{NOMBRE}</h1>
            <p>Ingeniería de IA aplicada</p>
          </div>
        </Link>
        {cursos.length > 1 && (
          <label className="course-pick">
            <span>Curso ({cursos.findIndex((c) => c.id === cursoId) + 1} de {cursos.length})</span>
            <select value={cursoId} onChange={(e) => router.push(`/leer/${inicios[e.target.value]}`)}>
              {cursos.map((c, idx) => <option key={c.id} value={c.id}>{idx + 1}. {c.titulo}</option>)}
            </select>
          </label>
        )}
        <nav className="nav" aria-label="Temario">
          {grupos.map((g) => {
            const gHechos = g.items.filter((i) => progreso[i.id]).length;
            const gCompleto = g.items.length > 0 && gHechos === g.items.length;
            return (
              <div className="nav-group" key={g.grupo}>
                <span className="glabel">
                  <span>{g.grupo}</span>
                  {email && (
                    <small className={gCompleto ? "g-ok" : ""} aria-label={`${gHechos} de ${g.items.length} completadas`}>
                      {gCompleto ? <Check size={13} strokeWidth={3} aria-hidden /> : `${gHechos}/${g.items.length}`}
                    </small>
                  )}
                </span>
                {g.items.map((it) => (
                  <Link key={it.id} href={`/leer/${it.id}`} prefetch={false}
                        className={"nav-item" + (it.id === actual ? " active" : "") + (progreso[it.id] ? " done" : "")}
                        aria-current={it.id === actual ? "page" : undefined}>
                    <span className="tick" aria-hidden><Check size={11} strokeWidth={3.2} /></span>
                    <span>{it.titulo}</span>
                    {!abierto && !it.gratis ? <span className="kind lock" title="Incluido en los planes"><Lock size={13} aria-label="De pago" /></span>
                      : !abierto && it.gratis ? <span className="kind">gratis</span>
                      : it.tipo === "quiz" ? <span className="kind" title="Autoevaluación"><CircleHelp size={14} aria-hidden /></span>
                      : it.tipo === "anotar" ? <span className="kind" title="Ejercicio de etiquetado"><PenLine size={14} aria-hidden /></span>
                      : it.tipo === "lab" ? <span className="kind" title="Código"><Code size={14} aria-hidden /></span> : null}
                  </Link>
                ))}
              </div>
            );
          })}
          <a
            className="nav-item nav-zip"
            href={abierto ? `/descargar/${cursoId}` : `/descargar/${cursoId}?muestra=1`}
          >
            <span className="tick zip" aria-hidden><Download size={12} /></span>
            <span>{abierto ? "Descargar código completo (.zip)" : "Descargar muestra gratis (.zip)"}</span>
          </a>
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setLateral(!lateral)} aria-label="Abrir el temario" aria-expanded={lateral}>
            <Menu size={18} aria-hidden />
          </button>
          <div className="progress-wrap">
            <div className="progress-top">
              <span>{titulo}</span>
              {email ? <span><b>{pct} %</b><span className="solo-ancho"> completado, {hechos} de {items.length}</span></span> : <span>Vista previa gratuita</span>}
            </div>
            <div className="bar"><span style={{ width: `${email ? pct : 0}%` }} /></div>
          </div>
          {email && pct === 100 && (
            <Link className="tbtn cta" href="/cuenta" title="Tu certificado está listo">
              Certificado listo
            </Link>
          )}
          <button className="tbtn" onClick={cambiarTema} title="Cambiar tema" aria-label="Cambiar tema">
            {tema === "light" ? <Sun size={16} aria-hidden /> : tema === "dark" ? <Moon size={16} aria-hidden /> : <Monitor size={16} aria-hidden />}
          </button>
          {!abierto && <Link className="tbtn cta" href="/#planes">Ver planes</Link>}
          {email ? <Link className="tbtn solo-ancho" href="/cuenta">Mi cuenta</Link> : <a className="tbtn solo-ancho" href={urlEntrar}>Entrar</a>}
          <div className="avance-leccion" aria-hidden><div ref={avanceRef} /></div>
        </header>
        <div className="scroll" key={actual} ref={scrollRef}>
          <div className="reader">{children}</div>
        </div>
      </main>
    </div>
  );
}
