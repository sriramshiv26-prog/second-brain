'use client';

import { useState, useCallback } from 'react';
import type { SearchResult } from '@/lib/types';

interface AdvancedSearchResultsProps {
  results: SearchResult[];
  loading?: boolean;
  error?: string;
  totalResults?: number;
  executionTime?: number;
}

export default function AdvancedSearchResults({
  results,
  loading = false,
  error,
  totalResults,
  executionTime,
}: AdvancedSearchResultsProps) {
  const [filteredResults, setFilteredResults] = useState<SearchResult[]>(results);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [sortBy, setSortBy] = useState<string>('relevance');

  const handleFilter = useCallback(
    (sourceType?: string) => {
      let filtered = results;
      if (sourceType) {
        filtered = filtered.filter((r) => r.source_type === sourceType);
      }
      setFilteredResults(filtered);
      setCurrentPage(1);
    },
    [results]
  );

  const handleSort = useCallback(
    (option: string) => {
      setSortBy(option);
      let sorted = [...filteredResults];

      switch (option) {
        case 'relevance':
          sorted.sort((a, b) => b.relevance_score - a.relevance_score);
          break;
        case 'title':
          sorted.sort((a, b) => a.title.localeCompare(b.title));
          break;
        default:
          break;
      }

      setFilteredResults(sorted);
    },
    [filteredResults]
  );

  const totalPages = Math.ceil(filteredResults.length / pageSize);
  const paginatedResults = filteredResults.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

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

  const sourceTypes = [...new Set(results.map((r) => r.source_type))];

  return (
    <div className="space-y-6">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Source Type
            </label>
            <select
              onChange={(e) => handleFilter(e.target.value || undefined)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">All Types</option>
              {sourceTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sort by
            </label>
            <select
              value={sortBy}
              onChange={(e) => handleSort(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="relevance">Relevance</option>
              <option value="title">Title</option>
            </select>
          </div>

          <div className="text-sm text-gray-600 pt-8">
            {filteredResults.length}
            {totalResults && totalResults > filteredResults.length && `/${totalResults}`} results
            {executionTime && ` in ${executionTime.toFixed(2)}ms`}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {paginatedResults.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No results found.
          </div>
        ) : (
          paginatedResults.map((result) => (
            <div
              key={result.doc_id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <h3 className="text-lg font-semibold text-blue-600 mb-2">
                {result.title}
              </h3>
              <p className="text-gray-700 mb-3 line-clamp-2">{result.excerpt}</p>
              <div className="flex justify-between items-center text-sm text-gray-500">
                <span className="badge bg-gray-100 px-2 py-1 rounded">
                  {result.source_type}
                </span>
                <span>
                  Relevance: {(result.relevance_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-4">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 border border-gray-300 rounded text-gray-700 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-gray-600">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 border border-gray-300 rounded text-gray-700 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
