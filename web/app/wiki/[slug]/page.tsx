'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import WikiViewer from '@/components/wiki/WikiViewer';
import { wikiAPI } from '@/lib/api';

/**
 * Wiki Page View
 * Responsive layout:
 * Mobile: Single column (sidebar hidden, toggle via hamburger)
 * Desktop: Sidebar with backlinks visible
 */
export default function WikiPageView() {
  const params = useParams();
  const slug = params?.slug as string;
  const [showSidebar, setShowSidebar] = useState(false);

  // Fetch wiki page
  const {
    data: page,
    isLoading: pageLoading,
    error: pageError,
  } = useQuery({
    queryKey: ['wiki-page', slug],
    queryFn: () => (slug ? wikiAPI.getPage(slug) : Promise.reject('No slug')),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch backlinks
  const {
    data: backlinks = [],
  } = useQuery({
    queryKey: ['wiki-backlinks', slug],
    queryFn: () => (slug ? wikiAPI.getBacklinks(slug) : Promise.resolve([])),
    enabled: !!slug,
    staleTime: 10 * 60 * 1000,
  });

  if (!slug) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (pageLoading) {
    return (
      <div className="min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="h-8 bg-gray-200 rounded animate-pulse mb-4 w-1/2" />
          <div className="space-y-2 mb-6">
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-5/6" />
          </div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (pageError || !page) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h2>
          <p className="text-gray-600 mb-6">The wiki page "{slug}" does not exist.</p>
          <Link
            href="/wiki"
            className="inline-block px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Wiki
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-white">
      {/* Header with nav */}
      <div className="border-b border-gray-200 sticky top-0 bg-white z-40">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/wiki" className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2">
            ← Back to Wiki
          </Link>

          <div className="flex items-center gap-2">
            {/* Edit button (desktop) */}
            <Link
              href={`/wiki/${slug}/edit`}
              className="hidden md:inline-block px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
            >
              Edit
            </Link>

            {/* Hamburger menu (mobile - toggle sidebar) */}
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="md:hidden p-2 hover:bg-gray-100 rounded-lg"
              aria-label="Toggle sidebar"
            >
              ☰
            </button>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex flex-col md:flex-row max-w-6xl mx-auto">
        {/* Main content */}
        <div className="flex-1 min-w-0 px-4 py-8 md:pr-8">
          <WikiViewer page={page} />

          {/* Edit button (mobile floating) */}
          <Link
            href={`/wiki/${slug}/edit`}
            className="md:hidden fixed bottom-20 right-4 w-14 h-14 bg-blue-500 text-white rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors shadow-lg text-xl"
            aria-label="Edit page"
          >
            ✏️
          </Link>
        </div>

        {/* Sidebar with backlinks */}
        <aside
          className={`
            w-full md:w-72 bg-gray-50 border-t md:border-t-0 md:border-l border-gray-200 p-4 md:pl-8
            ${showSidebar ? 'block' : 'hidden md:block'}
          `}
        >
          {/* Backlinks section */}
          {backlinks.length > 0 && (
            <div className="mb-6">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                🔗 Backlinks ({backlinks.length})
              </h3>
              <ul className="space-y-2">
                {backlinks.map((backlink) => (
                  <li key={backlink.to_slug}>
                    <Link
                      href={`/wiki/${backlink.to_slug}`}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium block"
                    >
                      {backlink.context || backlink.to_slug}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata section */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="font-bold text-gray-900 mb-3">Info</h4>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-600 font-medium">Version</dt>
                <dd className="text-gray-900">{page.version}</dd>
              </div>
              <div>
                <dt className="text-gray-600 font-medium">Created</dt>
                <dd className="text-gray-900">
                  {new Date(page.created_at).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-gray-600 font-medium">Updated</dt>
                <dd className="text-gray-900">
                  {new Date(page.updated_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </div>
        </aside>
      </div>

      {/* Mobile bottom nav */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around">
        <Link href="/wiki" className="flex-1 text-center py-3 border-b-2 border-blue-500 text-blue-600 font-medium">
          Wiki
        </Link>
        <Link href="/wiki/search" className="flex-1 text-center py-3 text-gray-600 hover:text-gray-900">
          Search
        </Link>
        <Link href="/" className="flex-1 text-center py-3 text-gray-600 hover:text-gray-900">
          Home
        </Link>
      </div>

      {/* Bottom padding for mobile nav */}
      <div className="md:hidden h-16" />
    </main>
  );
}
