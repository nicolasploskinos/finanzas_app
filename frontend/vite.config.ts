import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

// El backend Flask de desarrollo (scratchpad/run_local2.py) escucha acá.
const FLASK = "http://127.0.0.1:5959";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  // Los assets se sirven desde Flask (/static/app/), no desde la raíz.
  base: "/static/app/",
  build: {
    outDir: "../static/app",
    emptyOutDir: true,
    // Nombres fijos (sin hash): PythonAnywhere no corre Node, así que el
    // build se commitea y la plantilla Jinja referencia estos archivos
    // directamente. El cache-busting lo pone Flask con ?v=<mtime>.
    rollupOptions: {
      output: {
        entryFileNames: "montor.js",
        chunkFileNames: "montor-[name].js",
        assetFileNames: "montor.[ext]",
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": FLASK,
      "/montor/login": FLASK,
      "/montor/logout": FLASK,
      "/static": FLASK,
    },
  },
});
