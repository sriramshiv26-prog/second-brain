const CACHE_NAME = 'second-brain-wiki-v1';
const RUNTIME_CACHE = 'second-brain-wiki-runtime-v1';
const OFFLINE_PAGE = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/wiki',
  '/offline.html',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching static assets');
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[Service Worker] Failed to cache some assets:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, cache fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Strategy: Network first for API, Cache first for assets
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
  } else {
    event.respondWith(cacheFirstStrategy(request));
  }
});

// Network first strategy (for API calls)
async function networkFirstStrategy(request) {
  try {
    const response = await fetch(request);
    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[Service Worker] Network request failed, checking cache:', request.url);
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    // Return offline page if available
    return caches.match(OFFLINE_PAGE).then((response) => {
      return (
        response ||
        new Response('Offline - Please check your connection', {
          status: 503,
          statusText: 'Service Unavailable',
          headers: new Headers({
            'Content-Type': 'text/plain',
          }),
        })
      );
    });
  }
}

// Cache first strategy (for static assets)
async function cacheFirstStrategy(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[Service Worker] Offline - returning cached asset or offline page');
    return caches.match(OFFLINE_PAGE).then((response) => {
      return (
        response ||
        new Response('Offline', {
          status: 503,
          statusText: 'Service Unavailable',
        })
      );
    });
  }
}

// Handle messages from clients (for cache clearing, etc.)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[Service Worker] Skipping waiting, reloading...');
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.delete(RUNTIME_CACHE).then(() => {
      console.log('[Service Worker] Runtime cache cleared');
    });
  }
});

// Periodic background sync (if supported)
// self.addEventListener('sync', (event) => {
//   if (event.tag === 'sync-pending-edits') {
//     event.waitUntil(syncPendingEdits());
//   }
// });

// async function syncPendingEdits() {
//   console.log('[Service Worker] Syncing pending edits...');
//   // TODO: Implement pending edit sync when online
// }
