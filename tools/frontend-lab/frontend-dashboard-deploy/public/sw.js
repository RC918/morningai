
const CACHE_VERSION = 'v1';
const CACHE_NAME = `morningai-${CACHE_VERSION}`;

const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/favicon.ico',
  '/manifest.json',
];

const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache-first',
  NETWORK_FIRST: 'network-first',
  STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
};

self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Precaching assets');
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') {
    return;
  }

  if (!url.protocol.startsWith('http')) {
    return;
  }

  let strategy = CACHE_STRATEGIES.CACHE_FIRST;

  if (url.pathname.startsWith('/api/')) {
    strategy = CACHE_STRATEGIES.NETWORK_FIRST;
  }
  else if (
    url.pathname.match(/\.(woff2?|ttf|eot|otf)$/) ||
    url.pathname.match(/\.(jpg|jpeg|png|gif|svg|webp|avif)$/) ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com')
  ) {
    strategy = CACHE_STRATEGIES.STALE_WHILE_REVALIDATE;
  }
  else if (url.pathname.match(/\.(js|css)$/)) {
    strategy = CACHE_STRATEGIES.CACHE_FIRST;
  }

  if (strategy === CACHE_STRATEGIES.CACHE_FIRST) {
    event.respondWith(cacheFirst(request));
  } else if (strategy === CACHE_STRATEGIES.NETWORK_FIRST) {
    event.respondWith(networkFirst(request));
  } else if (strategy === CACHE_STRATEGIES.STALE_WHILE_REVALIDATE) {
    event.respondWith(staleWhileRevalidate(request));
  }
});

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  if (cached) {
    console.log('[SW] Cache hit:', request.url);
    return cached;
  }

  try {
    const response = await fetch(request);
    
    if (response.ok) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[SW] Fetch failed:', error);
    
    const offlinePage = await cache.match('/offline.html');
    if (offlinePage) {
      return offlinePage;
    }
    
    throw error;
  }
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);

  try {
    const response = await fetch(request);
    
    if (response.ok) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[SW] Network failed, trying cache:', error);
    
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    
    throw error;
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch((error) => {
    console.error('[SW] Background fetch failed:', error);
  });

  if (cached) {
    console.log('[SW] Serving from cache (stale):', request.url);
    return cached;
  }

  return fetchPromise;
}

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.delete(CACHE_NAME).then(() => {
        console.log('[SW] Cache cleared');
        return self.clients.matchAll();
      }).then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'CACHE_CLEARED' });
        });
      })
    );
  }
});
