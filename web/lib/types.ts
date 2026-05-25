/**
 * Wiki and related types for Second Brain
 */

export interface WikiPage {
  id: string;
  slug: string;
  title: string;
  content: string;
  synthesized_content?: string;
  entity_ids?: string[];
  contradiction_count: number;
  version: number;
  created_at: string;
  updated_at: string;
  last_synthesis?: string;
}

export interface WikiBacklink {
  from_slug: string;
  to_slug: string;
  context?: string;
  created_at: string;
}

export interface WikiSearchResult {
  slug: string;
  title: string;
  excerpt: string;
  relevance: number;
}

export interface WikiPageCreateInput {
  slug: string;
  title: string;
  content: string;
  entity_ids?: string[];
}

export interface WikiPageUpdateInput {
  title?: string;
  content?: string;
  synthesized_content?: string;
}

export interface WikiListResponse {
  pages: WikiPage[];
  total: number;
  limit: number;
  offset: number;
}

export interface WikiSearchResponse {
  query: string;
  total: number;
  results: WikiSearchResult[];
}
