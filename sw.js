/*
 * sw.js — service worker. Caches the whole app shell so it runs OFFLINE.
 * Bump CACHE_VERSION whenever you change any cached file to force an update.
 */
"use strict";

const CACHE_VERSION = "vault-v2";
const ASSETS = [
  ".",
  "index.html",
  "manifest.webmanifest",
  "css/fonts.css",
  "css/style.css",
  "fonts/inter.woff2",
  "fonts/jetbrains-mono.woff2",
  "js/crypto.js",
  "js/store.js",
  "js/manual.js",
  "js/app.js",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-maskable-512.png",
];

// Install: pre-cache the app shell.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

// Activate: drop old caches.
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch: cache-first for our own assets (true offline), network for the rest
// (e.g. Google Fonts) with a graceful fallback to whatever is cached.
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req)
        .then((res) => {
          // Opportunistically cache same-origin GETs we didn't list explicitly.
          if (res && res.status === 200 && new URL(req.url).origin === self.location.origin) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
    })
  );
});
