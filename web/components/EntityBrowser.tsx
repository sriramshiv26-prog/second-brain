'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import type { Entity } from '@/lib/types';

interface EntityBrowserProps {
  entities: Entity[];
  loading?: boolean;
  error?: string;
}

export default function EntityBrowser({
  entities,
  loading = false,
  error,
}: EntityBrowserProps) {
  const [filteredEntities, setFilteredEntities] = useState<Entity[]>(entities);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const handleFilter = useCallback(
    (entityType?: string) => {
      setSelectedType(entityType || null);
      let filtered = entities;

      if (entityType) {
        filtered = filtered.filter((e) => e.type === entityType);
      }

      if (searchTerm) {
        filtered = filtered.filter((e) =>
          e.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }

      setFilteredEntities(filtered);
    },
    [entities, searchTerm]
  );

  const handleSearch = useCallback(
    (term: string) => {
      setSearchTerm(term);
      let filtered = entities;

      if (selectedType) {
        filtered = filtered.filter((e) => e.type === selectedType);
      }

      if (term) {
        filtered = filtered.filter((e) =>
          e.name.toLowerCase().includes(term.toLowerCase())
        );
      }

      setFilteredEntities(filtered);
    },
    [entities, selectedType]
  );

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin">⏳</div>
        <p className="mt-2 text-gray-600">Loading entities...</p>
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

  const entityTypes = [...new Set(entities.map((e) => e.type))];

  return (
    <div className="space-y-6">
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Entity Browser
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search entities..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Type
            </label>
            <select
              value={selectedType || ''}
              onChange={(e) => handleFilter(e.target.value || undefined)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">All Types</option>
              {entityTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-sm text-gray-600">
          Showing {filteredEntities.length} of {entities.length} entities
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEntities.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-8">
            No entities found.
          </div>
        ) : (
          filteredEntities.map((entity) => (
            <Link
              key={entity.id}
              href={`/entity/${entity.id}`}
              className="block border border-gray-200 rounded-lg p-4 hover:shadow-lg hover:border-blue-300 transition-all"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-900 flex-1">
                  {entity.name}
                </h3>
              </div>

              <div className="mb-3">
                <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">
                  {entity.type}
                </span>
              </div>

              {entity.definition && (
                <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                  {entity.definition}
                </p>
              )}

              <div className="text-xs text-gray-500">
                {entity.mention_count || 0} mentions
              </div>

              {entity.relationships && entity.relationships.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-700 mb-2">
                    Related:
                  </p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    {entity.relationships.slice(0, 2).map((rel, idx) => (
                      <li key={idx}>
                        <span className="font-medium">{rel.name}</span>
                        <span className="text-gray-500 ml-1">
                          ({rel.relationship_type})
                        </span>
                      </li>
                    ))}
                    {entity.relationships.length > 2 && (
                      <li className="italic text-gray-500">
                        +{entity.relationships.length - 2} more
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
