// Composición de la app: navegación, barra superior y el notebook activo.
import { useEffect, useMemo, useState } from "react";
import { api, API_URL } from "./api";
import { Notebook } from "./components/Notebook";
import { Sidebar } from "./components/Sidebar";
import { Toaster, toast } from "./toast";
import type { NavGroup, Progress } from "./types";

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
  const [progress, setProgress] = useState<Progress>({});
  const [current, setCurrent] = useState<string | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [sideOpen, setSideOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>(() => {
    const t = lsGet(LS_THEME);
    return t === "light" || t === "dark" ? t : "system";
  });

  const flat = useMemo(() => nav.flatMap((g) => g.items), [nav]);

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
    setSideOpen(false);
    document.querySelector(".scroll")?.scrollTo({ top: 0 });
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
      <Sidebar nav={nav} current={current} progress={progress} open={sideOpen} onSelect={go} />

      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setSideOpen(!sideOpen)} aria-label="Menú">☰</button>
          <div className="progress-wrap">
            <div className="progress-top">
              <span>Progreso del curso</span>
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
            {current ? (
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
