"use client";
// HTML de una lección (ya convertido en el servidor). Añade "copiar" a los bloques de código,
// visor ampliado al hacer clic en infografías, un índice lateral "En esta lección" en pantallas anchas
// y navegación fluida entre lecciones.
import { X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type MouseEvent } from "react";

type Seccion = { id: string; texto: string };

const slug = (t: string) =>
  t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);

export function Prosa({ html }: { html: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const [zoom, setZoom] = useState<{ src: string; alt: string } | null>(null);
  const [secciones, setSecciones] = useState<Seccion[]>([]);
  const [activa, setActiva] = useState<string>("");

  // Botón de copiar en cada bloque de código.
  useEffect(() => {
    ref.current?.querySelectorAll("pre").forEach((pre) => {
      if (pre.querySelector(".copiar")) return;
      const b = document.createElement("button");
      b.className = "copiar";
      b.type = "button";
      b.textContent = "Copiar";
      b.setAttribute("aria-label", "Copiar el código");
      b.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(pre.querySelector("code")?.textContent ?? "");
          b.textContent = "Copiado";
        } catch {
          b.textContent = "No se pudo copiar";
        }
        setTimeout(() => { b.textContent = "Copiar"; }, 1500);
      });
      pre.appendChild(b);
    });
  }, [html]);

  // Índice de la lección a partir de los h2, y sección activa según el scroll.
  useEffect(() => {
    const raiz = ref.current;
    if (!raiz) return;
    const usados = new Set<string>();
    const hs = [...raiz.querySelectorAll("h2")];
    const lista = hs.map((h) => {
      let id = h.id || slug(h.textContent ?? "") || "seccion";
      while (usados.has(id)) id += "-2";
      usados.add(id);
      h.id = id;
      return { id, texto: (h.textContent ?? "").replace(/^\d+\.\s*/, "") };
    });
    setSecciones(lista.length >= 3 ? lista : []);
    if (lista.length < 3) return;
    // Sección activa: la última cuyo título ya pasó el primer tercio de la ventana de lectura.
    // El contenedor y los títulos se resuelven en vivo: React puede reemplazarlos después de este efecto.
    let pendiente = false;
    const calcular = () => {
      pendiente = false;
      const scroller = ref.current?.closest(".scroll") as HTMLElement | null;
      if (!scroller) return;
      const corte = scroller.getBoundingClientRect().top + scroller.clientHeight / 3;
      // Se consultan en cada cálculo: si React vuelve a pintar el HTML, los nodos anteriores quedan desconectados.
      const vivos = [...(ref.current?.querySelectorAll("h2") ?? [])];
      let actual = vivos[0]?.id ?? "";
      for (const h of vivos) {
        if (h.getBoundingClientRect().top <= corte) actual = h.id;
        else break;
      }
      setActiva(actual);
    };
    const alMover = () => {
      if (!pendiente) { pendiente = true; requestAnimationFrame(calcular); }
    };
    calcular();
    // El evento scroll no burbujea, pero sí se ve en la fase de captura del documento.
    document.addEventListener("scroll", alMover, { capture: true, passive: true });
    return () => document.removeEventListener("scroll", alMover, { capture: true });
  }, [html]);

  useEffect(() => {
    if (!zoom) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setZoom(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [zoom]);

  function onClick(e: MouseEvent<HTMLDivElement>) {
    const target = e.target as HTMLElement;
    const img = target.closest("figure.infografia img") as HTMLImageElement | null;
    if (img) {
      setZoom({ src: img.src, alt: img.alt });
      return;
    }
    const a = target.closest("a");
    const href = a?.getAttribute("href") ?? "";
    if (href.startsWith("/leer/") && !e.metaKey && !e.ctrlKey) {
      e.preventDefault();
      router.push(href);
      return;
    }
    // Enlaces internos del índice que trae el propio manual (#1-que-es): desplazamiento suave dentro del lector.
    if (href.startsWith("#") && href.length > 1) {
      const destino = ref.current?.querySelector(`[id="${CSS.escape(href.slice(1))}"], [name="${CSS.escape(href.slice(1))}"]`);
      if (destino) {
        e.preventDefault();
        destino.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }

  function ir(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <>
      {secciones.length > 0 && (
        <nav className="toc" aria-label="En esta lección">
          <p className="toc-titulo">En esta lección</p>
          <ol>
            {secciones.map((s) => (
              <li key={s.id}>
                <button type="button" className={s.id === activa ? "activa" : undefined} onClick={() => ir(s.id)}
                        aria-current={s.id === activa ? "location" : undefined}>
                  {s.texto}
                </button>
              </li>
            ))}
          </ol>
        </nav>
      )}
      <div className="md" ref={ref} onClick={onClick} dangerouslySetInnerHTML={{ __html: html }} />
      {zoom && (
        <div className="lightbox" role="dialog" aria-modal="true" aria-label={zoom.alt} onClick={() => setZoom(null)}>
          <div className="lightbox-bar">
            <span>{zoom.alt}</span>
            <button type="button" className="btn" onClick={() => setZoom(null)}>
              <X size={16} aria-hidden /> Cerrar
            </button>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={zoom.src} alt={zoom.alt} onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </>
  );
}
