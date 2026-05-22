'use client';

import type { VisualizationResponse } from '@/lib/types';

interface GraphVisualizationProps {
  data: VisualizationResponse;
  loading?: boolean;
  error?: string;
}

export default function GraphVisualization({
  data,
  loading = false,
  error,
}: GraphVisualizationProps) {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin">⏳</div>
        <p className="mt-2 text-gray-600">Loading visualization...</p>
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

  return (
    <div className="w-full border border-gray-200 rounded-lg p-4 bg-gray-50">
      <h3 className="text-lg font-semibold mb-4">Graph Visualization</h3>
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium text-gray-900 mb-3">
            Nodes ({data.node_count})
          </h4>
          <ul className="space-y-2 text-sm">
            {data.nodes.map((node) => (
              <li key={node.id} className="text-gray-700">
                <span className="font-medium">{node.label}</span>
                <span className="text-gray-500 text-xs ml-2">
                  ({node.type}, size: {node.size})
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="font-medium text-gray-900 mb-3">
            Edges ({data.edge_count})
          </h4>
          <ul className="space-y-2 text-sm">
            {data.edges.map((edge, idx) => (
              <li key={idx} className="text-gray-700">
                <span className="font-medium">{edge.label}</span>
                <span className="text-gray-500 text-xs ml-2">
                  {edge.source} → {edge.target}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-4 italic">
        Interactive D3.js/Cytoscape visualization will render here in Phase 3
      </p>
    </div>
  );
}
