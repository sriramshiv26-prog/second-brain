'use client';

import { useEffect, useState } from 'react';
import { initializePWA, isOnline } from '@/lib/pwa';

/**
 * PWAInitializer - Initializes service worker and PWA features
 * Displays online/offline status indicator
 */
export default function PWAInitializer() {
  const [isAppOnline, setIsAppOnline] = useState(true);

  useEffect(() => {
    // Initialize PWA
    initializePWA({
      onOnline: () => {
        setIsAppOnline(true);
        console.log('[PWA] App is back online');
      },
      onOffline: () => {
        setIsAppOnline(false);
        console.log('[PWA] App is offline');
      },
    });

    // Set initial online status
    setIsAppOnline(isOnline());
  }, []);

  return (
    <>
      {!isAppOnline && (
        <div
          role="status"
          aria-live="polite"
          className="bg-yellow-100 border-b border-yellow-400 text-yellow-800 px-4 py-3 flex items-center gap-2"
        >
          <span className="text-lg">📡</span>
          <span className="text-sm font-medium">
            You are offline. Some features may be limited. (Read-only mode)
          </span>
        </div>
      )}
    </>
  );
}
