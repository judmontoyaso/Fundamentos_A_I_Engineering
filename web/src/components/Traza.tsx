"use client";
// La traza de una ejecución real del laboratorio 1 del curso de agentes (VAC-101, modelo simulado).
// Es la pieza que da identidad a la portada: lo que se enseña aquí es a medir lo que hace un sistema.
// Se escribe paso a paso una sola vez al cargar; con "reducir movimiento" aparece completa.
import { Check, X } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

const PASOS: { n: string; llamada: string; resultado: string; tono?: "ok" | "no" }[] = [
  { n: "1", llamada: "obtener_vacante(VAC-101)", resultado: "Senior AI Engineer, híbrido en Bogotá" },
  { n: "2", llamada: "buscar_candidatos(4 requisitos, hasta 6.500 USD)", resultado: "4 encontrados" },
  { n: "3–4", llamada: "verificar_elegibilidad(CAND-01)", resultado: "elegible", tono: "ok" },
  { n: "5–6", llamada: "verificar_elegibilidad(CAND-03)", resultado: "elegible", tono: "ok" },
  { n: "7–8", llamada: "verificar_elegibilidad(CAND-04)", resultado: "1 año de experiencia, inglés A2", tono: "no" },
  { n: "9–10", llamada: "verificar_elegibilidad(CAND-07)", resultado: "inglés B1, vive en Medellín", tono: "no" },
  { n: "11", llamada: "entregar_terna", resultado: "CAND-01 y CAND-03", tono: "ok" },
];

const MEDIDOR = [
  { k: "Pasos", v: "11" },
  { k: "Tokens", v: "16.446" },
  { k: "Costo", v: "0,0069 USD" },
  { k: "Terna", v: "exacta", ok: true },
];

export function Traza() {
  const quieto = useReducedMotion();
  const aparece = (i: number) =>
    quieto
      ? {}
      : {
          initial: { opacity: 0, y: 6 },
          animate: { opacity: 1, y: 0 },
          transition: { delay: 0.25 + i * 0.16, duration: 0.32, ease: [0.2, 0.7, 0.2, 1] as const },
        };

  return (
    <figure className="traza" aria-label="Traza de una ejecución del agente del curso">
      <figcaption className="traza-cab">
        <span>Agente de preselección, vacante VAC-101</span>
        <span className="traza-fuente">laboratorio 1, curso de agentes</span>
      </figcaption>
      <ol className="traza-pasos">
        {PASOS.map((p, i) => (
          <motion.li key={p.n} className={p.tono ? `t-${p.tono}` : undefined} {...aparece(i)}>
            <span className="t-n">{p.n}</span>
            <code>{p.llamada}</code>
            <span className="t-r">
              {p.tono === "ok" && <Check aria-hidden size={14} strokeWidth={2.5} />}
              {p.tono === "no" && <X aria-hidden size={14} strokeWidth={2.5} />}
              {p.resultado}
            </span>
          </motion.li>
        ))}
      </ol>
      <motion.dl className="traza-medidor" {...aparece(PASOS.length + 0.5)}>
        {MEDIDOR.map((m) => (
          <div key={m.k} className={m.ok ? "t-ok" : undefined}>
            <dt>{m.k}</dt>
            <dd>{m.v}</dd>
          </div>
        ))}
      </motion.dl>
    </figure>
  );
}
