# Curso AI Engineering · App notebook

Dos proyectos separados que se hablan por HTTP:

```
┌──────────────────────────────┐   HTTP / JSON   ┌──────────────────────────────┐
│ frontend/  (Vite + React)    │ ──────────────▶ │ backend/  (FastAPI)          │
│ http://127.0.0.1:5173        │ ◀────────────── │ http://127.0.0.1:8000        │
│ notebook, editor, progreso   │      CORS       │ contenido · kernel · SQLite  │
└──────────────────────────────┘                 └──────────────┬───────────────┘
                                                                │ lee
                                                 ../modulo-0X-*/README.md, ejercicios.md, code/*.py
```

- **[backend/](backend/README.md)** — API REST: convierte los módulos en notebooks, ejecuta celdas de Python con
  estado por notebook y guarda progreso y ediciones en SQLite.
- **[frontend/](frontend/README.md)** — SPA: muestra la teoría, edita y ejecuta el código del laboratorio.

El contenido no está duplicado: ambos leen tus archivos de los módulos. Editar un `.md` o un script de `code/`
actualiza el curso.

## Arrancar todo

Doble clic en **`iniciar.bat`**: abre una ventana para la API, otra para el frontend, y luego el navegador.

A mano, en dos terminales:

```bash
# terminal 1
cd backend
.venv\Scripts\activate
python run.py
```

```bash
# terminal 2
cd frontend
npm run dev
```

## Cómo usar el notebook

- **Manual** y **Ejercicios**: lectura. Los bloques de código son fragmentos (solo lectura, con botón copiar).
- **Laboratorio** (▶ en la barra lateral): los scripts completos del módulo, ejecutables. Las celdas de un mismo
  laboratorio comparten variables; la última es una celda libre para experimentar.

## Seguridad

El backend ejecuta Python en tu máquina. Solo escucha en `127.0.0.1` y solo acepta peticiones del frontend local.
No lo expongas a una red.
