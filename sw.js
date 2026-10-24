// A basic service worker just to satisfy the PWA install requirement
self.addEventListener('install', (e) => {
    console.log('[Service Worker] Install');
});

self.addEventListener('fetch', (e) => {
    // We aren't caching anything for offline use yet, just passing requests through
    return;
});