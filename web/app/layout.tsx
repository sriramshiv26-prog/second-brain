import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Second Brain',
  description: 'Personal knowledge management system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white">
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
      </body>
    </html>
  );
}
