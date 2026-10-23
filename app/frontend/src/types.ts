// Contratos de la API (espejo de backend/curso_api).

export type NavItem = { id: string; title: string; type: "md" | "lab" | "quiz" | "app" };
export type NavGroup = { group: string; items: NavItem[] };

export type Cell = {
  idx: number;
  type: "md" | "code";
  lang: string;
  source: string;
  runnable?: boolean;
  fragment?: boolean;
  edited?: boolean;
  file?: string; // script de laboratorio: el kernel lo expone como __file__
};

export type Notebook = { id: string; title: string; cells: Cell[] };

export type RunResult = {
  stdout: string;
  stderr: string;
  result: string | null;
  timed_out: boolean;
};

export type Progress = Record<string, boolean>;

export type Pregunta = {
  pregunta: string;
  opciones: string[];
  correcta: number;
  explicacion: string;
};
export type Quiz = { id: string; title: string; preguntas: Pregunta[] };

export type EstadoAsistente = {
  listo: boolean;
  modelo: string | null;
  cvs: { nombre: string; nivel: string; areas: string[]; revisar: boolean }[];
};

export type Consulta = {
  respuesta: string;
  bloqueado: boolean;
  estado_salida: string;
  recuerdos: string[];
  candidatos: { nombre: string; nivel: string; evidencia: string[] }[];
  evaluaciones: { nombre: string; puntaje: number; motivo: string; revisar: boolean }[];
  trace_id: string;
  arbol: string;
  uso: { llamadas: number; tokens_entrada: number; tokens_salida: number; tokens_razonamiento: number };
  segundos: number;
};

export type Recuerdo = { id: string; texto: string };
