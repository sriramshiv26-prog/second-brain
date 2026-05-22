'use client';

import Link from 'next/link';
import type { SearchResult } from '@/lib/types';

interface SearchResultsProps {
  results: SearchResult[];
  loading?: boolean;
  error?: string;
  totalResults?: number;
  executionTime?: number;
}

export default function SearchResults({
  results,
  loading = false,
  error,
  totalResults,
  executionTime,
}: SearchResultsProps) {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin">⏳</div>
        <p className="mt-2 text-gray-600">Searching...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        Error: {error}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No results found. Try a different search query.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {executionTime && (
        <div className="text-sm text-gray-600">
          Found {totalResults || results.length} results in {executionTime.toFixed(2)}ms
        </div>
      )}
      <div className="space-y-4">
        {results.map((result) => (
          <div
            key={result.doc_id}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-semibold text-blue-600 mb-2">
              {result.title}
            </h3>
            <p className="text-gray-700 mb-2 line-clamp-3">{result.excerpt}</p>
            <div className="flex justify-between items-center text-sm text-gray-500">
              <span className="badge bg-gray-100 px-2 py-1 rounded">
                {result.source_type}
              </span>
              <span className="text-gray-600">
                Relevance: {(result.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
