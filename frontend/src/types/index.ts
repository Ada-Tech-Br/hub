export type UserType = "internal" | "external";
export type UserRole = "admin" | "user";
export type AuthProvider = "google" | "otp";
export type ContentType = "project" | "file";
export type FileType = "html" | "zip" | "external";

export interface User {
  id: string;
  name: string;
  email: string;
  type: UserType;
  role: UserRole;
  auth_provider: AuthProvider;
  is_active: boolean;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Content {
  id: string;
  title: string;
  description: string | null;
  type: ContentType;
  icon: string | null;
  is_public: boolean;
  external_url: string | null;
  file_type: FileType | null;
  s3_path: string | null;
  uploaded_file_path: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentListItem {
  id: string;
  title: string;
  description: string | null;
  type: ContentType;
  icon: string | null;
  is_public: boolean;
  external_url: string | null;
  file_type: FileType | null;
  s3_path: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ContentAccessResponse {
  access_url: string;
  type: ContentType;
  file_type: FileType | null;
}

export interface SnippetResponse {
  content_id: string;
  snippet: string;
}

export interface ApiError {
  detail: string;
}
