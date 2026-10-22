// Celda de código: editor CodeMirror + ejecución en el kernel del backend.
import { useMemo, useRef, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorView, keymap } from "@codemirror/view";
import { Prec } from "@codemirror/state";
import { api } from "../api";
import { toast } from "../toast";
import type { Cell, RunResult } from "../types";

const editorLook = EditorView.theme({
  "&": { fontSize: "0.83rem", backgroundColor: "var(--code-bg)" },
  ".cm-content, .cm-gutters": { fontFamily: '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace' },
  ".cm-gutters": { backgroundColor: "var(--code-bg)", borderRight: "1px solid rgba(255,255,255,.06)" },
});

type Props = { cell: Cell; nbId: string; onReload: () => void };

export function CodeCell({ cell, nbId, onReload }: Props) {
  const [code, setCode] = useState(cell.source);
  const [output, setOutput] = useState<RunResult | null>(null);
  const [running, setRunning] = useState(false);
  const saveTimer = useRef<number | undefined>(undefined);
  const runRef = useRef<() => void>(() => {});

  const runnable = Boolean(cell.runnable);
  const isPython = cell.lang === "python" || cell.lang === "py";

  async function run() {
    if (running) return;
    setRunning(true);
    setOutput(null);
    try {
      setOutput(await api.run(nbId, code, cell.file));
    } catch (e) {
      setOutput({ stdout: "", stderr: `No se pudo contactar la API: ${(e as Error).message}`, result: null, timed_out: false });
    } finally {
      setRunning(false);
    }
  }
  runRef.current = run;

  function onChange(value: string) {
    setCode(value);
    if (!runnable) return;
    window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      api.saveCell(nbId, cell.idx, value).catch(() => toast("No se pudo guardar la edición"));
    }, 700);
  }

  async function restoreOriginal() {
    await api.resetCell(nbId, cell.idx);
    onReload();
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      toast("Copiado");
    } catch {
      toast("No se pudo copiar");
    }
  }

  const extensions = useMemo(() => {
    const ext = [editorLook, EditorView.lineWrapping];
    if (isPython) ext.push(python());
    if (runnable) {
      ext.push(Prec.highest(keymap.of([{ key: "Mod-Enter", run: () => { runRef.current(); return true; } }])));
    }
    return ext;
  }, [isPython, runnable]);

  const hasOutput = output && (output.stdout || output.stderr || output.result !== null || output.timed_out);

  return (
    <div className={"cell" + (runnable ? "" : " readonly")}>
      <div className="cell-head">
        <span className="cell-lang">{cell.lang}</span>
        {cell.fragment && <span className="cell-lang muted">· fragmento · solo lectura</span>}
        {cell.edited && <span className="cell-badge">editada</span>}
        <div className="cell-actions">
          {runnable ? (
            <>
              <button className="cbtn run" disabled={running} onClick={run} title="Ejecutar (Ctrl/Cmd+Enter)">
                {running ? "⏳ ejecutando" : "▶ ejecutar"}
              </button>
              {cell.edited && (
                <button className="cbtn" onClick={restoreOriginal} title="Volver al código del curso">↺ original</button>
              )}
            </>
          ) : (
            <button className="cbtn" onClick={copy}>copiar</button>
          )}
        </div>
      </div>

      <CodeMirror
        value={code}
        onChange={onChange}
        theme={oneDark}
        extensions={extensions}
        editable={runnable}
        readOnly={!runnable}
        basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: runnable, highlightActiveLineGutter: runnable }}
      />

      {hasOutput && (
        <div className="cell-out">
          {output.stdout && <pre>{output.stdout}</pre>}
          {output.stderr && (
            // Rojo solo para errores reales; avisos y logs de librerías van en ámbar.
            <pre className={output.stderr.includes("Traceback (most recent call last)") ? "err" : "warn"}>
              {output.stderr}
            </pre>
          )}
          {output.result !== null && <pre className="result">{output.result}</pre>}
          {output.timed_out && (
            <div className="meta timeout">⏱ La celda superó el tiempo límite (KERNEL_TIMEOUT, 300 s por defecto) y sigue corriendo en segundo plano.</div>
          )}
        </div>
      )}
    </div>
  );
}
