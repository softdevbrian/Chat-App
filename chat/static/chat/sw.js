// Tuko Chat Service Worker for PWA Offline Shell & Installation
const CACHE_NAME = 'tuko-chat-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/chat/style.css?v=7',
  '/static/chat/manifest.json',
  '/static/chat/icon-192.png',
  '/static/chat/icon-512.png',
  'https://unpkg.com/vue@3/dist/vue.global.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {
        // Fallback gracefully if any asset fails to fetch during install
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Only cache GET requests, bypass WebSockets and APIs
  if (event.request.method !== 'GET' || event.request.url.includes('/ws/') || event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
