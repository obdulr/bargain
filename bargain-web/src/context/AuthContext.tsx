"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { authService, type AuthUser } from "@/lib/authService";

interface AuthContextType {
  user: AuthUser | null;
  idToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  logout: () => void;
  refresh: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  idToken: null,
  isAuthenticated: false,
  loading: true,
  logout: () => {},
  refresh: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function loadAuth() {
    const token = authService.getToken();
    const currentUser = authService.getUser();
    setIdToken(token);
    setUser(currentUser);
    setLoading(false);
  }

  useEffect(() => {
    loadAuth();

    function handleStorage(event: StorageEvent) {
      if (event.key === "bargain_auth_token" || event.key === "bargain_user_data") {
        loadAuth();
      }
    }

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  function logout() {
    authService.logout();
    setUser(null);
    setIdToken(null);
  }

  function refresh() {
    loadAuth();
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        idToken,
        isAuthenticated: !!idToken && !!user,
        loading,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
