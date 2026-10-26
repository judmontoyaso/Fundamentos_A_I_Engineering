// Tarea de anotación (curso de Evals, Módulo 4): un ítem a la vez, con la guía a mano.
// Atajos: P = pasa, N = no pasa, flechas = anterior / siguiente.
import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { toast } from "../toast";
import type { NavItem, TareaAnotacion } from "../types";
import { MarkdownCell } from "./MarkdownCell";

type Props = {
  id: string;
  flat: NavItem[];
  done: boolean;
  onCompleted: () => void;
  onNavigate: (id: string) => void;
};

export function Anotar({ id, flat, done, onCompleted, onNavigate }: Props) {
  const [tarea, setTarea] = useState<TareaAnotacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pos, setPos] = useState(0);
  const [nota, setNota] = useState("");
  const [verGuia, setVerGuia] = useState(true);

  useEffect(() => {
    setTarea(null);
    api.anotacion(id).then((t) => {
      setTarea(t);
      const primera = t.items.findIndex((it) => !(it.id in t.etiquetas));
      setPos(primera === -1 ? 0 : primera);
    }).catch((e: Error) => setError(e.message));
  }, [id]);

  const item = tarea?.items[pos];
  useEffect(() => { setNota(item && tarea ? tarea.etiquetas[item.id]?.nota ?? "" : ""); }, [item, tarea]);

  const total = tarea?.items.length ?? 0;
  const hechas = tarea ? Object.keys(tarea.etiquetas).length : 0;

  const etiquetar = useCallback(async (label: boolean) => {
    if (!tarea || !item) return;
    try {
      await api.anotar(id, item.id, label, nota);
    } catch {
      toast("No se pudo guardar la etiqueta");
      return;
    }
    const etiquetas = { ...tarea.etiquetas, [item.id]: { label, nota } };
    setTarea({ ...tarea, etiquetas });
    if (Object.keys(etiquetas).length === tarea.items.length && !done) onCompleted();
    const siguiente = tarea.items.findIndex((it, k) => k > pos && !(it.id in etiquetas));
    if (siguiente !== -1) setPos(siguiente);
    else if (pos < tarea.items.length - 1) setPos(pos + 1);
  }, [tarea, item, id, nota, pos, done, onCompleted]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.target as HTMLElement)?.tagName === "TEXTAREA") return;
      if (e.key === "p" || e.key === "P") etiquetar(true);
      else if (e.key === "n" || e.key === "N") etiquetar(false);
      else if (e.key === "ArrowRight") setPos((p) => Math.min(p + 1, total - 1));
      else if (e.key === "ArrowLeft") setPos((p) => Math.max(p - 1, 0));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [etiquetar, total]);

  if (error) return <p className="muted">No se pudo cargar la tarea ({error}).</p>;
  if (!tarea || !item) return <p className="muted">Cargando…</p>;

  const actual = tarea.etiquetas[item.id];
  const idx = flat.findIndex((it) => it.id === id);
  const prev = flat[idx - 1];
  const next = flat[idx + 1];

  return (
    <div className="anotar">
      <div className="md">
        <h1>{tarea.title}</h1>
        <p>
          Etiqueta cada salida <b>sin mirar</b> las etiquetas del autor. Tus etiquetas se guardan en la base de la app y
          los laboratorios de este módulo las comparan con las del autor. Atajos: <kbd>P</kbd> pasa, <kbd>N</kbd> no
          pasa, <kbd>←</kbd> <kbd>→</kbd> moverse.
        </p>
      </div>

      <button className="link-btn" onClick={() => setVerGuia(!verGuia)}>{verGuia ? "Ocultar la guía" : "Ver la guía"}</button>
      {verGuia && <div className="an-guia"><MarkdownCell source={tarea.guia} onNavigate={onNavigate} /></div>}

      <div className="an-barra mono">
        <span>{pos + 1} / {total}</span>
        <span>{hechas} anotadas</span>
        <div className="bar"><span style={{ width: `${(hechas / total) * 100}%` }} /></div>
      </div>

      <article className="an-item">
        <div className="an-campo"><span className="an-etq">CV</span><p>{item.cv}</p></div>
        <div className="an-campo"><span className="an-etq">Salida</span><p className="an-salida">{item.salida}</p></div>
        <p className="an-preg">{tarea.pregunta}</p>
        <textarea
          rows={2}
          placeholder="Nota (opcional): por qué, o tu duda"
          value={nota}
          onChange={(e) => setNota(e.target.value)}
        />
        <div className="an-botones">
          <button className={"btn an-pasa" + (actual?.label === true ? " sel" : "")} onClick={() => etiquetar(true)}>
            ✓ Pasa
          </button>
          <button className={"btn an-nopasa" + (actual?.label === false ? " sel" : "")} onClick={() => etiquetar(false)}>
            ✗ No pasa
          </button>
          <span className="an-nav">
            <button className="btn" disabled={pos === 0} onClick={() => setPos(pos - 1)}>←</button>
            <button className="btn" disabled={pos === total - 1} onClick={() => setPos(pos + 1)}>→</button>
          </span>
        </div>
      </article>

      <div className="an-mapa">
        {tarea.items.map((it, k) => {
          const e = tarea.etiquetas[it.id];
          return (
            <button key={it.id} title={`#${it.id}`} onClick={() => setPos(k)}
                    className={"an-punto" + (k === pos ? " act" : "") + (e ? (e.label ? " ok" : " no") : "")}>
              {it.id}
            </button>
          );
        })}
      </div>

      <div className="foot">
        <span className="muted mono">{hechas === total ? "Tarea completa: corre el laboratorio 01." : `Faltan ${total - hechas}.`}</span>
        <div className="nav-arrows">
          {prev && <button className="btn" onClick={() => onNavigate(prev.id)}>← {prev.title}</button>}
          {next && <button className="btn" onClick={() => onNavigate(next.id)}>{next.title} →</button>}
        </div>
      </div>
    </div>
  );
}
