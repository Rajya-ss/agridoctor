// AgriDoctor offline service worker. prepare.py changes VERSION on every build.
const VERSION = "20261124010903";
const CACHE = "agridoctor-offline-" + VERSION;
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png",
              "icon-maskable-512.png", "labels.json", "kb.json", "files.json", "model.onnx"];

async function tell(msg) {
  const all = await self.clients.matchAll({ includeUncontrolled: true });
  all.forEach((c) => c.postMessage(msg));
}

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    let extra = [];
    try {
      const r = await fetch("files.json", { cache: "no-store" });
      extra = (await r.json()).ort.map((f) => "ort/" + f);
    } catch (err) { /* addAll below fails and install retries next visit */ }
    await cache.addAll(CORE.concat(extra));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
    await tell({ type: "ready" });
  })());
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith((async () => {
    const hit = await caches.match(e.request, { ignoreSearch: true });
    if (hit) return hit;
    try { return await fetch(e.request); }
    catch (err) {
      if (e.request.mode === "navigate") return (await caches.match("index.html")) || Response.error();
      return Response.error();
    }
  })());
});
