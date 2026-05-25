import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import PWAInitializer from '@/components/PWAInitializer';

export const metadata: Metadata = {
  title: 'Second Brain',
  description: 'Personal knowledge management system',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#3b82f6" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Wiki" />
      </head>
      <body className="bg-white">
        <PWAInitializer />
        <Providers>
          <nav className="bg-gray-900 text-white shadow-lg">
            <div className="max-w-7xl mx-auto px-4 py-4">
              <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold">
                  <a href="/">Second Brain</a>
                </h1>
                <ul className="flex gap-6">
                  <li>
                    <a href="/" className="hover:text-gray-300 transition-colors">
                      Home
                    </a>
                  </li>
                  <li>
                    <a href="/search" className="hover:text-gray-300 transition-colors">
                      Search
                    </a>
                  </li>
                  <li>
                    <a href="/graph" className="hover:text-gray-300 transition-colors">
                      Graph
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="bg-gray-100 text-gray-600 text-center py-4 mt-12">
            <p>Second Brain © 2026. Personal Knowledge Management System.</p>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
