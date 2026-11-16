"use client";
// Pie de una lección: marcar como leída y pasar a la anterior o la siguiente.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { guardarProgreso } from "@/lib/cliente";
import type { ItemNav } from "@/lib/tipos";

export function Flechas({ prev, next }: { prev?: ItemNav; next?: ItemNav }) {
  return (
    <nav className="paginador" aria-label="Lecciones">
      {prev ? (
        <Link className="pag pag-prev" href={`/leer/${prev.id}`}>
          <span className="pag-dir"><ChevronLeft size={15} aria-hidden /> Anterior</span>
          <span className="pag-titulo">{prev.titulo}</span>
        </Link>
      ) : <span />}
      {next ? (
        <Link className="pag pag-next" href={`/leer/${next.id}`}>
          <span className="pag-dir">Siguiente <ChevronRight size={15} aria-hidden /></span>
          <span className="pag-titulo">{next.titulo}</span>
        </Link>
      ) : (
        <Link className="pag pag-next" href="/cuenta">
          <span className="pag-dir">Terminaste el curso <ChevronRight size={15} aria-hidden /></span>
          <span className="pag-titulo">Ver tu certificado en Mi cuenta</span>
        </Link>
      )}
    </nav>
  );
}

type Props = { id: string; hecho: boolean; conSesion: boolean; urlEntrar: string; prev?: ItemNav; next?: ItemNav };

export function Pie({ id, hecho, conSesion, urlEntrar, prev, next }: Props) {
  const router = useRouter();
  const [valor, setValor] = useState(hecho);
  const [error, setError] = useState(false);

  async function alternar() {
    const nuevo = !valor;
    setValor(nuevo);
    setError(false);
    if (await guardarProgreso(id, nuevo)) {
      toast.success(nuevo ? "Lección marcada como completada" : "Lección marcada como pendiente");
      router.refresh();
    } else {
      setValor(!nuevo);
      setError(true);
      toast.error("No se pudo guardar tu progreso. Revisa tu conexión e inténtalo otra vez.");
    }
  }

  return (
    <div className="foot">
      <div className="foot-marca">
        {conSesion ? (
          <button className={"btn " + (valor ? "done-state" : "primary")} onClick={alternar} aria-pressed={valor}>
            {valor ? <><Check size={16} aria-hidden /> Leída</> : "Marcar como leída"}
          </button>
        ) : (
          <a className="btn" href={urlEntrar}>Crea tu cuenta para guardar tu progreso</a>
        )}
        {error && <span className="aviso">No se pudo guardar. Intenta de nuevo.</span>}
      </div>
      <Flechas prev={prev} next={next} />
    </div>
  );
}
