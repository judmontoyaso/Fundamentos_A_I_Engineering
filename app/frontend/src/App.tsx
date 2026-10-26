// Composición de la app: navegación, barra superior y el notebook activo.
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, API_URL } from "./api";
import { Anotar } from "./components/Anotar";
import { Asistente } from "./components/Asistente";
import { Notebook } from "./components/Notebook";
import { Quiz } from "./components/Quiz";
import { Sidebar } from "./components/Sidebar";
import { Toaster, toast } from "./toast";
import type { Course, NavGroup, Progress } from "./types";

type Theme = "system" | "light" | "dark";
const THEMES: Theme[] = ["system", "light", "dark"];
const LS_THEME = "curso_tema";
const LS_LAST = "curso_ultimo";

function lsGet(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
function lsSet(key: string, value: string) {
  try { localStorage.setItem(key, value); } catch { /* almacenamiento bloqueado */ }
}

export default function App() {
  const [nav, setNav] = useState<NavGroup[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [progress, setProgress] = useState<Progress>({});
  const [current, setCurrent] = useState<string | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [sideOpen, setSideOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>(() => {
    const t = lsGet(LS_THEME);
    return t === "light" || t === "dark" ? t : "system";
  });

  const items = useMemo(() => nav.flatMap((g) => g.items), [nav]);
  // El curso activo es el del notebook abierto; la navegación y el progreso son de ese curso.
  const course = nav.find((g) => g.items.some((it) => it.id === current))?.course ?? courses[0]?.id;
  const courseNav = useMemo(() => nav.filter((g) => g.course === course), [nav, course]);
  const flat = useMemo(
    () => courseNav.flatMap((g) => g.items).filter((it) => it.type !== "app"),   // lo que cuenta para el progreso
    [courseNav],
  );
  const currentType = items.find((it) => it.id === current)?.type;

  const markPassed = useCallback(() => {
    if (!current) return;
    setProgress((p) => ({ ...p, [current]: true }));
    api.setProgress(current, true).catch(() => toast("No se pudo guardar el progreso"));
  }, [current]);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    lsSet(LS_THEME, theme);
  }, [theme]);

  useEffect(() => {
    api.modules()
      .then((d) => {
        setNav(d.nav);
        setCourses(d.courses ?? []);
        setProgress(d.progress ?? {});
        const ids = d.nav.flatMap((g) => g.items.map((it) => it.id));
        const last = lsGet(LS_LAST);
        setCurrent(last && ids.includes(last) ? last : ids[0] ?? null);
      })
      .catch(() => setApiDown(true));
  }, []);

  function go(id: string) {
    setCurrent(id);
    lsSet(LS_LAST, id);
    const c = nav.find((g) => g.items.some((it) => it.id === id))?.course;
    if (c) lsSet(`${LS_LAST}:${c}`, id);
    setSideOpen(false);
    document.querySelector(".scroll")?.scrollTo({ top: 0 });
  }

  function switchCourse(id: string) {
    const last = lsGet(`${LS_LAST}:${id}`);
    const ids = nav.filter((g) => g.course === id).flatMap((g) => g.items.map((it) => it.id));
    const target = last && ids.includes(last) ? last : ids[0];
    if (target) go(target);
  }

  function toggleDone(id: string) {
    const value = !progress[id];
    setProgress((p) => ({ ...p, [id]: value }));
    api.setProgress(id, value).catch(() => toast("No se pudo guardar el progreso"));
  }

  async function resetKernel() {
    if (!current) return;
    await api.resetSession(current);
    toast("Kernel reiniciado: las variables de este notebook se borraron");
  }

  const done = flat.filter((it) => progress[it.id]).length;
  const pct = flat.length ? Math.round((done / flat.length) * 100) : 0;
  const themeIcon = theme === "light" ? "☀" : theme === "dark" ? "☾" : "◐";

  if (apiDown) {
    return (
      <div className="api-down">
        <h1>No hay conexión con la API</h1>
        <p>El frontend no pudo llegar a <code>{API_URL}</code>. Arranca el backend en otra terminal:</p>
        <pre>cd app/backend{"\n"}.venv\Scripts\activate{"\n"}python run.py</pre>
        <p>Y recarga esta página.</p>
      </div>
    );
  }

  return (
    <div className="app">
      <div className={"scrim" + (sideOpen ? " show" : "")} onClick={() => setSideOpen(false)} />
      <Sidebar nav={courseNav} courses={courses} course={course} onCourse={switchCourse}
               current={current} progress={progress} open={sideOpen} onSelect={go} />

      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setSideOpen(!sideOpen)} aria-label="Menú">☰</button>
          <div className="progress-wrap">
            <div className="progress-top">
              <span>Progreso · {courses.find((c) => c.id === course)?.title ?? "curso"}</span>
              <span className="mono"><b>{pct}%</b> · {done}/{flat.length}</span>
            </div>
            <div className="bar"><span style={{ width: `${pct}%` }} /></div>
          </div>
          <button className="tbtn" onClick={resetKernel} title="Borrar las variables del kernel de este notebook">↺ kernel</button>
          <button className="tbtn" onClick={() => setTheme(THEMES[(THEMES.indexOf(theme) + 1) % 3])} title="Cambiar tema">
            {themeIcon}
          </button>
        </header>

        <div className="scroll">
          <div className="reader">
            {current && currentType === "app" ? (
              <Asistente />
            ) : current && currentType === "anotar" ? (
              <Anotar key={current} id={current} flat={flat} done={Boolean(progress[current])}
                      onCompleted={markPassed} onNavigate={go} />
            ) : current && currentType === "quiz" ? (
              <Quiz key={current} id={current} flat={flat} done={Boolean(progress[current])}
                    onPassed={markPassed} onNavigate={go} />
            ) : current ? (
              <Notebook
                key={current}
                id={current}
                flat={flat}
                done={Boolean(progress[current])}
                onToggleDone={() => toggleDone(current)}
                onNavigate={go}
              />
            ) : (
              <p className="muted">Cargando el curso…</p>
            )}
          </div>
        </div>
      </main>
      <Toaster />
    </div>
  );
}
