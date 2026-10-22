// Contratos de la API (espejo de backend/curso_api).

export type NavItem = { id: string; title: string; type: "md" | "lab" };
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
