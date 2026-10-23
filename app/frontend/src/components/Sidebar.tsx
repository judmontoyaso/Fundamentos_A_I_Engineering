// Navegación por módulos con el estado de cada notebook.
import type { NavGroup, Progress } from "../types";

type Props = {
  nav: NavGroup[];
  current: string | null;
  progress: Progress;
  open: boolean;
  onSelect: (id: string) => void;
};

export function Sidebar({ nav, current, progress, open, onSelect }: Props) {
  return (
    <aside className={"sidebar" + (open ? " open" : "")}>
      <div className="brand">
        <div className="logo">AIE</div>
        <div>
          <h1>AI Engineering</h1>
          <p>Notebook interactivo</p>
        </div>
      </div>
      <nav className="nav">
        {nav.map((g) => (
          <div className="nav-group" key={g.group}>
            <span className="glabel">{g.group}</span>
            {g.items.map((it) => (
              <button
                key={it.id}
                className={
                  "nav-item" + (it.id === current ? " active" : "") + (progress[it.id] ? " done" : "")
                }
                onClick={() => onSelect(it.id)}
              >
                <span className="tick">✓</span>
                <span>{it.title}</span>
                {it.type === "lab" && <span className="kind">▶</span>}
                {it.type === "quiz" && <span className="kind">?</span>}
                {it.type === "app" && <span className="kind live">● en vivo</span>}
              </button>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
