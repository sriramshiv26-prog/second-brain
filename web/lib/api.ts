/**
 * API client for wiki operations
 */

import axios, { AxiosInstance } from 'axios';
import {
  WikiPage,
  WikiBacklink,
  WikiSearchResult,
  WikiPageCreateInput,
  WikiPageUpdateInput,
  WikiListResponse,
  WikiSearchResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Wiki API client
 */
export const wikiAPI = {
  /**
   * Get all wiki pages with pagination
   */
  getPages: async (limit: number = 50, offset: number = 0): Promise<WikiPage[]> => {
    try {
      const response = await apiClient.get<WikiPage[]>('/wiki', {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching wiki pages:', error);
      throw error;
    }
  },

  /**
   * Get a specific wiki page by slug
   */
  getPage: async (slug: string): Promise<WikiPage> => {
    try {
      const response = await apiClient.get<WikiPage>(`/wiki/${slug}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching wiki page ${slug}:`, error);
      throw error;
    }
  },

  /**
   * Create a new wiki page
   */
  createPage: async (data: WikiPageCreateInput): Promise<WikiPage> => {
    try {
      const response = await apiClient.post<WikiPage>('/wiki', data);
      return response.data;
    } catch (error) {
      console.error('Error creating wiki page:', error);
      throw error;
    }
  },

  /**
   * Update an existing wiki page
   */
  updatePage: async (slug: string, data: WikiPageUpdateInput): Promise<WikiPage> => {
    try {
      const response = await apiClient.put<WikiPage>(`/wiki/${slug}`, data);
      return response.data;
    } catch (error) {
      console.error(`Error updating wiki page ${slug}:`, error);
      throw error;
    }
  },

  /**
   * Delete a wiki page
   */
  deletePage: async (slug: string): Promise<void> => {
    try {
      await apiClient.delete(`/wiki/${slug}`);
    } catch (error) {
      console.error(`Error deleting wiki page ${slug}:`, error);
      throw error;
    }
  },

  /**
   * Search wiki pages
   */
  searchPages: async (query: string, limit: number = 20): Promise<WikiSearchResult[]> => {
    try {
      const response = await apiClient.get<WikiSearchResult[]>('/wiki/search', {
        params: { q: query, limit },
      });
      return response.data;
    } catch (error) {
      console.error('Error searching wiki pages:', error);
      throw error;
    }
  },

  /**
   * Get backlinks for a wiki page
   */
  getBacklinks: async (slug: string): Promise<WikiBacklink[]> => {
    try {
      const response = await apiClient.get<WikiBacklink[]>(`/wiki/${slug}/backlinks`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching backlinks for ${slug}:`, error);
      throw error;
    }
  },

  /**
   * Get related pages for a wiki page
   */
  getRelatedPages: async (slug: string): Promise<WikiPage[]> => {
    try {
      const response = await apiClient.get<WikiPage[]>(`/wiki/${slug}/related`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching related pages for ${slug}:`, error);
      throw error;
    }
  },
};

/**
 * Graph and Visualization API (for existing pages)
 */
export const graphAPI = {
  getEntityDetail: async (entityId: string) => {
    const response = await apiClient.get(`/graph/entity/${entityId}`);
    return response.data;
  },
  traverseGraph: async (entityId: string, depth: number = 2) => {
    const response = await apiClient.get(`/graph/traverse`, {
      params: { entity_id: entityId, depth },
    });
    return response.data;
  },
};

/**
 * Visualization API (for existing pages)
 */
export const vizAPI = {
  getEntityVisualization: async (entityId: string) => {
    const response = await apiClient.get(`/viz/entity/${entityId}`);
    return response.data;
  },
};

/**
 * Search API (for existing pages)
 */
export const searchAPI = {
  search: async (query: string, limit: number = 20) => {
    const response = await apiClient.get('/search', {
      params: { q: query, limit },
    });
    return response.data;
  },
};

export default apiClient;
