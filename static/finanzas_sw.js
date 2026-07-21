const CACHE = "finanzas-v3";
const URLS  = ["/finanzas", "/finanzas/viajes"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(URLS)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  if (e.request.url.includes("/api/")) return; // siempre red para la API
  e.respondWith(
    fetch(e.request).catch(async () =>
      (await caches.match(e.request)) || (await caches.match("/finanzas")) || Response.error()
    )
  );
});
