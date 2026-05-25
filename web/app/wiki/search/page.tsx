'use client';

import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import Link from 'next/link';
import WikiSearch from '@/components/wiki/WikiSearch';
import { wikiAPI } from '@/lib/api';

/**
 * Wiki Search Page
 * Responsive search results display
 */
export default function WikiSearchPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams?.get('q') || '';
  const [query, setQuery] = useState(initialQuery);

  // Fetch search results
  const {
    data: results = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['wiki-search', query],
    queryFn: () => (query.trim() ? wikiAPI.searchPages(query) : Promise.resolve([])),
    enabled: query.trim().length > 0,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <main className="min-h-screen bg-white">
      {/* Header section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            Search Wiki
          </h1>
          <p className="text-gray-600">Find knowledge in your wiki pages</p>
        </div>
      </div>

      {/* Content section */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <WikiSearch
          query={query}
          results={results}
          isLoading={isLoading}
          error={error?.message}
          onQueryChange={setQuery}
        />
      </div>

      {/* Navigation links for mobile */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around">
        <Link href="/wiki" className="flex-1 text-center py-3 text-gray-600 hover:text-gray-900">
          Wiki
        </Link>
        <Link href="/wiki/search" className="flex-1 text-center py-3 border-b-2 border-blue-500 text-blue-600 font-medium">
          Search
        </Link>
        <Link href="/" className="flex-1 text-center py-3 text-gray-600 hover:text-gray-900">
          Home
        </Link>
      </div>

      {/* Bottom padding on mobile */}
      <div className="md:hidden h-16" />
    </main>
  );
}
