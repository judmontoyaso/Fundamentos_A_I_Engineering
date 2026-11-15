// Tipos compartidos entre el compilador de contenido, el servidor y los componentes.
export type TipoItem = "md" | "lab" | "quiz" | "anotar";
export type ItemNav = { id: string; titulo: string; tipo: TipoItem; curso: string; gratis: boolean };
export type GrupoNav = { curso: string; grupo: string; items: ItemNav[] };
export type CursoNav = { id: string; titulo: string; modulos: number };
export type Nav = { cursos: CursoNav[]; grupos: GrupoNav[] };

export type Pregunta = { pregunta: string; opciones: string[]; correcta: number; explicacion: string };
export type ItemAnotacion = { id: string; cv: string; salida: string };
export type Tarea = { titulo: string; pregunta: string; guiaHtml: string; items: ItemAnotacion[] };
export type ItemContenido = ItemNav & { html?: string; preguntas?: Pregunta[]; tarea?: Tarea };

export type Usuario = { id: string; email: string; nombre?: string; verificado: boolean };
export type UsuarioRegistrado = { id: string; email: string; nombre: string | null; creado: string; unidadesHechas: number };
export type Progreso = Record<string, boolean>;
export type Etiquetas = Record<string, { label: boolean; nota: string }>;

export type PlanId = "mensual" | "anual" | "curso";
/** Un derecho de lectura. `alcance` es "todo" o el id de un curso; `hasta` nulo = sin vencimiento. */
export type Acceso = {
  id: string; userId: string; plan: PlanId; alcance: string; estado: "activo" | "revocado";
  hasta: string | null; origen: string; pedidoId: string | null; creado: string;
};
export type EstadoPedido = "pendiente" | "pagado" | "rechazado" | "reembolsado";
export type Pedido = {
  id: string; userId: string; email: string; plan: PlanId; curso: string | null;
  monto: number; moneda: string; proveedor: string; estado: EstadoPedido; refProveedor: string | null; creado: string;
};

export type Cupon = {
  codigo: string;
  porcentaje: number;
  plan: PlanId | null;
  curso: string | null;
  usosMax: number | null;
  usos: number;
  activo: boolean;
  creado: string;
};
