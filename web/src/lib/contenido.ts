// Acceso al contenido compilado. Solo servidor: el HTML de las lecciones de pago nunca entra al bundle del navegador.
import "server-only";
import nav from "@/content/nav";
import items from "@/content/items";
import type { GrupoNav, ItemContenido, ItemNav } from "./tipos";

export const cursos = nav.cursos;
export const grupos = nav.grupos;

export function item(id: string): ItemContenido | null {
  return Object.prototype.hasOwnProperty.call(items, id) ? items[id] : null;
}
export function curso(id: string) {
  return cursos.find((c) => c.id === id) ?? null;
}
export function gruposDe(cursoId: string): GrupoNav[] {
  return grupos.filter((g) => g.curso === cursoId);
}
export function itemsDe(cursoId: string): ItemNav[] {
  return gruposDe(cursoId).flatMap((g) => g.items);
}
