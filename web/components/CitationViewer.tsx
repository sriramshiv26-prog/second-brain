'use client';

import { useState } from 'react';

interface Citation {
  id: string;
  title: string;
  author?: string;
  year?: number;
  url?: string;
  doi?: string;
}

interface CitationViewerProps {
  citations?: Citation[];
  entityId?: string;
  loading?: boolean;
}

type CitationFormat = 'apa' | 'mla' | 'chicago' | 'bibtex';

export default function CitationViewer({
  citations = [],
  loading = false,
}: CitationViewerProps) {
  const [selectedFormat, setSelectedFormat] = useState<CitationFormat>('apa');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const formatCitation = (citation: Citation, format: CitationFormat): string => {
    switch (format) {
      case 'apa':
        return `${citation.author || 'Unknown'} (${citation.year || 'n.d.'}). ${citation.title}.${citation.url ? ` Retrieved from ${citation.url}` : ''}`;

      case 'mla':
        return `${citation.author || 'Unknown'}. "${citation.title}." ${citation.year || 'n.d.'}.${citation.url ? ` ${citation.url}.` : ''}`;

      case 'chicago':
        return `${citation.author || 'Unknown'}. ${citation.title}. ${citation.year || 'n.d.'}.${citation.url ? ` ${citation.url}` : ''}`;

      case 'bibtex':
        return `@article{${citation.id.slice(0, 10)},\n  author = {${citation.author || 'Unknown'}},\n  title = {${citation.title}},\n  year = {${citation.year || 'n.d.'}}\n}`;

      default:
        return citation.title;
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Loading citations...</p>
      </div>
    );
  }

  if (citations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No citations available for this entity.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Citation Format
        </label>
        <select
          value={selectedFormat}
          onChange={(e) => setSelectedFormat(e.target.value as CitationFormat)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
        >
          <option value="apa">APA</option>
          <option value="mla">MLA</option>
          <option value="chicago">Chicago</option>
          <option value="bibtex">BibTeX</option>
        </select>
      </div>

      <div className="space-y-2">
        {citations.map((citation) => (
          <div key={citation.id} className="border border-gray-200 rounded-lg p-4">
            <button
              onClick={() =>
                setExpandedId(expandedId === citation.id ? null : citation.id)
              }
              className="w-full text-left flex items-start justify-between"
            >
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">{citation.title}</h4>
                <p className="text-sm text-gray-600">
                  {citation.author && `${citation.author} `}
                  {citation.year && `(${citation.year})`}
                </p>
              </div>
              <span className="text-gray-400 ml-2">
                {expandedId === citation.id ? '▼' : '▶'}
              </span>
            </button>

            {expandedId === citation.id && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">
                  {formatCitation(citation, selectedFormat)}
                </pre>
                <button
                  onClick={() => {
                    const text = formatCitation(citation, selectedFormat);
                    navigator.clipboard.writeText(text);
                  }}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-700"
                >
                  Copy to clipboard
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
