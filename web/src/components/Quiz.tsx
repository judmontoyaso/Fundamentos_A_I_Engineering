"use client";
// Autoevaluación de un módulo: cada respuesta se corrige al momento y explica por qué.
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { guardarProgreso } from "@/lib/cliente";
import type { ItemNav, Pregunta } from "@/lib/tipos";
import { Flechas } from "./Pie";

type Props = { id: string; preguntas: Pregunta[]; hecho: boolean; conSesion: boolean; prev?: ItemNav; next?: ItemNav };

const APROBADO = 0.8;

export function Quiz({ id, preguntas, hecho, conSesion, prev, next }: Props) {
  const router = useRouter();
  const [elegidas, setElegidas] = useState<Record<number, number>>({});
  const guardado = useRef(hecho);

  const total = preguntas.length;
  const respondidas = Object.keys(elegidas).length;
  const aciertos = preguntas.filter((p, i) => elegidas[i] === p.correcta).length;
  const terminado = total > 0 && respondidas === total;
  const aprobado = terminado && aciertos / total >= APROBADO;

  useEffect(() => {
    if (!aprobado || guardado.current || !conSesion) return;
    guardado.current = true;
    const respuestas = preguntas.map((_, i) => elegidas[i] ?? -1);
    guardarProgreso(id, true, respuestas).then((ok) => { if (ok) router.refresh(); else guardado.current = false; });
  }, [aprobado, conSesion, elegidas, id, preguntas, router]);

  return (
    <div className="quiz">
      <div className="md">
        <h1>Autoevaluación</h1>
        <p>
          {total} preguntas. Cada una se corrige al elegir y explica por qué: equivocarse aquí es parte de estudiar.
          Con {Math.round(APROBADO * 100)} % o más, el módulo queda marcado como completado.
        </p>
      </div>
      {preguntas.map((p, i) => {
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
        <Flechas prev={prev} next={next} />
      </div>
    </div>
  );
}
