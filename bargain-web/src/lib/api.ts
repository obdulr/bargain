const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.bargainhuntrs.com";

async function fetchWithAuth(endpoint: string, token: string | null, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

export async function getCurrentUser(token: string) {
  return fetchWithAuth("/api/v1/auth/me", token, {
    method: "GET",
  });
}

export async function getWatchlist(token: string) {
  return fetchWithAuth("/api/v1/watchlist", token, {
    method: "GET",
  });
}

export async function addWatchlistItem(
  token: string,
  item_name: string,
  retailer_url: string,
  target_price?: number
) {
  return fetchWithAuth("/api/v1/watchlist", token, {
    method: "POST",
    body: JSON.stringify({ item_name, retailer_url, target_price }),
  });
}

export async function refreshWatchlistItem(token: string, itemId: string) {
  return fetchWithAuth(`/api/v1/watchlist/${itemId}/refresh`, token, {
    method: "POST",
  });
}

export async function deleteWatchlistItem(token: string, itemId: string) {
  return fetchWithAuth(`/api/v1/watchlist/${itemId}`, token, {
    method: "DELETE",
  });
}