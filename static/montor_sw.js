self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  // Se borran todas las cachés viejas, incluida cualquier versión anterior
  // de esta misma caché: ya no se precachea nada.
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k)))));
  self.clients.claim();
});

// Sin lógica de caché/fallback: las páginas dinámicas van con
// Cache-Control: no-store del lado del servidor, así que no hay nada
// útil para interceptar acá. Se deja el listener solo para mantener
// los criterios de instalabilidad de la PWA.
self.addEventListener("fetch", () => {});
