'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import EntityDetail from '@/components/EntityDetail';
import GraphVisualization from '@/components/GraphVisualization';
import { graphAPI, vizAPI } from '@/lib/api';

export default function EntityPage() {
  const params = useParams();
  const entityId = params.id as string;

  const {
    data: entity,
    isLoading: entityLoading,
    error: entityError,
  } = useQuery({
    queryKey: ['entity', entityId],
    queryFn: () => graphAPI.getEntityDetail(entityId),
    enabled: !!entityId,
  });

  const {
    data: visualization,
    isLoading: vizLoading,
    error: vizError,
  } = useQuery({
    queryKey: ['viz', entityId],
    queryFn: () => vizAPI.getEntityVisualization(entityId),
    enabled: !!entityId,
  });

  return (
    <div className="py-8">
      <Link
        href="/"
        className="text-blue-600 hover:text-blue-800 mb-6 inline-block"
      >
        ← Back to Home
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {entity ? (
            <EntityDetail entity={entity} />
          ) : entityLoading ? (
            <div className="text-center py-8">Loading entity...</div>
          ) : entityError ? (
            <div className="text-red-600">Error loading entity</div>
          ) : null}
        </div>

        <div className="lg:col-span-1">
          {visualization && (
            <div className="sticky top-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Visualization
              </h2>
              <GraphVisualization
                data={visualization}
                loading={vizLoading}
                error={vizError instanceof Error ? vizError.message : undefined}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
