'use strict';
const CACHE = 'maffini-v1';
const SHELL = ['/', '/bundle.js', '/manifest.json', '/css/brand.css', '/css/views.css'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // API calls always go to network — never serve stale legal data from cache.
  if (new URL(e.request.url).pathname.startsWith('/api/')) return;
  // App shell: cache-first.
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request))
  );
});
