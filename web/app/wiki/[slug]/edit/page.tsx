'use client';

import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import WikiEditor from '@/components/wiki/WikiEditor';
import { wikiAPI } from '@/lib/api';

/**
 * Wiki Edit Page
 * Responsive editor for mobile and desktop
 */
export default function WikiEditPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params?.slug as string;

  // Fetch wiki page
  const {
    data: page,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['wiki-page', slug],
    queryFn: () => (slug ? wikiAPI.getPage(slug) : Promise.reject('No slug')),
    enabled: !!slug,
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!slug) throw new Error('No slug');
      await wikiAPI.updatePage(slug, { content });
    },
    onSuccess: () => {
      router.push(`/wiki/${slug}`);
    },
    onError: (error) => {
      alert(`Failed to save: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  if (!slug) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <p className="text-gray-600">Loading page...</p>
      </div>
    );
  }

  if (error || !page) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h2>
          <p className="text-gray-600 mb-6">Unable to load the wiki page for editing.</p>
          <Link
            href="/wiki"
            className="inline-block px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Wiki
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="h-screen bg-white flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Editing: {page.title}</h1>
            <p className="text-sm text-gray-600 mt-1">
              Last updated: {new Date(page.updated_at).toLocaleDateString()}
            </p>
          </div>
          <Link
            href={`/wiki/${slug}`}
            className="text-gray-600 hover:text-gray-900"
          >
            ✕
          </Link>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <WikiEditor
          page={page}
          onSave={(content) => updateMutation.mutateAsync(content)}
          onCancel={() => router.push(`/wiki/${slug}`)}
          isSaving={updateMutation.isPending}
        />
      </div>
    </main>
  );
}
