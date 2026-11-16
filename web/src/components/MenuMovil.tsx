"use client";
// Menú de navegación para pantallas angostas: un panel lateral accesible (foco atrapado, Esc para cerrar).
import * as Dialog from "@radix-ui/react-dialog";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

type Enlace = { href: string; texto: string };

export function MenuMovil({ enlaces, cuenta, salir }: { enlaces: Enlace[]; cuenta: Enlace; salir?: string }) {
  const [abierto, setAbierto] = useState(false);
  const cerrar = () => setAbierto(false);
  return (
    <Dialog.Root open={abierto} onOpenChange={setAbierto}>
      <Dialog.Trigger className="menu-movil-btn" aria-label="Abrir el menú">
        <Menu size={20} aria-hidden />
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="menu-movil-fondo" />
        <Dialog.Content className="menu-movil-panel">
          <div className="menu-movil-cab">
            <Dialog.Title className="menu-movil-titulo">Menú</Dialog.Title>
            <Dialog.Close className="menu-movil-btn" aria-label="Cerrar el menú">
              <X size={20} aria-hidden />
            </Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">Secciones del sitio y acceso a tu cuenta</Dialog.Description>
          <nav aria-label="Navegación principal">
            {enlaces.map((e) => (
              <Link key={e.href} href={e.href} onClick={cerrar}>
                {e.texto}
              </Link>
            ))}
          </nav>
          <Link className="btn primary" href={cuenta.href} onClick={cerrar}>
            {cuenta.texto}
          </Link>
          {salir && (
            <a className="btn" href={salir}>
              Cerrar sesión
            </a>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
