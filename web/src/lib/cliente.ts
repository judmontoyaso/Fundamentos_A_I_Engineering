// Llamadas del navegador a la API propia.
async function post(url: string, body: unknown): Promise<boolean> {
  try {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return r.ok;
  } catch {
    return false;
  }
}

export const guardarProgreso = (id: string, hecho: boolean, respuestas?: number[]) =>
  post("/api/progreso", respuestas ? { id, hecho, respuestas } : { id, hecho });
export const guardarEtiqueta = (nb: string, item: string, label: boolean, nota: string) =>
  post("/api/anotacion", { nb, item, label, nota });
