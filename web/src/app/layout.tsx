import { Toaster } from "sonner";
import type { Metadata, Viewport } from "next";
import { cursos } from "@/lib/contenido";
import { NOMBRE_SITIO, urlSitioPublico } from "@/lib/sitio";
import "./base.css";
import "./sitio.css";

const BASE = urlSitioPublico();
const MODULOS = cursos.reduce((n, c) => n + c.modulos, 0);
const DESCRIPCION =
  `Cursos de ingeniería de IA en español para construir, evaluar y llevar a producción sistemas con modelos de lenguaje. ${cursos.length} cursos y ${MODULOS} módulos con código en Python y certificado verificable.`;

export const metadata: Metadata = {
  metadataBase: new URL(BASE),
  title: { default: `${NOMBRE_SITIO} · Cursos técnicos de AI Engineering, Evals, RAG y Agentes`, template: `%s · ${NOMBRE_SITIO}` },
  description: DESCRIPCION,
  keywords: [
    "AI Engineering en español",
    "curso de inteligencia artificial aplicada",
    "evaluación de LLMs",
    "Evals para AI Engineers",
    "RAG en producción",
    "AI Search",
    "agentes de IA en producción",
    "MCP Model Context Protocol",
    "LangGraph en español",
    "Python LLM",
  ],
  authors: [{ name: NOMBRE_SITIO }],
  creator: NOMBRE_SITIO,
  publisher: NOMBRE_SITIO,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    locale: "es_CO",
    url: "/",
    siteName: NOMBRE_SITIO,
    title: `${NOMBRE_SITIO}: cursos de ingeniería de IA en español`,
    description: DESCRIPCION,
  },
  twitter: {
    card: "summary_large_image",
    title: `${NOMBRE_SITIO}: cursos de ingeniería de IA en español`,
    description: DESCRIPCION,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
      "max-video-preview": -1,
    },
  },
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
          href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,300;0,400;0,500;0,700;1,300;1,400&family=Roboto+Mono:wght@400;500&display=swap"
        />
        <script dangerouslySetInnerHTML={{ __html: TEMA }} />
      </head>
      <body>
        {children}
        <Toaster position="bottom-center" richColors closeButton />
      </body>
    </html>
  );
}
