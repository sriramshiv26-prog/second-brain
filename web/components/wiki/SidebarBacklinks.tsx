'use client';

import Link from 'next/link';
import { WikiBacklink } from '@/lib/types';

interface SidebarBacklinksProps {
  backlinks: WikiBacklink[];
  isLoading?: boolean;
}

/**
 * SidebarBacklinks - Shows related pages that link to current page
 * Mobile: Collapsible via hamburger, Desktop: Always visible
 */
export default function SidebarBacklinks({
  backlinks,
  isLoading = false,
}: SidebarBacklinksProps) {
  if (backlinks.length === 0 && !isLoading) {
    return null;
  }

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
        🔗 Backlinks {backlinks.length > 0 && `(${backlinks.length})`}
      </h3>

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-6 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <ul className="space-y-2">
          {backlinks.map((backlink) => (
            <li key={`${backlink.from_slug}-${backlink.to_slug}`}>
              <Link
                href={`/wiki/${backlink.to_slug}`}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium block truncate"
                title={backlink.to_slug}
              >
                {backlink.context ? backlink.context : backlink.to_slug}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
