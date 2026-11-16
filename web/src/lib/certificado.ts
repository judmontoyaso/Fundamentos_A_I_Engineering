// Emisión y verificación de certificados de finalización de curso.
// El código del certificado lleva los datos firmados con HMAC-SHA256 (secreto del servidor)
// y además se comprueba contra el progreso real guardado en la base de datos.
import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";
import { curso, itemsDe } from "./contenido";
import { secretoServidor } from "./secreto";
import { store } from "./store";
import type { Progreso, Usuario } from "./tipos";

export type DatosCertificado = {
  u: string;       // user_id
  c: string;       // curso_id
  n: string;       // nombre para mostrar
  f: string;       // fecha ISO (YYYY-MM-DD)
};

function firmar(payloadB64: string): string {
  return createHmac("sha256", secretoServidor()).update(`cert:${payloadB64}`).digest("base64url").slice(0, 22);
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
  if (codigo.toUpperCase().startsWith("IAP-")) {
    try { return await verificarIdCorto(codigo); } catch { return null; }
  }
  const partes = codigo.split(".");
  if (partes.length !== 2) return null;
  const [payload, firma] = partes;
  let esperada: string;
  try {
    esperada = firmar(payload);
  } catch {
    return null; // sin secreto de servidor en producción no se valida ningún certificado
  }
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

  return armar(datos.u, datos.c, datos.n, datos.f);
}

/** Identificador corto y estable de un certificado: IAP-<CURSO>-<10 hex>. Es el que va en el QR y en el PDF. */
export function idCertificado(userId: string, cursoId: string): string {
  const hash = createHmac("sha256", secretoServidor()).update(`${userId}:${cursoId}`).digest("hex").slice(0, 10).toUpperCase();
  return `IAP-${cursoId.toUpperCase()}-${hash}`;
}

async function armar(userId: string, cursoId: string, nombre: string, fechaRespaldo: string) {
  const infoCurso = curso(cursoId)!;
  const items = itemsDe(cursoId);
  // La fecha es la de la última unidad completada, así el certificado no cambia cada día que se abre.
  const fecha = (await store.fechaCompletado(userId, items.map((i) => i.id)).catch(() => null)) ?? fechaRespaldo;
  return {
    valido: true,
    idVerificacion: idCertificado(userId, cursoId),
    nombre,
    cursoId,
    cursoTitulo: infoCurso.titulo,
    modulos: infoCurso.modulos,
    lecciones: items.length,
    quizzes: items.filter((i) => i.tipo === "quiz").length,
    fecha,
  };
}

/** Resuelve un identificador corto buscando la cuenta cuyo HMAC coincide (comparación en tiempo constante). */
async function verificarIdCorto(codigo: string) {
  const m = /^IAP-([A-Z0-9-]+)-([0-9A-F]{10})$/.exec(codigo.toUpperCase());
  if (!m) return null;
  const cursoId = m[1].toLowerCase();
  if (!curso(cursoId)) return null;
  const buscado = Buffer.from(`IAP-${m[1]}-${m[2]}`);
  for (const u of await store.usuariosRecientes(10000)) {
    if (u.unidadesHechas === 0) continue;
    const propio = Buffer.from(idCertificado(u.id, cursoId));
    if (propio.length !== buscado.length || !timingSafeEqual(propio, buscado)) continue;
    if (!cursoCompletado(cursoId, await store.progreso(u.id))) return null;
    return armar(u.id, cursoId, u.nombre?.trim() || u.email.split("@")[0], new Date().toISOString().slice(0, 10));
  }
  return null;
}
