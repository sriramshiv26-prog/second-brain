'use client';

import Link from 'next/link';
import { WikiSearchResult } from '@/lib/types';

interface WikiSearchProps {
  query: string;
  results: WikiSearchResult[];
  isLoading?: boolean;
  error?: string;
  onQueryChange?: (query: string) => void;
}

/**
 * WikiSearch - Search results display with responsive grid
 */
export default function WikiSearch({
  query,
  results,
  isLoading = false,
  error,
  onQueryChange,
}: WikiSearchProps) {
  return (
    <div className="w-full">
      {/* Search input */}
      {onQueryChange && (
        <div className="mb-6">
          <input
            type="search"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Search wiki pages..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
        </div>
      )}

      {/* Status messages */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-6">
          <p className="text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {isLoading && results.length === 0 && (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && results.length === 0 && query && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">No results found for "{query}"</p>
          <p className="text-gray-400">Try different keywords or browse all wiki pages</p>
        </div>
      )}

      {!isLoading && results.length === 0 && !query && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">Enter a search term to find wiki pages</p>
        </div>
      )}

      {/* Results grid */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {results.map((result) => (
            <Link
              key={result.slug}
              href={`/wiki/${result.slug}`}
              className="p-4 border border-gray-200 rounded-lg hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer bg-white"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="text-lg font-bold text-gray-900 flex-1">
                  {result.title}
                </h3>
                {/* Relevance badge */}
                {result.relevance && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded whitespace-nowrap">
                    {Math.round(result.relevance * 100)}% match
                  </span>
                )}
              </div>

              {/* Excerpt */}
              <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                {result.excerpt || 'No description available'}
              </p>

              {/* Slug footer */}
              <p className="text-xs text-gray-400">/{result.slug}</p>
            </Link>
          ))}
        </div>
      )}

      {/* Result count */}
      {results.length > 0 && (
        <div className="mt-6 text-sm text-gray-600 text-center">
          Found <strong>{results.length}</strong> result
          {results.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
