// Avisos breves en pantalla, sin librerías: un emisor de eventos y un componente.
import { useEffect, useState } from "react";

type Listener = (msg: string) => void;
const listeners = new Set<Listener>();

export function toast(msg: string) {
  listeners.forEach((l) => l(msg));
}

export function Toaster() {
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    let timer: number | undefined;
    const onMsg: Listener = (m) => {
      setMsg(m);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setMsg(null), 2400);
    };
    listeners.add(onMsg);
    return () => {
      listeners.delete(onMsg);
      window.clearTimeout(timer);
    };
  }, []);

  return <div className={"toast" + (msg ? " show" : "")} role="status">{msg}</div>;
}
