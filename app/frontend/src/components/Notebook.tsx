// Un notebook: carga sus celdas de la API y las pinta en orden.
import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { NavItem, Notebook as NotebookT } from "../types";
import { CodeCell } from "./CodeCell";
import { MarkdownCell } from "./MarkdownCell";

type Props = {
  id: string;
  flat: NavItem[];
  done: boolean;
  onToggleDone: () => void;
  onNavigate: (id: string) => void;
};

export function Notebook({ id, flat, done, onToggleDone, onNavigate }: Props) {
  const [nb, setNb] = useState<NotebookT | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const load = useCallback(() => {
    setError(null);
    return api.notebook(id).then(setNb).catch((e: Error) => setError(e.message));
  }, [id]);

  useEffect(() => { setNb(null); load(); }, [load]);

  // Tras restaurar una celda: recargar y volver a montar las celdas con el código nuevo.
  const reload = () => { load().then(() => setVersion((v) => v + 1)); };

  if (error) return <p className="muted">No se pudo cargar el notebook ({error}).</p>;
  if (!nb) return <p className="muted">Cargando…</p>;

  const pos = flat.findIndex((it) => it.id === id);
  const prev = flat[pos - 1];
  const next = flat[pos + 1];

  return (
    <>
      {nb.cells.map((cell) =>
        cell.type === "code" ? (
          <CodeCell key={`${id}:${cell.idx}:${version}`} cell={cell} nbId={id} onReload={reload} />
        ) : (
          <MarkdownCell key={`${id}:${cell.idx}`} source={cell.source} prefix={id.replace(/(m\d+-[a-z]+|inicio)$/, "")}
                        onNavigate={onNavigate} />
        ),
      )}
      <div className="foot">
        <button className={"btn " + (done ? "done-state" : "primary")} onClick={onToggleDone}>
          {done ? "✓ Leída" : "Marcar como leída"}
        </button>
        <div className="nav-arrows">
          {prev && <button className="btn" onClick={() => onNavigate(prev.id)}>← {prev.title}</button>}
          {next && <button className="btn" onClick={() => onNavigate(next.id)}>{next.title} →</button>}
        </div>
      </div>
    </>
  );
}
