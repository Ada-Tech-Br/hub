import { api } from "@/lib/api";
import type { User, PaginatedResponse } from "@/types";

export interface UserFilters {
  page?: number;
  page_size?: number;
  search?: string;
  role?: string;
  type?: string;
  is_active?: boolean;
}

export interface CreateUserData {
  name: string;
  email: string;
  type: string;
  role: string;
  auth_provider: string;
}

export interface UpdateUserData {
  name?: string;
  email?: string;
  type?: string;
  role?: string;
  auth_provider?: string;
  is_active?: boolean;
}

export const usersService = {
  async list(filters: UserFilters = {}): Promise<PaginatedResponse<User>> {
    const params = new URLSearchParams();
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));
    if (filters.search) params.set("search", filters.search);
    if (filters.role) params.set("role", filters.role);
    if (filters.type) params.set("type", filters.type);
    if (filters.is_active !== undefined) params.set("is_active", String(filters.is_active));

    const { data } = await api.get(`/users?${params.toString()}`);
    return data;
  },

  async getById(id: string): Promise<User> {
    const { data } = await api.get(`/users/${id}`);
    return data;
  },

  async create(userData: CreateUserData): Promise<User> {
    const { data } = await api.post("/users", userData);
    return data;
  },

  async update(id: string, userData: UpdateUserData): Promise<User> {
    const { data } = await api.patch(`/users/${id}`, userData);
    return data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/users/${id}`);
  },

  async activate(id: string): Promise<User> {
    const { data } = await api.patch(`/users/${id}/activate`);
    return data;
  },

  async deactivate(id: string): Promise<User> {
    const { data } = await api.patch(`/users/${id}/deactivate`);
    return data;
  },
};
