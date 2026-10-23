// Cliente HTTP de la API del curso. Toda la comunicación con el backend pasa por aquí.
import type {
  Consulta, EstadoAsistente, NavGroup, Notebook, Progress, Quiz, Recuerdo, RunResult,
} from "./types";

export const API_URL = (import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().then((b) => b?.detail, () => null);
    throw new Error(typeof detail === "string" ? detail : `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
}

export const api = {
  modules: () => request<{ nav: NavGroup[]; progress: Progress }>("/modules"),
  notebook: (id: string) => request<Notebook>(`/notebook/${encodeURIComponent(id)}`),
  run: (sessionId: string, code: string, file?: string) =>
    post<RunResult>("/run", { session_id: sessionId, code, file }),
  resetSession: (sessionId: string) => post<{ ok: boolean }>(`/session/${encodeURIComponent(sessionId)}/reset`),
  saveCell: (nbId: string, cellIdx: number, source: string) =>
    post<{ ok: boolean }>("/cell/save", { nb_id: nbId, cell_idx: cellIdx, source }),
  resetCell: (nbId: string, cellIdx: number) =>
    post<{ ok: boolean }>("/cell/reset", { nb_id: nbId, cell_idx: cellIdx, source: "" }),
  setProgress: (nbId: string, done: boolean) => post<{ ok: boolean }>("/progress", { nb_id: nbId, done }),
  quiz: (id: string) => request<Quiz>(`/quiz/${encodeURIComponent(id)}`),
  asistente: {
    estado: () => request<EstadoAsistente>("/asistente/estado"),
    consultar: (usuario: string, pedido: string) => post<Consulta>("/asistente/consultar", { usuario, pedido }),
    memoria: (usuario: string) =>
      request<{ recuerdos: Recuerdo[] }>(`/asistente/memoria/${encodeURIComponent(usuario)}`),
    olvidar: (usuario: string, recuerdoId: string) =>
      post<{ ok: boolean }>("/asistente/olvidar", { usuario, recuerdo_id: recuerdoId }),
  },
};
