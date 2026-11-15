"use client";
// Tarea de anotación (curso de Evals, Módulo 4): un ítem a la vez, con la guía a mano.
// Atajos: P = pasa, N = no pasa, flechas = anterior / siguiente.
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { guardarEtiqueta, guardarProgreso } from "@/lib/cliente";
import type { Etiquetas, ItemNav, Tarea } from "@/lib/tipos";
import { Flechas } from "./Pie";

type Props = { id: string; tarea: Tarea; iniciales: Etiquetas; hecho: boolean; prev?: ItemNav; next?: ItemNav };

export function Anotar({ id, tarea, iniciales, hecho, prev, next }: Props) {
  const router = useRouter();
  const [etiquetas, setEtiquetas] = useState<Etiquetas>(iniciales);
  const [pos, setPos] = useState(() => {
    const primera = tarea.items.findIndex((it) => !(it.id in iniciales));
    return primera === -1 ? 0 : primera;
  });
  const [nota, setNota] = useState("");
  const [verGuia, setVerGuia] = useState(true);
  const [error, setError] = useState(false);

  const item = tarea.items[pos];
  const total = tarea.items.length;
  const hechas = Object.keys(etiquetas).length;

  useEffect(() => { setNota(etiquetas[item.id]?.nota ?? ""); }, [item.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const etiquetar = useCallback(async (label: boolean) => {
    setError(false);
    if (!(await guardarEtiqueta(id, item.id, label, nota))) { setError(true); return; }
    const nuevas = { ...etiquetas, [item.id]: { label, nota } };
    setEtiquetas(nuevas);
    if (Object.keys(nuevas).length === total && !hecho && (await guardarProgreso(id, true))) router.refresh();
    const siguiente = tarea.items.findIndex((it, k) => k > pos && !(it.id in nuevas));
    if (siguiente !== -1) setPos(siguiente);
    else if (pos < total - 1) setPos(pos + 1);
  }, [etiquetas, item.id, id, nota, pos, hecho, total, tarea.items, router]);

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

  const actual = etiquetas[item.id];

  return (
    <div className="anotar">
      <div className="md">
        <h1>{tarea.titulo}</h1>
        <p>
          Etiqueta cada salida <b>sin mirar</b> las etiquetas del autor. Tus etiquetas se guardan en tu cuenta.
          Atajos: <kbd>P</kbd> pasa, <kbd>N</kbd> no pasa, <kbd>←</kbd> <kbd>→</kbd> moverse.
        </p>
      </div>

      <button className="link-btn" onClick={() => setVerGuia(!verGuia)}>{verGuia ? "Ocultar la guía" : "Ver la guía"}</button>
      {verGuia && <div className="an-guia md" dangerouslySetInnerHTML={{ __html: tarea.guiaHtml }} />}

      <div className="an-barra mono">
        <span>{pos + 1} / {total}</span>
        <span>{hechas} anotadas</span>
        <div className="bar"><span style={{ width: `${(hechas / total) * 100}%` }} /></div>
      </div>

      <article className="an-item">
        <div className="an-campo"><span className="an-etq">CV</span><p>{item.cv}</p></div>
        <div className="an-campo"><span className="an-etq">Salida</span><p className="an-salida">{item.salida}</p></div>
        <p className="an-preg">{tarea.pregunta}</p>
        <textarea rows={2} placeholder="Nota (opcional): por qué, o tu duda" value={nota} onChange={(e) => setNota(e.target.value)} />
        <div className="an-botones">
          <button className={"btn an-pasa" + (actual?.label === true ? " sel" : "")} onClick={() => etiquetar(true)}>✓ Pasa</button>
          <button className={"btn an-nopasa" + (actual?.label === false ? " sel" : "")} onClick={() => etiquetar(false)}>✗ No pasa</button>
          <span className="an-nav">
            <button className="btn" disabled={pos === 0} onClick={() => setPos(pos - 1)} aria-label="Anterior">←</button>
            <button className="btn" disabled={pos === total - 1} onClick={() => setPos(pos + 1)} aria-label="Siguiente">→</button>
          </span>
        </div>
        {error && <span className="aviso">No se pudo guardar la etiqueta. Intenta de nuevo.</span>}
      </article>

      <div className="an-mapa">
        {tarea.items.map((it, k) => {
          const e = etiquetas[it.id];
          return (
            <button key={it.id} title={`#${it.id}`} onClick={() => setPos(k)}
                    className={"an-punto" + (k === pos ? " act" : "") + (e ? (e.label ? " ok" : " no") : "")}>
              {it.id}
            </button>
          );
        })}
      </div>

      <div className="foot">
        <span className="muted mono">
          {hechas === total ? "Tarea completa." : `Faltan ${total - hechas}.`}
          {hechas > 0 && (
            <>
              {" "}
              <a href={`/api/anotacion?nb=${encodeURIComponent(id)}`} download="mis_etiquetas.json">Descargar mis etiquetas (.json)</a>
            </>
          )}
        </span>
        <Flechas prev={prev} next={next} />
      </div>
    </div>
  );
}
