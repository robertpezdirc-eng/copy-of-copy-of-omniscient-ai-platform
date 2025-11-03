// Service Worker for Omni Dashboard PWA
const CACHE_NAME = 'omni-dashboard-v1.0.0';
const API_CACHE = 'omni-api-v1';
const STATIC_CACHE = 'omni-static-v1';
const IMAGE_CACHE = 'omni-images-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/logo192.png',
  '/logo512.png',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            return name !== CACHE_NAME && name !== API_CACHE && name !== STATIC_CACHE && name !== IMAGE_CACHE;
          })
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API requests: Network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request, API_CACHE));
  }
  // Images: Cache-first strategy
  else if (request.destination === 'image') {
    event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
  }
  // Static assets: Stale-while-revalidate
  else {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
  }
});

// Network-first strategy (good for API calls)
async function networkFirstStrategy(request, cacheName) {
  try {
    const response = await fetch(request);
    // Cache successful responses
    if (response.status === 200) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Network request failed, trying cache...');
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }
    return new Response('Network error happened', {
      status: 408,
      headers: { 'Content-Type': 'text/plain' },
    });
  }
}

// Cache-first strategy (good for images, fonts)
async function cacheFirstStrategy(request, cacheName) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
    return response;
  } catch (error) {
    console.log('[SW] Cache-first strategy failed for:', request.url);
    return new Response('Resource unavailable', { status: 404 });
  }
}

// Stale-while-revalidate strategy (good for static assets)
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await caches.match(request);

  const fetchPromise = fetch(request).then((response) => {
    cache.put(request, response.clone());
    return response;
  });

  return cachedResponse || fetchPromise;
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  if (event.tag === 'sync-data') {
    event.waitUntil(syncPendingActions());
  }
});

async function syncPendingActions() {
  console.log('[SW] Syncing pending actions...');
  // Get pending actions from IndexedDB
  const db = await openDB();
  const actions = await db.getAll('pendingActions');
  
  for (const action of actions) {
    try {
      await fetch(action.url, {
        method: action.method,
        body: JSON.stringify(action.data),
        headers: { 'Content-Type': 'application/json' },
      });
      // Remove from pending after successful sync
      await db.delete('pendingActions', action.id);
    } catch (error) {
      console.error('[SW] Failed to sync action:', error);
    }
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const data = event.data ? event.data.json() : {
    title: 'Notification',
    body: 'You have a new notification',
  };

  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/badge.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/',
      ...data.data,
    },
    actions: data.actions || [
      { action: 'open', title: 'Open' },
      { action: 'close', title: 'Close' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.action);
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const urlToOpen = event.notification.data.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // Check if there's already a window open
      for (const client of windowClients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      // Open a new window
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Message handler for communication with app
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    const urlsToCache = event.data.payload;
    event.waitUntil(
      caches.open(STATIC_CACHE).then((cache) => {
        return cache.addAll(urlsToCache);
      })
    );
  }
});

// Helper function to open IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('OmniDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pendingActions')) {
        db.createObjectStore('pendingActions', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

console.log('[SW] Service worker loaded');
