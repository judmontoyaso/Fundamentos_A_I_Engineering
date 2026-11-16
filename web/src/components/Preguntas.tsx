"use client";
// Preguntas frecuentes en acordeón accesible: una abierta a la vez, navegable con teclado.
import * as Accordion from "@radix-ui/react-accordion";
import { Plus } from "lucide-react";

export function Preguntas({ items }: { items: { q: string; a: string }[] }) {
  return (
    <Accordion.Root type="single" collapsible className="preguntas">
      {items.map((f, i) => (
        <Accordion.Item key={f.q} value={`p${i}`} className="pregunta">
          <Accordion.Header asChild>
            <h3>
              <Accordion.Trigger className="pregunta-btn">
                <span>{f.q}</span>
                <Plus aria-hidden size={18} className="pregunta-icono" />
              </Accordion.Trigger>
            </h3>
          </Accordion.Header>
          <Accordion.Content className="pregunta-resp">
            <p>{f.a}</p>
          </Accordion.Content>
        </Accordion.Item>
      ))}
    </Accordion.Root>
  );
}
