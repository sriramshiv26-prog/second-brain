'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface SynthesisSectionProps {
  content: string;
  lastSynthesisDate?: string;
}

/**
 * SynthesisSection - Displays AI synthesis insights
 * Mobile: Collapsible sections, Desktop: Expanded
 */
export default function SynthesisSection({
  content,
  lastSynthesisDate,
}: SynthesisSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!content) {
    return null;
  }

  return (
    <div className="mt-8 pt-6 border-t border-gray-200">
      {/* Header with toggle (mobile) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="md:hidden w-full flex items-center justify-between mb-4 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
      >
        <h3 className="text-lg font-bold text-blue-900">✨ Synthesis Insights</h3>
        <span className="text-blue-900">{isExpanded ? '▼' : '▶'}</span>
      </button>

      {/* Desktop header */}
      <h3 className="hidden md:block text-xl font-bold text-gray-900 mb-4">
        ✨ Synthesis Insights
      </h3>

      {/* Content (hidden on mobile unless expanded) */}
      <div
        className={`bg-blue-50 p-4 rounded-lg prose prose-sm max-w-none ${
          isExpanded ? 'block' : 'hidden md:block'
        }`}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h2: ({ ...props }) => (
              <h4 className="text-base font-bold mt-3 mb-2 text-blue-900" {...props} />
            ),
            h3: ({ ...props }) => (
              <h5 className="text-sm font-bold mt-2 mb-1 text-blue-900" {...props} />
            ),
            ul: ({ ...props }) => (
              <ul className="list-disc list-inside space-y-1 my-2" {...props} />
            ),
            li: ({ ...props }) => <li className="text-sm text-blue-800" {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>
      </div>

      {/* Timestamp */}
      {lastSynthesisDate && (
        <p className="text-xs text-gray-500 mt-3">
          Last synthesized: {new Date(lastSynthesisDate).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}
