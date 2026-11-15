"use client";
import { useEffect, useState } from "react";

type Tema = "system" | "light" | "dark";
const TEMAS: Tema[] = ["system", "light", "dark"];

export function TemaBtn() {
  const [tema, setTema] = useState<Tema>("system");

  useEffect(() => {
    try {
      const t = localStorage.getItem("curso_tema");
      if (t === "light" || t === "dark") setTema(t);
    } catch { /* almacenamiento bloqueado */ }
  }, []);

  function cambiar() {
    const t = TEMAS[(TEMAS.indexOf(tema) + 1) % 3];
    setTema(t);
    if (t === "system") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("curso_tema", t); } catch { /* idem */ }
  }

  return (
    <button type="button" className="tbtn" onClick={cambiar} title="Cambiar tema (sistema / claro / oscuro)" aria-label="Cambiar tema">
      {tema === "light" ? "☀" : tema === "dark" ? "☾" : "◐"}
    </button>
  );
}
