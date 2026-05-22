'use client';

import { useCallback, useState } from 'react';
import type { FilterRequest } from '@/lib/types';

interface AdvancedFiltersProps {
  onFilter?: (filters: FilterRequest) => void;
  entityTypes?: string[];
  relationshipTypes?: string[];
}

export default function AdvancedFilters({
  onFilter,
  entityTypes = [],
  relationshipTypes = [],
}: AdvancedFiltersProps) {
  const [filters, setFilters] = useState<FilterRequest>({
    entityTypes: [],
    relationshipTypes: [],
    mentionCountMin: undefined,
    mentionCountMax: undefined,
    searchQuery: '',
  });

  const handleEntityTypeChange = useCallback(
    (type: string) => {
      setFilters((prev) => ({
        ...prev,
        entityTypes: prev.entityTypes?.includes(type)
          ? prev.entityTypes.filter((t) => t !== type)
          : [...(prev.entityTypes || []), type],
      }));
    },
    []
  );

  const handleMentionCountChange = useCallback(
    (field: 'mentionCountMin' | 'mentionCountMax', value: string) => {
      setFilters((prev) => ({
        ...prev,
        [field]: value ? parseInt(value) : undefined,
      }));
    },
    []
  );

  const handleSearchChange = useCallback((value: string) => {
    setFilters((prev) => ({
      ...prev,
      searchQuery: value,
    }));
  }, []);

  const handleApplyFilters = useCallback(() => {
    if (onFilter) {
      onFilter(filters);
    }
  }, [filters, onFilter]);

  const handleReset = useCallback(() => {
    setFilters({
      entityTypes: [],
      relationshipTypes: [],
      mentionCountMin: undefined,
      mentionCountMax: undefined,
      searchQuery: '',
    });
  }, []);

  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-white">
      <h3 className="text-lg font-semibold mb-4">Advanced Filters</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Query
          </label>
          <input
            type="text"
            placeholder="Search in name and definition..."
            value={filters.searchQuery || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Entity Types
          </label>
          <div className="grid grid-cols-2 gap-2">
            {entityTypes.map((type) => (
              <label key={type} className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.entityTypes?.includes(type) || false}
                  onChange={() => handleEntityTypeChange(type)}
                  className="rounded border-gray-300 mr-2"
                />
                <span className="text-sm text-gray-700">{type}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Mentions
            </label>
            <input
              type="number"
              min="0"
              value={filters.mentionCountMin || ''}
              onChange={(e) => handleMentionCountChange('mentionCountMin', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              placeholder="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Mentions
            </label>
            <input
              type="number"
              min="0"
              value={filters.mentionCountMax || ''}
              onChange={(e) => handleMentionCountChange('mentionCountMax', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              placeholder="100"
            />
          </div>
        </div>

        {relationshipTypes.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Relationship Types
            </label>
            <select
              multiple
              value={filters.relationshipTypes || []}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  relationshipTypes: Array.from(e.target.selectedOptions, (o) => o.value),
                })
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              {relationshipTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={handleApplyFilters}
            className="flex-1 bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Apply Filters
          </button>
          <button
            onClick={handleReset}
            className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
