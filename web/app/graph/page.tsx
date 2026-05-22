'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import SearchForm from '@/components/SearchForm';
import GraphVisualization from '@/components/GraphVisualization';
import { graphAPI } from '@/lib/api';

export default function GraphPage() {
  const [entityId, setEntityId] = useState('');
  const [depth, setDepth] = useState(2);

  const { data, isLoading, error } = useQuery({
    queryKey: ['graphTraverse', entityId, depth],
    queryFn: () => graphAPI.traverseGraph(entityId, depth),
    enabled: !!entityId,
  });

  const handleSearch = (query: string) => {
    setEntityId(query);
  };

  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Graph Explorer
      </h1>
      <p className="text-gray-600 mb-8">
        Explore the knowledge graph by traversing relationships between entities.
      </p>

      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 mb-8">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search for Entity
            </label>
            <SearchForm onSearch={handleSearch} />
          </div>

          {entityId && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Traversal Depth: {depth}
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={depth}
                onChange={(e) => setDepth(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">
                1 (immediate neighbors) to 5 (distant connections)
              </div>
            </div>
          )}
        </div>
      </div>

      {entityId && (
        <div className="mt-8">
          {isLoading && <div className="text-center py-8">Loading graph...</div>}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              Error: {error instanceof Error ? error.message : 'Unknown error'}
            </div>
          )}
          {data && (
            <GraphVisualization
              data={{
                nodes: data.nodes.map((n) => ({
                  id: n.id,
                  label: n.name,
                  type: n.type,
                  size: 10,
                })),
                edges: data.edges.map((e) => ({
                  source: e.source_id,
                  target: e.target_name || '',
                  label: e.relationship_type,
                })),
                center_id: data.root_entity_id,
                node_count: data.node_count,
                edge_count: data.edge_count,
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}
