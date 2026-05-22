'use client';

import type { Entity } from '@/lib/types';

interface EntityDetailProps {
  entity: Entity;
  loading?: boolean;
  error?: string;
}

export default function EntityDetail({
  entity,
  loading = false,
  error,
}: EntityDetailProps) {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin">⏳</div>
        <p className="mt-2 text-gray-600">Loading entity...</p>
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
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{entity.name}</h1>
            <p className="text-gray-600 mt-1">Type: {entity.type}</p>
          </div>
          {entity.mention_count && (
            <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
              Mentioned {entity.mention_count} times
            </div>
          )}
        </div>
        {entity.definition && (
          <p className="text-gray-700">{entity.definition}</p>
        )}
      </div>

      {entity.relationships && entity.relationships.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">
            Relationships
          </h2>
          <ul className="space-y-2">
            {entity.relationships.map((rel, idx) => (
              <li key={idx} className="text-gray-700">
                <span className="font-medium">{rel.name}</span>
                <span className="text-gray-500 mx-2">({rel.relationship_type})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {entity.documents && entity.documents.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">
            Documents ({entity.documents.length})
          </h2>
          <div className="space-y-3">
            {entity.documents.map((doc) => (
              <div
                key={doc.doc_id}
                className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
              >
                <p className="font-medium text-blue-600">{doc.title}</p>
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {doc.excerpt}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
