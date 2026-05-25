'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import WikiList from '@/components/wiki/WikiList';
import { wikiAPI } from '@/lib/api';
import Link from 'next/link';

/**
 * Wiki Pages List Page
 * Responsive: Full width on mobile, centered container on desktop
 */
export default function WikiPage() {
  const router = useRouter();
  const [limit] = useState(12);
  const [offset, setOffset] = useState(0);

  // Fetch wiki pages with React Query
  const {
    data: pages = [],
    isLoading,
    error,
    isPreviousData,
  } = useQuery({
    queryKey: ['wiki-pages', offset, limit],
    queryFn: () => wikiAPI.getPages(limit, offset),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  const handleLoadMore = () => {
    setOffset((prev) => prev + limit);
  };

  return (
    <main className="min-h-screen bg-white">
      {/* Header section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-8 md:py-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
                Wiki
              </h1>
              <p className="text-gray-600">
                Knowledge base synthesized from your documents
              </p>
            </div>

            {/* Create button */}
            <Link
              href="/wiki/create"
              className="inline-flex items-center justify-center px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
            >
              + New Page
            </Link>
          </div>

          {/* Search bar */}
          <div className="mt-6">
            <div className="relative">
              <input
                type="search"
                placeholder="Search wiki pages..."
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const query = (e.target as HTMLInputElement).value;
                    if (query.trim()) {
                      router.push(`/wiki/search?q=${encodeURIComponent(query)}`);
                    }
                  }
                }}
              />
              <button className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                🔍
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content section */}
      <div className="max-w-6xl mx-auto px-4 py-8 md:py-12">
        {error && (
          <div className="text-center py-8">
            <p className="text-red-600 font-medium">Failed to load wiki pages</p>
            <p className="text-gray-600 text-sm mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        )}

        {!error && (
          <>
            {/* Stats */}
            <div className="mb-6 text-sm text-gray-600">
              <p>
                Showing <strong>{pages.length}</strong> wiki page{pages.length !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Wiki list */}
            <WikiList
              pages={pages}
              isLoading={isLoading && !isPreviousData}
              error={error?.message}
              onLoadMore={handleLoadMore}
              hasMore={pages.length >= limit}
            />
          </>
        )}
      </div>

      {/* Navigation links for mobile bottom tab bar */}
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

      {/* Add bottom padding on mobile for tab bar */}
      <div className="md:hidden h-16" />
    </main>
  );
}
