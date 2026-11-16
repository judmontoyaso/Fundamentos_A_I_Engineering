"use client";
// Pie de una lección: marcar como leída y pasar a la anterior o la siguiente.
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { guardarProgreso } from "@/lib/cliente";
import type { ItemNav } from "@/lib/tipos";

export function Flechas({ prev, next }: { prev?: ItemNav; next?: ItemNav }) {
  return (
    <div className="nav-arrows">
      {prev && <Link className="btn" href={`/leer/${prev.id}`}>← {prev.titulo}</Link>}
      {next ? (
        <Link className="btn" href={`/leer/${next.id}`}>{next.titulo} →</Link>
      ) : (
        <Link className="btn" href="/cuenta">Ir a Mi cuenta / Certificado →</Link>
      )}
    </div>
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
      {conSesion ? (
        <button className={"btn " + (valor ? "done-state" : "primary")} onClick={alternar}>
          {valor ? "✓ Leída" : "Marcar como leída"}
        </button>
      ) : (
        <a className="btn" href={urlEntrar}>Crea tu cuenta para guardar tu progreso</a>
      )}
      {error && <span className="aviso">No se pudo guardar. Intenta de nuevo.</span>}
      <Flechas prev={prev} next={next} />
    </div>
  );
}
