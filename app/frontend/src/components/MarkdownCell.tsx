// Celda de prosa: Markdown del curso renderizado, con navegación interna.
import { useEffect, useMemo, useRef, type MouseEvent } from "react";
import { marked } from "marked";
import { toast } from "../toast";

marked.setOptions({ gfm: true, breaks: false });

// Links relativos del repo -> id de notebook de la app.
function linkToNotebook(href: string): string | null {
  const low = href.toLowerCase();
  const m = low.match(/modulo-0(\d)/);
  if (!m) return null;
  return `m${m[1]}-${low.includes("ejercicios") ? "ejercicios" : "manual"}`;
}

type Props = { source: string; onNavigate: (id: string) => void };

export function MarkdownCell({ source, onNavigate }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const htmlStr = useMemo(() => marked.parse(source, { async: false }) as string, [source]);

  useEffect(() => {
    // tablas con scroll horizontal propio
    ref.current?.querySelectorAll("table").forEach((t) => {
      if (t.parentElement?.classList.contains("table-scroll")) return;
      const w = document.createElement("div");
      w.className = "table-scroll";
      t.parentNode?.insertBefore(w, t);
      w.appendChild(t);
    });
  }, [htmlStr]);

  function onClick(e: MouseEvent<HTMLDivElement>) {
    const a = (e.target as HTMLElement).closest("a");
    if (!a) return;
    const href = a.getAttribute("href") ?? "";
    if (href.startsWith("#")) {
      e.preventDefault();
      const name = href.slice(1);
      document.querySelector(`[name="${CSS.escape(name)}"], #${CSS.escape(name)}`)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (/^https?:\/\//.test(href)) {
      a.target = "_blank";
      a.rel = "noopener";
    } else {
      e.preventDefault();
      const id = linkToNotebook(href);
      if (id) onNavigate(id);
      else toast(`Ese archivo vive en tu carpeta del proyecto: ${href}`);
    }
  }

  return <div className="md" ref={ref} onClick={onClick} dangerouslySetInnerHTML={{ __html: htmlStr }} />;
}
