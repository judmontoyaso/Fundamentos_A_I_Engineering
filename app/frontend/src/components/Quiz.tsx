// Autoevaluación de un módulo: cada respuesta se corrige al momento y explica por qué.
import { useEffect, useState } from "react";
import { api } from "../api";
import type { NavItem, Quiz as QuizT } from "../types";

type Props = {
  id: string;
  flat: NavItem[];
  done: boolean;
  onPassed: () => void;
  onNavigate: (id: string) => void;
};

const APROBADO = 0.8;

export function Quiz({ id, flat, done, onPassed, onNavigate }: Props) {
  const [quiz, setQuiz] = useState<QuizT | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elegidas, setElegidas] = useState<Record<number, number>>({});

  useEffect(() => {
    setQuiz(null);
    setElegidas({});
    api.quiz(id).then(setQuiz).catch((e: Error) => setError(e.message));
  }, [id]);

  const total = quiz?.preguntas.length ?? 0;
  const respondidas = Object.keys(elegidas).length;
  const aciertos = quiz ? quiz.preguntas.filter((p, i) => elegidas[i] === p.correcta).length : 0;
  const terminado = total > 0 && respondidas === total;
  const aprobado = terminado && aciertos / total >= APROBADO;

  useEffect(() => { if (aprobado && !done) onPassed(); }, [aprobado, done, onPassed]);

  if (error) return <p className="muted">No se pudo cargar la autoevaluación ({error}).</p>;
  if (!quiz) return <p className="muted">Cargando…</p>;

  const pos = flat.findIndex((it) => it.id === id);
  const prev = flat[pos - 1];
  const next = flat[pos + 1];

  return (
    <div className="quiz">
      <div className="md">
        <h1>Autoevaluación</h1>
        <p>
          {total} preguntas. Cada una se corrige al elegir y explica por qué: equivocarse aquí es parte de estudiar.
          Con {Math.round(APROBADO * 100)} % o más, el módulo queda marcado como completado.
        </p>
      </div>
      {quiz.preguntas.map((p, i) => {
        const elegida = elegidas[i];
        const respondida = elegida !== undefined;
        return (
          <section className="q" key={i}>
            <h3><span className="q-n mono">{i + 1}</span>{p.pregunta}</h3>
            <div className="q-ops">
              {p.opciones.map((op, j) => {
                let clase = "q-op";
                if (respondida && j === p.correcta) clase += " ok";
                else if (respondida && j === elegida) clase += " bad";
                return (
                  <button key={j} className={clase} disabled={respondida}
                          onClick={() => setElegidas((e) => ({ ...e, [i]: j }))}>
                    {op}
                  </button>
                );
              })}
            </div>
            {respondida && (
              <p className={"q-exp " + (elegida === p.correcta ? "ok" : "bad")}>
                <b>{elegida === p.correcta ? "Correcto." : "No."}</b> {p.explicacion}
              </p>
            )}
          </section>
        );
      })}
      <div className="foot">
        <div className="q-score">
          {terminado
            ? <><b className="mono">{aciertos}/{total}</b> {aprobado ? "· módulo completado" : "· repasa el manual y vuelve a intentarlo"}</>
            : <span className="muted mono">{respondidas}/{total} respondidas</span>}
          {respondidas > 0 && <button className="btn" onClick={() => setElegidas({})}>Reintentar</button>}
        </div>
        <div className="nav-arrows">
          {prev && <button className="btn" onClick={() => onNavigate(prev.id)}>← {prev.title}</button>}
          {next && <button className="btn" onClick={() => onNavigate(next.id)}>{next.title} →</button>}
        </div>
      </div>
    </div>
  );
}
