"use client";
// HTML de una lección (ya convertido en el servidor). Añade "copiar" a los bloques de código
// y hace que los links a otras lecciones naveguen sin recargar la página.
import { useRouter } from "next/navigation";
import { useEffect, useRef, type MouseEvent } from "react";

export function Prosa({ html }: { html: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    ref.current?.querySelectorAll("pre").forEach((pre) => {
      if (pre.querySelector(".copiar")) return;
      const b = document.createElement("button");
      b.className = "copiar";
      b.type = "button";
      b.textContent = "copiar";
      b.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(pre.querySelector("code")?.textContent ?? "");
          b.textContent = "copiado";
        } catch {
          b.textContent = "no se pudo";
        }
        setTimeout(() => { b.textContent = "copiar"; }, 1500);
      });
      pre.appendChild(b);
    });
  }, [html]);

  function onClick(e: MouseEvent<HTMLDivElement>) {
    const a = (e.target as HTMLElement).closest("a");
    const href = a?.getAttribute("href") ?? "";
    if (href.startsWith("/leer/") && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      router.push(href);
    }
  }

  return <div className="md" ref={ref} onClick={onClick} dangerouslySetInnerHTML={{ __html: html }} />;
}
