'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import SearchForm from '@/components/SearchForm';
import SearchResults from '@/components/SearchResults';
import { searchAPI } from '@/lib/api';

function SearchPageContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', query],
    queryFn: () => (query ? searchAPI.search(query) : Promise.resolve(null)),
    enabled: !!query,
  });

  return (
    <div className="py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Search Results</h1>
        <SearchForm />
      </div>

      {query && (
        <div className="mt-8">
          <p className="text-gray-600 mb-4">
            Searching for: <span className="font-semibold">"{query}"</span>
          </p>

          {isLoading && (
            <SearchResults loading={true} results={[]} />
          )}

          {error && (
            <SearchResults
              results={[]}
              error={error instanceof Error ? error.message : 'Unknown error'}
            />
          )}

          {data && (
            <SearchResults
              results={data.results}
              totalResults={data.total_results}
              executionTime={data.execution_time_ms}
            />
          )}
        </div>
      )}

      {!query && (
        <div className="text-center text-gray-500 py-12">
          <p>Enter a search query above to get started.</p>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="py-8 text-center">Loading...</div>}>
      <SearchPageContent />
    </Suspense>
  );
}
