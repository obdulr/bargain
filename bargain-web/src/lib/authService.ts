const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.bargainhuntrs.com";

const TOKEN_KEY = "bargain_auth_token";
const USER_KEY = "bargain_user_data";
const REFRESH_KEY = "bargain_refresh_token";

export interface AuthUser {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role?: string;
  subscriptionTier?: string;
}

export interface AuthResponse {
  success: boolean;
  user?: AuthUser;
  accessToken?: string;
  refreshToken?: string;
  expiresIn?: number;
  error?: string;
  message?: string;
  status?: number;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  referralCode?: string;
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const data = localStorage.getItem(USER_KEY);
  if (!data) return null;
  try {
    return JSON.parse(data) as AuthUser;
  } catch {
    return null;
  }
}

function storeAuth(accessToken: string, refreshToken: string, user: AuthUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleAuthResponse(response: Response): Promise<AuthResponse> {
  const json = await response.json().catch(() => ({}));

  if (!response.ok) {
    let errorMessage = "Request failed";
    if (response.status === 401) {
      errorMessage = json?.message || "Invalid email or password.";
    } else if (response.status === 409) {
      errorMessage = "An account with this email already exists.";
    } else if (response.status >= 400 && response.status < 500) {
      errorMessage = json?.message || json?.error || "Please check your input and try again.";
    } else {
      errorMessage = json?.message || json?.error || "Server error. Please try again later.";
    }
    return { success: false, error: errorMessage, message: errorMessage, status: response.status };
  }

  const accessToken = json?.accessToken || json?.access_token;
  const refreshToken = json?.refreshToken || json?.refresh_token;
  const user = json?.user as AuthUser | undefined;

  if (accessToken && user) {
    storeAuth(accessToken, refreshToken || "", user);
  }

  return {
    success: true,
    accessToken,
    refreshToken,
    expiresIn: json?.expiresIn,
    user,
  };
}

class AuthService {
  async login(data: LoginData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: data.email, password: data.password }),
      });
      return handleAuthResponse(response);
    } catch (error) {
      return { success: false, error: "Network error", message: (error as Error).message };
    }
  }

  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return handleAuthResponse(response);
    } catch (error) {
      return { success: false, error: "Network error", message: (error as Error).message };
    }
  }

  async getProfile(): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/profile`, {
        method: "GET",
        headers: getAuthHeaders(),
      });
      const json = await response.json().catch(() => ({}));
      if (!response.ok) {
        return { success: false, error: json?.message || "Failed to load profile" };
      }
      return { success: true, user: json as AuthUser };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  }

  async refreshAccessToken(): Promise<AuthResponse> {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) return { success: false, error: "No refresh token" };

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: refreshToken }),
      });
      const json = await response.json().catch(() => ({}));
      if (!response.ok) {
        clearAuth();
        return { success: false, error: json?.message || "Session expired" };
      }
      const accessToken = json?.accessToken || json?.access_token;
      if (accessToken && typeof window !== "undefined") {
        localStorage.setItem(TOKEN_KEY, accessToken);
      }
      return { success: true, accessToken };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  }

  logout(): void {
    clearAuth();
  }

  getToken(): string | null {
    return getStoredToken();
  }

  getUser(): AuthUser | null {
    return getStoredUser();
  }

  isAuthenticated(): boolean {
    return !!getStoredToken();
  }
}

export const authService = new AuthService();
