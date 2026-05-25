'use client';

import { useState, useEffect } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { WikiPage } from '@/lib/types';

interface WikiEditorProps {
  page: WikiPage;
  onSave: (content: string) => Promise<void>;
  onCancel: () => void;
  isSaving?: boolean;
}

/**
 * WikiEditor - Markdown editor with live preview
 * Mobile: Toggle preview, Desktop: Side-by-side preview
 */
export default function WikiEditor({
  page,
  onSave,
  onCancel,
  isSaving = false,
}: WikiEditorProps) {
  const [content, setContent] = useState(page.content);
  const [showPreview, setShowPreview] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(`wiki-${page.slug}-draft`);
    if (saved) {
      setContent(saved);
      setIsDirty(true);
    }
  }, [page.slug]);

  const handleChange = (value?: string) => {
    const newContent = value || '';
    setContent(newContent);
    setIsDirty(true);
    localStorage.setItem(`wiki-${page.slug}-draft`, newContent);
  };

  const handleSave = async () => {
    try {
      await onSave(content);
      localStorage.removeItem(`wiki-${page.slug}-draft`);
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to save:', error);
    }
  };

  const handleCancel = () => {
    if (isDirty && !confirm('You have unsaved changes. Discard them?')) {
      return;
    }
    localStorage.removeItem(`wiki-${page.slug}-draft`);
    onCancel();
  };

  return (
    <div className="w-full h-full flex flex-col bg-white" data-color-mode="light">
      {/* Toolbar */}
      <div className="border-b border-gray-200 p-4 flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">
            {isDirty ? '✏️ Editing' : 'Saved'}
          </span>
        </div>

        {/* Preview toggle (mobile only) */}
        <button
          onClick={() => setShowPreview(!showPreview)}
          className="md:hidden px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 transition-colors"
        >
          {showPreview ? '✏️ Edit' : '👁️ Preview'}
        </button>

        {/* Save/Cancel buttons */}
        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={handleCancel}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 font-medium"
            disabled={isSaving || !isDirty}
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Editor area */}
      <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
        {/* Editor (hide on mobile if preview shown) */}
        <div className={`flex-1 overflow-hidden ${showPreview ? 'hidden md:block' : 'block'}`}>
          <MDEditor
            value={content}
            onChange={handleChange}
            preview="edit"
            hideToolbar={false}
            visibleDragbar={false}
            height="100%"
            className="!border-0 !rounded-0"
            textareaProps={{
              disabled: isSaving,
            }}
            preview="live"
          />
        </div>

        {/* Preview (hide on mobile if edit shown) */}
        <div
          className={`flex-1 overflow-auto border-l border-gray-200 p-4 bg-gray-50 ${
            showPreview ? 'block' : 'hidden md:block'
          }`}
        >
          <div className="prose prose-sm max-w-none">
            {content ? (
              <div>
                {content.split('\n').map((line, i) => {
                  if (line.startsWith('#')) {
                    const level = line.match(/^#+/)?.[0].length || 1;
                    const text = line.replace(/^#+\s/, '');
                    const Heading = `h${level}` as keyof JSX.IntrinsicElements;
                    return (
                      <Heading key={i} className="font-bold my-2">
                        {text}
                      </Heading>
                    );
                  }
                  if (line.trim() === '') {
                    return <br key={i} />;
                  }
                  return (
                    <p key={i} className="my-1">
                      {line}
                    </p>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-400">Start typing to see preview...</p>
            )}
          </div>
        </div>
      </div>

      {/* Draft indicator */}
      {isDirty && (
        <div className="bg-yellow-50 border-t border-yellow-200 px-4 py-2 text-sm text-yellow-800">
          📝 Draft saved locally. Click "Save" to publish changes.
        </div>
      )}
    </div>
  );
}
