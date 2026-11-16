// Compila el contenido del curso (Markdown, scripts y autoevaluaciones de la raíz del repo)
// a JSON que la app importa solo en el servidor. Se ejecuta antes de `dev` y de `build`.
//
//   src/content/nav.js    cursos, grupos e ítems (sin contenido): lo único que llega al navegador
//   src/content/items.js  contenido de cada ítem, ya convertido a HTML
//   src/content/code.js   archivos de código por curso, para armar el .zip de descarga
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";

const WEB = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ROOT = process.env.COURSE_ROOT ? path.resolve(process.env.COURSE_ROOT) : path.resolve(WEB, "..");
const OUT = path.join(WEB, "src", "content");
const PUBLIC_INFOGRAFIAS = path.join(WEB, "public", "infografias");

const read = (p) => fs.readFileSync(p, "utf8");
const exists = (p) => fs.existsSync(p);
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function titulo(readme, fallback) {
  for (const line of read(readme).split(/\r?\n/)) if (line.startsWith("# ")) return line.slice(2).trim();
  return fallback;
}

function extraerResumen(md) {
  for (const raw of md.split(/\r?\n\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || line.startsWith(">") || line.startsWith("!") || line.startsWith("|") || line.startsWith("---")) continue;
    const limpio = line
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/[`*_]/g, "")
      .replace(/\s+/g, " ")
      .trim();
    if (limpio.length >= 40) return limpio.slice(0, 260);
  }
  return "";
}

function infografiaDeCurso(cursoId, meta) {
  if (meta.infografia) return meta.infografia;
  for (const ext of [".png", ".jpg", ".webp", ".svg"]) {
    const nombre = `${cursoId}-arquitectura${ext}`;
    if (exists(path.join(PUBLIC_INFOGRAFIAS, nombre))) return `/infografias/${nombre}`;
  }
  return undefined;
}

function leerMetaCurso(dir) {
  const p = path.join(dir, "curso.json");
  if (!exists(p)) return {};
  try {
    return JSON.parse(read(p));
  } catch {
    return {};
  }
}

function resaltar(code, lang) {
  const l = lang && hljs.getLanguage(lang) ? lang : null;
  return l ? hljs.highlight(code, { language: l }).value : esc(code);
}

function slug(text) {
  return text.toLowerCase().replace(/<[^>]+>/g, "").replace(/[^\p{L}\p{N}\s-]/gu, "").trim().replace(/\s+/g, "-");
}

// Links relativos del repo -> ruta del lector. `prefijo` es el del curso que se está compilando.
function destino(href, prefijo) {
  const low = href.toLowerCase();
  const m = low.match(/modulo-(\d+)/);
  if (!m) {
    const curso = low.match(/^(?:\.\.\/)*curso-([a-z0-9-]+)\/readme\.md/);
    if (!curso) return null;
    const pre = curso[1] === "ai-engineering" ? "" : `${curso[1]}-`;
    return `/leer/${pre}inicio`;
  }
  const curso = low.match(/curso-([a-z0-9-]+?)\//);
  const pre = curso ? (curso[1] === "ai-engineering" ? "" : `${curso[1]}-`) : prefijo && low.startsWith("../../") ? "" : prefijo;
  return `/leer/${pre}m${Number(m[1])}-${low.includes("ejercicios") ? "ejercicios" : "manual"}`;
}

function crearMarked(prefijo) {
  const m = new Marked(markedHighlight({ langPrefix: "hljs language-", highlight: resaltar }));
  m.setOptions({ gfm: true, breaks: false });
  m.use({
    renderer: {
      heading(text, level, raw) {
        return `<h${level} id="${slug(raw)}">${text}</h${level}>\n`;
      },
      table(header, body) {
        return `<div class="table-scroll"><table><thead>${header}</thead><tbody>${body}</tbody></table></div>\n`;
      },
      image(href, title, text) {
        if (!href) return "";
        const src = href.startsWith("/") || /^https?:/.test(href) ? href : `/infografias/${path.basename(href)}`;
        const alt = esc(text || title || "Infografía técnica");
        const cap = text ? `<figcaption>${esc(text)}</figcaption>` : "";
        return `<figure class="infografia"><img src="${esc(src)}" alt="${alt}" loading="lazy" />${cap}</figure>\n`;
      },
      link(href, title, text) {
        if (!href) return text;
        if (href.startsWith("#")) return `<a href="${esc(href)}">${text}</a>`;
        if (/^(https?:|mailto:)/.test(href)) return `<a href="${esc(href)}" target="_blank" rel="noopener">${text}</a>`;
        const d = destino(href, prefijo);
        return d ? `<a href="${d}">${text}</a>` : `<span class="ref">${text}</span>`; // archivo del repo: va en el .zip
      },
    },
  });
  return m;
}

// La presentación del curso principal habla de la app local: en la web esa sección no aplica.
function limpiarInicio(md) {
  return md.replace(/### La app del curso[\s\S]*?(?=\n### )/, "");
}

function primerDocstring(code) {
  const m = code.match(/"""([\s\S]*?)"""/);
  if (!m) return "";
  return m[1].trim().split(/\r?\n/).find((l) => l.trim())?.trim() ?? "";
}

function htmlLab(dir, cursoId, esGratis) {
  const enlaceZip = esGratis
    ? `Si estás probando la muestra gratis, <a href="/descargar/${cursoId}?muestra=1">descarga los scripts de este módulo inicial (.zip)</a> (con un plan activo también bajas <a href="/descargar/${cursoId}">el curso completo en .zip</a>).`
    : `<a href="/descargar/${cursoId}">Descarga el código completo del curso (.zip)</a>, instala las dependencias indicadas y ejecuta cada script en orden.`;
  const partes = [
    `<h1>Código del módulo</h1>`,
    `<p>Los scripts completos de este módulo están pensados para correrse en tu máquina. ${enlaceZip}</p>`,
  ];
  for (const f of fs.readdirSync(dir).filter((f) => f.endsWith(".py")).sort()) {
    const code = read(path.join(dir, f));
    const desc = primerDocstring(code);
    partes.push(`<h4><code>${esc(f)}</code></h4>`);
    if (desc) partes.push(`<p>${esc(desc)}</p>`);
    partes.push(`<pre><code class="hljs language-python">${resaltar(code.trimEnd(), "python")}</code></pre>`);
  }
  return partes.join("\n");
}

const CODE_EXT = new Set([".py", ".json", ".jsonl", ".txt", ".yml", ".yaml"]);
// anotacion.json SÍ va en el .zip: el script del Módulo 4 de Evals lo lee para comparar anotadores.
const NO_ZIP = new Set(["autoevaluacion.json", "curso.json"]);

function archivosDeCodigo(dir, rel = "", out = {}) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith(".") || e.name === "__pycache__" || e.name === "node_modules") continue;
    const abs = path.join(dir, e.name);
    const r = rel ? `${rel}/${e.name}` : e.name;
    if (e.isDirectory()) archivosDeCodigo(abs, r, out);
    else if (CODE_EXT.has(path.extname(e.name)) && !NO_ZIP.has(e.name)) out[r] = read(abs);
  }
  return out;
}

// ---------- descubrir cursos y módulos ----------
const dirAiEng = path.join(ROOT, "curso-ai-engineering");
if (!exists(dirAiEng) && exists(path.join(OUT, "nav.js"))) {
  console.log("contenido: usando src/content precompilado");
  process.exit(0);
}
const cursos = [{ id: "ai-engineering", dir: dirAiEng, prefijo: "", titulo: titulo(path.join(dirAiEng, "README.md"), "AI Engineering") }];
for (const d of fs.readdirSync(ROOT).filter((d) => d.startsWith("curso-") && d !== "curso-ai-engineering").sort()) {
  const dir = path.join(ROOT, d);
  if (exists(path.join(dir, "README.md"))) {
    const s = d.replace(/^curso-/, "");
    cursos.push({ id: s, dir, prefijo: `${s}-`, titulo: titulo(path.join(dir, "README.md"), s) });
  }
}

// Archivos base de curso-ai-engineering que reutilizan otros cursos dependientes
const BASE_AI_ENG = [
  "modulo-02-embeddings-busqueda-semantica/code/06_embeddings_reales.py",
  "modulo-04-bm25-hibrida-rrf/code/01_bm25_desde_cero.py",
  "modulo-05-workflows-agentes/code/00_comun.py",
  "modulo-05-workflows-agentes/code/03_paralelizacion.py",
  "modulo-07-observabilidad/code/00_trazador.py",
  "modulo-08-memoria-guardrails/code/02_memoria_largo_plazo.py",
  "modulo-08-memoria-guardrails/code/03_guardrails_entrada.py",
  "modulo-08-memoria-guardrails/code/04_guardrails_salida.py",
  "modulo-09-proyecto-integrador/code/00_datos_cvs.py",
  "modulo-09-proyecto-integrador/code/00_sistema.py",
];

const scriptsBase = new Map();
for (const rel of Object.keys(archivosDeCodigo(dirAiEng))) {
  if (!rel.endsWith(".py")) continue;
  const nombre = rel.split("/").pop();
  scriptsBase.set(nombre, [...(scriptsBase.get(nombre) ?? []), rel]);
}
function completarBase(archivos, cursoId) {
  const nombres = new Set(Object.keys(archivos).map((r) => r.split("/").pop()));
  for (let cambio = true; cambio; ) {
    cambio = false;
    for (const [ruta, texto] of Object.entries(archivos)) {
      if (!ruta.endsWith(".py")) continue;
      for (const m of texto.matchAll(/import_module\(\s*"([0-9a-z_]+)"\s*\)/g)) {
        const nombre = `${m[1]}.py`;
        if (nombres.has(nombre)) continue;
        const candidatos = scriptsBase.get(nombre) ?? [];
        if (candidatos.length !== 1) {
          console.warn(`contenido: ${cursoId}: ${ruta} importa ${nombre} y ${candidatos.length ? "hay varios con ese nombre" : "no existe"} en el curso base`);
          nombres.add(nombre);
          continue;
        }
        archivos[`_base/curso-ai-engineering/${candidatos[0]}`] = read(path.join(dirAiEng, candidatos[0]));
        nombres.add(nombre);
        cambio = true;
      }
    }
  }
}

const nav = { cursos: [], grupos: [] };
const items = {};
const code = {};

for (let ci = 0; ci < cursos.length; ci += 1) {
  const c = cursos[ci];
  const meta = leerMetaCurso(c.dir);
  const md = crearMarked(c.prefijo);
  const modulos = fs.readdirSync(c.dir).filter((d) => /^modulo-\d+-/.test(d) && exists(path.join(c.dir, d, "README.md"))).sort();
  const primerModuloN = modulos.length ? Number(modulos[0].match(/^modulo-(\d+)-/)[1]) : -1;
  const readmeRaw = read(path.join(c.dir, "README.md"));
  const mdInicio = limpiarInicio(readmeRaw);

  nav.cursos.push({
    id: c.id,
    titulo: c.titulo.replace(/\s*\(edición personal\)\s*/i, ""),
    modulos: modulos.length,
    orden: typeof meta.orden === "number" ? meta.orden : 50 + ci,
    etapa: meta.etapa ?? `Curso ${ci + 1}`,
    descripcion: meta.descripcion ?? extraerResumen(mdInicio),
    infografia: infografiaDeCurso(c.id, meta),
  });

  const add = (grupo, item, contenido, gratis = false) => {
    item.curso = c.id;
    item.gratis = gratis;
    grupo.items.push(item);
    items[item.id] = { ...item, ...contenido };
  };

  // La presentación y todo el primer módulo de cualquier curso son gratuitos por convención.
  const inicio = { curso: c.id, grupo: "Inicio", items: [] };
  add(inicio, { id: `${c.prefijo}inicio`, titulo: "Presentación del curso", tipo: "md" }, { html: md.parse(mdInicio) }, true);
  nav.grupos.push(inicio);

  for (const carpeta of modulos) {
    const n = Number(carpeta.match(/^modulo-(\d+)-/)[1]);
    const esGratis = n === primerModuloN;
    const dir = path.join(c.dir, carpeta);
    const grupo = { curso: c.id, grupo: titulo(path.join(dir, "README.md"), `Módulo ${n}`), items: [] };
    const id = (s) => `${c.prefijo}m${n}-${s}`;

    add(grupo, { id: id("manual"), titulo: "Manual", tipo: "md" }, { html: md.parse(read(path.join(dir, "README.md"))) }, esGratis);
    if (exists(path.join(dir, "ejercicios.md")))
      add(grupo, { id: id("ejercicios"), titulo: "Ejercicios", tipo: "md" }, { html: md.parse(read(path.join(dir, "ejercicios.md"))) }, esGratis);
    const codeDir = path.join(dir, "code");
    if (exists(codeDir) && fs.readdirSync(codeDir).some((f) => f.endsWith(".py")))
      add(grupo, { id: id("lab"), titulo: "Código del módulo", tipo: "lab" }, { html: htmlLab(codeDir, c.id, esGratis) }, esGratis);
    if (exists(path.join(dir, "anotacion.json"))) {
      const a = JSON.parse(read(path.join(dir, "anotacion.json")));
      add(grupo, { id: id("anotar"), titulo: "Anotar (tu turno)", tipo: "anotar" },
        { tarea: { titulo: a.titulo, pregunta: a.pregunta, guiaHtml: md.parse(a.guia), items: a.items } }, esGratis);
    }
    if (exists(path.join(dir, "autoevaluacion.json")))
      add(grupo, { id: id("quiz"), titulo: "Autoevaluación", tipo: "quiz" },
        { preguntas: JSON.parse(read(path.join(dir, "autoevaluacion.json"))).preguntas }, esGratis);
    nav.grupos.push(grupo);
  }

  // Código descargable del curso (+ dependencias explícitas en _base/ cuando aplica).
  code[c.id] = {};
  archivosDeCodigo(c.dir, "", code[c.id]);
  const deps = new Set(Array.isArray(meta.dependencias) ? meta.dependencias : []);
  if (deps.has("ai-engineering")) {
    for (const rel of BASE_AI_ENG) {
      const abs = path.join(dirAiEng, rel);
      if (exists(abs)) code[c.id][`_base/curso-ai-engineering/${rel}`] = read(abs);
    }
  }
  if (deps.has("evals")) {
    const evComun = path.join(ROOT, "curso-evals", "comun", "ev_comun.py");
    if (exists(evComun)) code[c.id]["_base/curso-evals/comun/ev_comun.py"] = read(evComun);
  }
  if (deps.size > 0) completarBase(code[c.id], c.id);
}

// Ordenar cursos según `orden` para que portada, cuenta y sitemap compartan exactamente la misma secuencia.
nav.cursos.sort((a, b) => (a.orden ?? 99) - (b.orden ?? 99));

fs.mkdirSync(OUT, { recursive: true });
const emitir = (nombre, datos, tipo) => {
  fs.writeFileSync(path.join(OUT, `${nombre}.js`), `export default ${JSON.stringify(datos)};\n`);
  fs.writeFileSync(path.join(OUT, `${nombre}.d.ts`), `declare const d: ${tipo};\nexport default d;\n`);
};
emitir("nav", nav, 'import("../lib/tipos").Nav');
emitir("items", items, 'Record<string, import("../lib/tipos").ItemContenido>');
emitir("code", code, "Record<string, Record<string, string>>");

const kb = (f) => Math.round(fs.statSync(path.join(OUT, f)).size / 1024);
console.log(`contenido: ${nav.cursos.length} cursos, ${Object.keys(items).length} ítems ` +
  `(nav ${kb("nav.js")} KB, items ${kb("items.js")} KB, código ${kb("code.js")} KB)`);
