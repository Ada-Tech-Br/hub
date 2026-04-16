import { api } from "@/lib/api";
import type {
  Content, ContentListItem, PaginatedResponse, ContentAccessResponse,
  SnippetResponse, AccessControlResponse, AccessMode,
} from "@/types";

export interface ContentFilters {
  page?: number;
  page_size?: number;
  search?: string;
  type?: string;
}

export interface CreateContentData {
  title: string;
  description?: string;
  type: string;
  icon?: string;
  is_public: boolean;
  external_url?: string;
}

export interface UpdateContentData {
  title?: string;
  description?: string;
  icon?: string;
  is_public?: boolean;
  external_url?: string;
}

export const contentService = {
  async list(filters: ContentFilters = {}): Promise<PaginatedResponse<ContentListItem>> {
    const params = new URLSearchParams();
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));
    if (filters.search) params.set("search", filters.search);
    if (filters.type) params.set("type", filters.type);

    const { data } = await api.get(`/content?${params.toString()}`);
    return data;
  },

  async getById(id: string): Promise<Content> {
    const { data } = await api.get(`/content/${id}`);
    return data;
  },

  async create(contentData: CreateContentData): Promise<Content> {
    const { data } = await api.post("/content", contentData);
    return data;
  },

  async update(id: string, contentData: UpdateContentData): Promise<Content> {
    const { data } = await api.patch(`/content/${id}`, contentData);
    return data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/content/${id}`);
  },

  async uploadFile(contentId: string, file: File): Promise<Content> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post(`/content/upload?content_id=${contentId}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async getAccess(id: string): Promise<ContentAccessResponse> {
    const { data } = await api.get(`/content/${id}/access`);
    return data;
  },

  async getSnippet(id: string): Promise<SnippetResponse> {
    const { data } = await api.get(`/content/${id}/snippet`);
    return data;
  },

  async getAccessControl(id: string): Promise<AccessControlResponse> {
    const { data } = await api.get(`/content/${id}/access-control`);
    return data;
  },

  async setAccessMode(id: string, mode: AccessMode): Promise<AccessControlResponse> {
    const { data } = await api.patch(`/content/${id}/access-control`, { access_mode: mode });
    return data;
  },

  async grantUsers(id: string, userIds: string[]): Promise<AccessControlResponse> {
    const { data } = await api.post(`/content/${id}/access-control/users`, { user_ids: userIds });
    return data;
  },

  async revokeUser(id: string, userId: string): Promise<void> {
    await api.delete(`/content/${id}/access-control/users/${userId}`);
  },
};
