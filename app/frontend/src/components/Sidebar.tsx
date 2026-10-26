// Navegación por módulos con el estado de cada notebook.
import type { Course, NavGroup, Progress } from "../types";

type Props = {
  nav: NavGroup[];
  courses: Course[];
  course: string | undefined;
  onCourse: (id: string) => void;
  current: string | null;
  progress: Progress;
  open: boolean;
  onSelect: (id: string) => void;
};

export function Sidebar({ nav, courses, course, onCourse, current, progress, open, onSelect }: Props) {
  return (
    <aside className={"sidebar" + (open ? " open" : "")}>
      <div className="brand">
        <div className="logo">AIE</div>
        <div>
          <h1>AI Engineering</h1>
          <p>Notebook interactivo</p>
        </div>
      </div>
      {courses.length > 1 && (
        <label className="course-pick">
          <span>Curso</span>
          <select value={course} onChange={(e) => onCourse(e.target.value)}>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
          </select>
        </label>
      )}
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
