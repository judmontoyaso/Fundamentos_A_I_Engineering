import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El frontend corre en su propio servidor (5173) y llama a la API por HTTP
// (VITE_API_URL, por defecto http://127.0.0.1:8000). No comparte proceso con el backend.
export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173, strictPort: true },
  preview: { host: "127.0.0.1", port: 4173 },
  build: {
    rollupOptions: {
      output: {
        // El editor pesa más que el resto de la app: va en su propio archivo cacheable.
        manualChunks: { editor: ["@uiw/react-codemirror", "@codemirror/lang-python", "@codemirror/theme-one-dark"] },
      },
    },
  },
});
