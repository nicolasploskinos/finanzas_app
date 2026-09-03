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
    // El JS se parte por página, pero el CSS entero pesa ~17 kB gzip:
    // partirlo sólo agregaba un parpadeo sin estilos mientras llega el CSS
    // del chunk, y once archivos más al repo.
    cssCodeSplit: false,
    // Flask lee este manifest para saber qué archivos referenciar (ver
    // _spa_assets en routes_paginas.py).
    manifest: true,
    // El hash va en el nombre, no en un `?v=`. Con code splitting eso no es
    // cosmético: la plantilla cargaba `montor.js?v=<mtime>` mientras los
    // chunks importaban `./montor.js` a secas, y como los módulos ES se
    // identifican por URL el navegador terminaba evaluando el entry dos
    // veces — dos copias de React y pantalla en blanco. Con el hash en el
    // nombre hay una sola URL por archivo, y encima la cache puede ser
    // inmutable. Flask resuelve los nombres leyendo el manifest.
    rollupOptions: {
      output: {
        entryFileNames: "montor-[hash].js",
        chunkFileNames: "montor-[name]-[hash].js",
        assetFileNames: "montor-[hash].[ext]",
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
