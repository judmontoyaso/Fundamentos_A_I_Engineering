# Frontend · Notebook del curso (Vite + React + TypeScript)

Interfaz tipo notebook: la teoría se renderiza como Markdown y el código se edita en CodeMirror. Las celdas del
**Laboratorio** se ejecutan contra la API del backend. No contiene lógica de servidor: todo pasa por `src/api.ts`.

## Arrancar

Necesitas el backend corriendo (`../backend`). Luego:

```bash
npm install
npm run dev
```

O doble clic en `iniciar-frontend.bat`. Abre `http://127.0.0.1:5173`.

Si tu API no está en `http://127.0.0.1:8000`, copia `.env.example` como `.env.local` y cambia `VITE_API_URL`.

## Scripts

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo con recarga en caliente |
| `npm run build` | Revisa tipos y genera `dist/` para producción |
| `npm run preview` | Sirve el `dist/` generado |
| `npm run typecheck` | Solo revisión de tipos |

## Estructura

```
src/
  main.tsx              # punto de entrada
  App.tsx               # layout, tema, progreso, notebook activo
  api.ts                # cliente HTTP de la API (único punto de contacto con el backend)
  types.ts              # contratos de datos de la API
  toast.tsx             # avisos breves
  components/
    Sidebar.tsx         # navegación por módulos
    Notebook.tsx        # carga y pinta las celdas de un notebook
    CodeCell.tsx        # editor + ejecución + salida
    MarkdownCell.tsx    # prosa del curso y links internos
  styles.css
```

## Atajos

- `Ctrl/Cmd + Enter` en una celda del laboratorio: ejecutarla.
- **↺ kernel** (barra superior): borra las variables del notebook actual.
- **↺ original** (en una celda editada): vuelve al código del curso.
