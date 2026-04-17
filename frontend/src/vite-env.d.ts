/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  /** Comma-separated; if exactly one value, adds OAuth `hd` (Google account picker). */
  readonly VITE_GOOGLE_ALLOWED_EMAIL_DOMAINS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
