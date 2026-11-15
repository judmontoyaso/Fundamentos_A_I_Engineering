// Emisión y verificación de certificados de finalización de curso.
// El código del certificado lleva los datos firmados con HMAC-SHA256 (secreto del servidor)
// y además se comprueba contra el progreso real guardado en la base de datos.
import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";
import { curso, itemsDe } from "./contenido";
import { store } from "./store";
import type { Progreso, Usuario } from "./tipos";

export type DatosCertificado = {
  u: string;       // user_id
  c: string;       // curso_id
  n: string;       // nombre para mostrar
  f: string;       // fecha ISO (YYYY-MM-DD)
};

function secreto(): string {
  return process.env.AUTH0_SECRET || process.env.SERVICE_ROLE || process.env.SUPABASE_SERVICE_ROLE_KEY || "dev-secret-ia-en-produccion";
}

function firmar(payloadB64: string): string {
  return createHmac("sha256", secreto()).update(`cert:${payloadB64}`).digest("base64url").slice(0, 22);
}

export function cursoCompletado(cursoId: string, progreso: Progreso): boolean {
  const lecciones = itemsDe(cursoId);
  return lecciones.length > 0 && lecciones.every((i) => Boolean(progreso[i.id]));
}

export function emitirCodigoCertificado(usuario: Usuario, cursoId: string, fecha = new Date().toISOString().slice(0, 10)): string {
  const datos: DatosCertificado = {
    u: usuario.id,
    c: cursoId,
    n: (usuario.nombre?.trim() || usuario.email.split("@")[0]),
    f: fecha,
  };
  const payload = Buffer.from(JSON.stringify(datos), "utf8").toString("base64url");
  return `${payload}.${firmar(payload)}`;
}

export async function verificarCertificado(codigo: string): Promise<{
  valido: boolean;
  esEjemplo?: boolean;
  idVerificacion: string;
  nombre: string;
  cursoId: string;
  cursoTitulo: string;
  modulos: number;
  lecciones: number;
  quizzes: number;
  fecha: string;
} | null> {
  if (codigo === "ejemplo") {
    const info = curso("ai-engineering")!;
    const items = itemsDe("ai-engineering");
    return {
      valido: true,
      esEjemplo: true,
      idVerificacion: "IAP-AI-ENGINEERING-DEMO2026",
      nombre: "Estudiante de Ejemplo",
      cursoId: "ai-engineering",
      cursoTitulo: info.titulo,
      modulos: info.modulos,
      lecciones: items.length,
      quizzes: items.filter((i) => i.tipo === "quiz").length,
      fecha: new Date().toISOString().slice(0, 10),
    };
  }
  const partes = codigo.split(".");
  if (partes.length !== 2) return null;
  const [payload, firma] = partes;
  const esperada = firmar(payload);
  const a = Buffer.from(esperada);
  const b = Buffer.from(firma);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;

  let datos: DatosCertificado;
  try {
    datos = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
  } catch {
    return null;
  }
  const infoCurso = curso(datos.c);
  if (!infoCurso || !datos.u || !datos.n) return null;

  const progreso = await store.progreso(datos.u);
  if (!cursoCompletado(datos.c, progreso)) return null;

  const items = itemsDe(datos.c);
  const quizzes = items.filter((i) => i.tipo === "quiz").length;
  const hashCorto = createHmac("sha256", secreto()).update(`${datos.u}:${datos.c}`).digest("hex").slice(0, 10).toUpperCase();

  return {
    valido: true,
    idVerificacion: `IAP-${datos.c.toUpperCase()}-${hashCorto}`,
    nombre: datos.n,
    cursoId: datos.c,
    cursoTitulo: infoCurso.titulo,
    modulos: infoCurso.modulos,
    lecciones: items.length,
    quizzes,
    fecha: datos.f,
  };
}
