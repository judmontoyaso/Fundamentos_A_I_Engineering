"use client";
import { Monitor, Moon, Sun } from "lucide-react";
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
    <button
      type="button"
      className="tbtn"
      onClick={cambiar}
      title={tema === "light" ? "Tema claro" : tema === "dark" ? "Tema oscuro" : "Tema del sistema"}
      aria-label={`Cambiar tema (ahora: ${tema === "light" ? "claro" : tema === "dark" ? "oscuro" : "el del sistema"})`}
    >
      {tema === "light" ? <Sun size={16} aria-hidden /> : tema === "dark" ? <Moon size={16} aria-hidden /> : <Monitor size={16} aria-hidden />}
    </button>
  );
}
