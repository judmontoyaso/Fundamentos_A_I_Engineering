import type { Metadata, Viewport } from "next";
import "./base.css";
import "./sitio.css";

const SITIO = process.env.NEXT_PUBLIC_NOMBRE_SITIO ?? "IA en Producción";

export const metadata: Metadata = {
  title: { default: SITIO, template: `%s · ${SITIO}` },
  description:
    "Cuatro cursos en español para pasar de un demo de LLM a software en producción: AI Engineering, Evals, AI Search y Agentes en Producción.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1 };

// Aplica el tema guardado antes de pintar, para que no parpadee.
const TEMA = `try{var t=localStorage.getItem("curso_tema");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
        />
        <script dangerouslySetInnerHTML={{ __html: TEMA }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
