import { api } from "@/lib/api";
import type { TokenResponse, User } from "@/types";

const GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";

export const authService = {
  async requestOtp(email: string): Promise<{ message: string }> {
    const { data } = await api.post("/auth/otp/request", { email });
    return data;
  },

  async verifyOtp(email: string, code: string): Promise<TokenResponse> {
    const { data } = await api.post("/auth/otp/verify", { email, code });
    return data;
  },

  async getMe(): Promise<User> {
    const { data } = await api.get("/auth/me");
    return data;
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const { data } = await api.post("/auth/refresh", { refresh_token: refreshToken });
    return data;
  },

  async exchangeGoogleCode(code: string): Promise<TokenResponse> {
    const { data } = await api.get<TokenResponse>(`/auth/google/callback?code=${code}`);
    return data;
  },

  getGoogleLoginUrl(): string {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/oauth/callback`;

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: "code",
      scope: "openid email profile",
      access_type: "offline",
      prompt: "select_account",
    });

    return `${GOOGLE_OAUTH_URL}?${params.toString()}`;
  },
};
