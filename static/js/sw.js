/* Service Worker v3.0 — GrafikRaboty PWA (2026) */
const CACHE_NAME = 'grafik-work-v4';
const OFFLINE_PAGE = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/login',
  '/chat',
  '/static/css/style.css',
  '/static/css/smart_revision.css',
  '/static/js/app.js',
  '/static/js/chat-modern.js',
  '/static/js/pwa-installer.js',
  '/static/js/barcode-scanner.js',
  '/static/js/converter.js',
  '/static/js/recipes.js',
  '/static/js/smart_revision.js',
  '/manifest.json'
];

const NETWORK_ONLY = ['/api/', '/socket.io/', '/ws', '/tunnel-info'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = event.request.url;
  const isAPI = url.includes('/api/');
  const isSocket = url.includes('/socket.io/') || url.includes('/ws');
  if (isSocket) return;
  if (isAPI && event.request.method !== 'GET') return;

  if (isAPI) {
    event.respondWith(
      fetch(event.request)
        .then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
          }
          return res;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return res;
      }).catch(() => {
        if (event.request.mode === 'navigate') return caches.match(OFFLINE_PAGE);
      });
    })
  );
});

/* Background Sync */
self.addEventListener('sync', event => {
  if (event.tag === 'sync-data') event.waitUntil(syncPendingData());
  if (event.tag === 'sync-messages') event.waitUntil(syncMessages());
});

async function syncPendingData() {
  const cache = await caches.open('pending-actions');
  const requests = await cache.keys();
  for (const req of requests) {
    try {
      const pending = await cache.match(req);
      if (pending) {
        await fetch(req, { method: 'POST', body: await pending.text(), headers: { 'Content-Type': 'application/json' }});
        await cache.delete(req);
      }
    } catch (e) { console.warn('[SW] Sync failed:', e); }
  }
}

async function syncMessages() {
  console.log('[SW] Syncing messages...');
}

/* Push Notifications */
self.addEventListener('push', event => {
  let data = { title: 'График работы', body: 'Новое уведомление', icon: '/static/images/vetgid-logo.png' };
  try { data = event.data ? JSON.parse(event.data.text()) : data; } catch { data.body = event.data.text(); }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon || '/static/images/vetgid-logo.png',
      badge: '/static/images/vetgid-logo.png',
      vibrate: [100, 50, 100],
      data: { url: data.url || '/' },
      actions: [{ action: 'open', title: 'Открыть' }, { action: 'close', title: 'Закрыть' }]
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'open' || !event.action) {
    event.waitUntil(clients.openWindow(event.notification.data?.url || '/'));
  }
});

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'CACHE_URLS') {
    event.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(event.data.urls)));
  }
});
