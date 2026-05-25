/**
 * PWA utilities - Service worker registration and online status
 */

export interface PWAConfig {
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onOffline?: () => void;
  onOnline?: () => void;
}

let registration: ServiceWorkerRegistration | null = null;

/**
 * Register service worker
 */
export async function registerServiceWorker(config?: PWAConfig): Promise<void> {
  if (typeof window === 'undefined') return;
  if (!('serviceWorker' in navigator)) {
    console.log('Service Workers not supported');
    return;
  }

  try {
    registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/',
    });

    console.log('[PWA] Service Worker registered:', registration.scope);

    registration.addEventListener('updatefound', () => {
      const newWorker = registration!.installing;
      if (!newWorker) return;

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          console.log('[PWA] New service worker available');
          config?.onUpdate?.(registration!);
          showUpdatePrompt();
        }
      });
    });
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

/**
 * Check online status and listen for changes
 */
export function setupOnlineStatusListener(config?: PWAConfig): void {
  if (typeof window === 'undefined') return;

  if (!navigator.onLine) {
    config?.onOffline?.();
  }

  window.addEventListener('online', () => {
    console.log('[PWA] Online');
    config?.onOnline?.();
  });

  window.addEventListener('offline', () => {
    console.log('[PWA] Offline');
    config?.onOffline?.();
  });
}

/**
 * Get online status
 */
export function isOnline(): boolean {
  if (typeof window === 'undefined') return true;
  return navigator.onLine;
}

/**
 * Clear cache
 */
export async function clearCache(): Promise<void> {
  if (typeof window === 'undefined') return;

  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map((name) => caches.delete(name)));
  console.log('[PWA] Cache cleared');

  if (registration?.active) {
    registration.active.postMessage({ type: 'CLEAR_CACHE' });
  }
}

/**
 * Skip waiting service worker
 */
export function skipWaitingServiceWorker(): void {
  if (!registration?.waiting) return;

  console.log('[PWA] Skipping waiting service worker...');
  registration.waiting.postMessage({ type: 'SKIP_WAITING' });

  let isReloading = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!isReloading) {
      isReloading = true;
      window.location.reload();
    }
  });
}

/**
 * Show update prompt with safe DOM methods
 */
function showUpdatePrompt(): void {
  const banner = document.createElement('div');
  banner.setAttribute('role', 'region');
  banner.setAttribute('aria-live', 'polite');
  banner.className = 'fixed bottom-0 left-0 right-0 bg-blue-500 text-white p-4 flex items-center justify-between gap-4 z-50';

  const message = document.createElement('span');
  message.textContent = 'A new version of Wiki is available';

  const buttonContainer = document.createElement('div');
  buttonContainer.className = 'flex gap-2';

  const reloadBtn = document.createElement('button');
  reloadBtn.textContent = 'Reload';
  reloadBtn.className = 'px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 transition-colors';

  const dismissBtn = document.createElement('button');
  dismissBtn.textContent = 'Dismiss';
  dismissBtn.className = 'px-4 py-2 bg-blue-400 rounded hover:bg-blue-500 transition-colors';

  buttonContainer.appendChild(reloadBtn);
  buttonContainer.appendChild(dismissBtn);
  banner.appendChild(message);
  banner.appendChild(buttonContainer);
  document.body.appendChild(banner);

  reloadBtn.addEventListener('click', () => {
    skipWaitingServiceWorker();
  });

  dismissBtn.addEventListener('click', () => {
    banner.remove();
  });

  setTimeout(() => {
    if (document.body.contains(banner)) {
      banner.remove();
    }
  }, 10000);
}

/**
 * Check if app is installable
 */
export function isInstallable(): boolean {
  if (typeof window === 'undefined') return false;
  return 'beforeinstallprompt' in window;
}

/**
 * Get install prompt
 */
let deferredPrompt: any = null;

export function setupInstallPrompt(): void {
  if (typeof window === 'undefined') return;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('[PWA] App is installable');
  });
}

/**
 * Trigger install prompt
 */
export async function promptInstall(): Promise<boolean> {
  if (!deferredPrompt) return false;

  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`User response to install prompt: ${outcome}`);

  deferredPrompt = null;
  return outcome === 'accepted';
}

/**
 * Initialize PWA
 */
export function initializePWA(config?: PWAConfig): void {
  if (typeof window === 'undefined') return;

  setupInstallPrompt();
  registerServiceWorker(config);
  setupOnlineStatusListener(config);
}
