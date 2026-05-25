'use client';

import Link from 'next/link';
import { WikiPage } from '@/lib/types';

interface WikiListProps {
  pages: WikiPage[];
  isLoading?: boolean;
  error?: string;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

/**
 * WikiList - Displays wiki pages in responsive grid
 * Mobile: 1 column, Tablet: 2 columns, Desktop: 3 columns
 */
export default function WikiList({
  pages,
  isLoading = false,
  error,
  onLoadMore,
  hasMore = false,
}: WikiListProps) {
  if (error) {
    return (
      <div className="w-full p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">
          <strong>Error:</strong> {error}
        </p>
      </div>
    );
  }

  if (isLoading && pages.length === 0) {
    return (
      <div className="w-full space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-48 bg-gray-200 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (pages.length === 0) {
    return (
      <div className="w-full py-12 text-center">
        <p className="text-gray-500 text-lg mb-4">No wiki pages yet</p>
        <Link
          href="/wiki/create"
          className="inline-block px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Create First Page
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Grid: 1 col on mobile, 2 on tablet, 3 on desktop */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {pages.map((page) => (
          <Link key={page.slug} href={`/wiki/${page.slug}`}>
            <div className="h-full p-4 border border-gray-200 rounded-lg hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer bg-white">
              {/* Title */}
              <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
                {page.title}
              </h3>

              {/* Excerpt from content */}
              <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                {page.content?.substring(0, 150).replace(/^#+ /, '') || 'No description'}
              </p>

              {/* Footer with stats */}
              <div className="flex items-center justify-between text-xs text-gray-500 border-t pt-2">
                <span>
                  {new Date(page.updated_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>

                {/* Contradiction badge */}
                {page.contradiction_count > 0 && (
                  <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">
                    ⚠️ {page.contradiction_count} issues
                  </span>
                )}

                {/* Version badge */}
                <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                  v{page.version}
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Load more button */}
      {hasMore && (
        <div className="mt-8 text-center">
          <button
            onClick={onLoadMore}
            disabled={isLoading}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </div>
  );
}
