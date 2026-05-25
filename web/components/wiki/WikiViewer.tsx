'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import Link from 'next/link';
import { WikiPage } from '@/lib/types';

interface WikiViewerProps {
  page: WikiPage;
}

/**
 * WikiViewer - Displays a wiki page with markdown rendering
 * Responsive design: full-width on mobile, max-width on desktop
 */
export default function WikiViewer({ page }: WikiViewerProps) {
  return (
    <div className="w-full">
      {/* Main content */}
      <article className="prose prose-sm md:prose-base max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkBreaks]}
          components={{
            // Custom link component for wiki links
            a: ({ node, ...props }) => {
              const href = props.href || '';
              // Check if it's an internal wiki link
              if (href.startsWith('#') || !href.startsWith('http')) {
                return (
                  <Link href={href} className="text-blue-600 hover:text-blue-800 underline">
                    {props.children}
                  </Link>
                );
              }
              // External link
              return (
                <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline">
                  {props.children}
                </a>
              );
            },
            // Code block styling
            code: ({ node, inline, ...props }) => {
              if (inline) {
                return (
                  <code className="bg-gray-100 rounded px-2 py-1 font-mono text-sm text-red-600" {...props} />
                );
              }
              return (
                <code className="block bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm" {...props} />
              );
            },
            // Heading styling
            h1: ({ ...props }) => <h1 className="text-4xl font-bold mt-6 mb-4" {...props} />,
            h2: ({ ...props }) => <h2 className="text-3xl font-bold mt-5 mb-3" {...props} />,
            h3: ({ ...props }) => <h3 className="text-2xl font-bold mt-4 mb-2" {...props} />,
            h4: ({ ...props }) => <h4 className="text-xl font-bold mt-3 mb-2" {...props} />,
            // List styling
            ul: ({ ...props }) => <ul className="list-disc list-inside space-y-1 my-3" {...props} />,
            ol: ({ ...props }) => <ol className="list-decimal list-inside space-y-1 my-3" {...props} />,
            li: ({ ...props }) => <li className="ml-4" {...props} />,
            // Blockquote styling
            blockquote: ({ ...props }) => (
              <blockquote className="border-l-4 border-gray-300 pl-4 py-2 italic text-gray-700 my-3" {...props} />
            ),
            // Table styling
            table: ({ ...props }) => (
              <table className="border-collapse border border-gray-300 w-full my-3" {...props} />
            ),
            th: ({ ...props }) => <th className="border border-gray-300 px-3 py-2 bg-gray-100 font-bold" {...props} />,
            td: ({ ...props }) => <td className="border border-gray-300 px-3 py-2" {...props} />,
          }}
        >
          {page.content}
        </ReactMarkdown>
      </article>

      {/* Synthesis insights (if available) */}
      {page.synthesized_content && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-xl font-bold mb-4">Synthesis Insights</h3>
          <article className="prose prose-sm md:prose-base max-w-none bg-blue-50 p-4 rounded-lg">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              components={{
                h2: ({ ...props }) => <h4 className="text-lg font-bold mt-3 mb-2" {...props} />,
                h3: ({ ...props }) => <h5 className="text-base font-bold mt-2 mb-1" {...props} />,
              }}
            >
              {page.synthesized_content}
            </ReactMarkdown>
          </article>
        </div>
      )}

      {/* Metadata (mobile: visible, desktop: smaller) */}
      <div className="mt-6 pt-4 border-t border-gray-200 text-xs md:text-sm text-gray-600">
        <p className="mb-1">
          <strong>Last updated:</strong> {new Date(page.updated_at).toLocaleDateString()}
        </p>
        {page.last_synthesis && (
          <p>
            <strong>Last synthesis:</strong> {new Date(page.last_synthesis).toLocaleDateString()}
          </p>
        )}
        {page.contradiction_count > 0 && (
          <p className="text-red-600 mt-2">
            ⚠️ <strong>{page.contradiction_count} contradiction(s) detected</strong>
          </p>
        )}
      </div>
    </div>
  );
}
