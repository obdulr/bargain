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

async function fetchPublic(endpoint: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

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

// ─── Coupons ────────────────────────────────────────────────────────────────

export interface Coupon {
  id: string;
  code: string;
  retailer: string;
  title: string;
  description?: string;
  discount_type: string;
  discount_value: number;
  min_purchase?: number;
  max_discount?: number;
  category?: string;
  product_url?: string;
  source: string;
  source_url?: string;
  expires_at?: string;
  verified: boolean;
  times_used: number;
  success_count: number;
  status: string;
  scraped_at: string;
}

export async function getCoupons(
  token: string,
  params?: { retailer?: string; category?: string; verified_only?: boolean; limit?: number }
) {
  const qs = new URLSearchParams();
  if (params?.retailer) qs.set("retailer", params.retailer);
  if (params?.category) qs.set("category", params.category);
  if (params?.verified_only) qs.set("verified_only", "true");
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return fetchWithAuth(`/api/v1/coupons${query ? `?${query}` : ""}`, token, { method: "GET" }) as Promise<Coupon[]>;
}

export async function getPublicCoupons(
  limit = 50,
  offset = 0,
  params?: { retailer?: string; verified_only?: boolean }
) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  if (params?.retailer) qs.set("retailer", params.retailer);
  if (params?.verified_only) qs.set("verified_only", "true");
  const res = await fetch(`${API_URL}/api/v1/coupons/public?${qs.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch coupons: ${res.status}`);
  return res.json() as Promise<Coupon[]>;
}

export async function getPublicCouponRetailers() {
  const res = await fetch(`${API_URL}/api/v1/coupons/public/retailers`);
  if (!res.ok) return [];
  return res.json() as Promise<string[]>;
}

export async function searchCoupons(token: string, q: string, retailer?: string) {
  const qs = new URLSearchParams({ q });
  if (retailer) qs.set("retailer", retailer);
  return fetchWithAuth(`/api/v1/coupons/search?${qs.toString()}`, token, { method: "GET" }) as Promise<Coupon[]>;
}

export async function getCouponRetailers(token: string) {
  return fetchWithAuth("/api/v1/coupons/retailers", token, { method: "GET" }) as Promise<string[]>;
}

export async function getCouponStatus(token: string) {
  return fetchWithAuth("/api/v1/coupons/status", token, { method: "GET" }) as Promise<{
    configured: boolean;
    source: string | null;
    message: string;
  }>;
}

export async function scrapeCoupons(token: string, retailers?: string[]) {
  return fetchWithAuth("/api/v1/coupons/scrape", token, {
    method: "POST",
    body: JSON.stringify({ retailers: retailers || null }),
  }) as Promise<{ scraped: number; saved: number; errors: number }>;
}

export async function applyCouponToDeal(token: string, dealId: string, couponId: string) {
  return fetchWithAuth("/api/v1/coupons/apply", token, {
    method: "POST",
    body: JSON.stringify({ deal_id: dealId, coupon_id: couponId }),
  }) as Promise<{
    deal_id: string;
    original_buy_price: number;
    effective_buy_price: number;
    coupon_code: string;
    coupon_discount: number;
    original_net_profit?: number;
    new_net_profit?: number;
    original_roi?: number;
    new_roi?: number;
  }>;
}

export async function getBestCouponsForDeal(token: string, dealId: string) {
  return fetchWithAuth(`/api/v1/coupons/deal/${dealId}/best`, token, { method: "GET" }) as Promise<Coupon[]>;
}

// ─── Arbitrage Deals ────────────────────────────────────────────────────────

export interface ArbitrageDeal {
  id: string;
  asin: string;
  title: string;
  image_url?: string;
  buy_url?: string;
  buy_price: number;
  sell_price: number;
  historical_avg?: number;
  discrepancy?: number;
  deal_tier: string;
  retailer?: string;
  deal_source?: string;
  net_profit?: number;
  roi?: number;
  total_costs?: number;
  platform_fee?: number;
  bsr?: number;
  category?: string;
  niche?: string;
  is_profitable: boolean;
  status: string;
  detected_at: string;
  applied_coupon_code?: string;
  coupon_discount?: number;
  original_buy_price?: number;
}

export interface Niche {
  key: string;
  name: string;
  emoji: string;
  description: string;
  typical_margin: string;
}

export async function getDeals(
  token: string,
  params?: { tier?: string; niche?: string; min_profit?: number; limit?: number; offset?: number }
) {
  const qs = new URLSearchParams();
  if (params?.tier) qs.set("tier", params.tier);
  if (params?.niche) qs.set("niche", params.niche);
  if (params?.min_profit) qs.set("min_profit", String(params.min_profit));
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const query = qs.toString();
  return fetchWithAuth(`/api/v1/arbitrage/deals${query ? `?${query}` : ""}`, token, { method: "GET" }) as Promise<ArbitrageDeal[]>;
}

export async function getNiches(token: string) {
  return fetchWithAuth("/api/v1/arbitrage/niches", token, { method: "GET" }) as Promise<Niche[]>;
}

export async function scanNiche(token: string, niche: string, maxProducts = 20) {
  const qs = new URLSearchParams({ max_products: String(maxProducts) });
  return fetchWithAuth(`/api/v1/arbitrage/scan/${niche}?${qs.toString()}`, token, {
    method: "POST",
  }) as Promise<{
    scan_id: string;
    niche: string;
    products_scanned: number;
    deals_found: number;
    deals: ArbitrageDeal[];
  }>;
}

export async function getDealStats(token: string) {
  return fetchWithAuth("/api/v1/arbitrage/stats", token, { method: "GET" });
}

// ─── Niche Preferences ──────────────────────────────────────────────────────

export async function getMyNiches(token: string) {
  return fetchWithAuth("/api/v1/auth/me/niches", token, { method: "GET" }) as Promise<{
    subscribed_niches: string[];
    available_niches: Niche[];
  }>;
}

export async function updateMyNiches(token: string, subscribed_niches: string[]) {
  return fetchWithAuth("/api/v1/auth/me/niches", token, {
    method: "PUT",
    body: JSON.stringify({ subscribed_niches }),
  }) as Promise<{ success: boolean; subscribed_niches: string[] }>;
}

// ─── Affiliate Click Tracking ───────────────────────────────────────────────

export async function trackAffiliateClick(
  token: string,
  data: { url: string; retailer?: string; asin?: string; deal_id?: string }
) {
  return fetchWithAuth("/api/v1/affiliate/click", token, {
    method: "POST",
    body: JSON.stringify(data),
  }) as Promise<{
    affiliate_url: string;
    original_url: string;
    retailer: string;
    tracked: boolean;
  }>;
}

// ─── Price Prediction ───────────────────────────────────────────────────────

export interface PriceTrend {
  recommendation: "buy_now" | "wait" | "monitor";
  confidence: number;
  predicted_low: number | null;
  current_vs_predicted: number;
  trend: "decreasing" | "stable" | "increasing";
  volatility: number;
  days_to_lowest: number;
  message?: string;
}

export interface DealQuality {
  score: number;
  method: string;
  percentile_rank?: number;
  z_score?: number;
  recent_trend_pct?: number;
}

export interface PricePrediction {
  deal_id: string;
  asin: string;
  current_price: number;
  trend?: PriceTrend;
  deal_quality?: DealQuality;
  recommendation?: string;
  tier: string;
  message?: string;
}

export async function getPricePrediction(token: string, dealId: string) {
  return fetchWithAuth(`/api/v1/arbitrage/deals/${dealId}/prediction`, token, {
    method: "GET",
  }) as Promise<PricePrediction>;
}

// ─── Notifications ──────────────────────────────────────────────────────────

export interface ChannelStatus {
  channel: string;
  configured: boolean;
}

export interface NotificationLogEntry {
  id: string;
  asin?: string;
  channel: string;
  recipient?: string;
  status: string;
  error?: string;
  sent_at?: string;
  created_at: string;
}

export async function getNotificationChannels(token: string) {
  return fetchWithAuth("/api/v1/notifications/channels", token, { method: "GET" }) as Promise<ChannelStatus[]>;
}

export async function getNotificationHistory(token: string, channel?: string, limit?: number) {
  const qs = new URLSearchParams();
  if (channel) qs.set("channel", channel);
  if (limit) qs.set("limit", String(limit));
  const query = qs.toString();
  return fetchWithAuth(`/api/v1/notifications/history${query ? `?${query}` : ""}`, token, { method: "GET" }) as Promise<NotificationLogEntry[]>;
}

export async function testNotifications(token: string) {
  return fetchWithAuth("/api/v1/notifications/test", token, { method: "POST" }) as Promise<{ results: Record<string, boolean> }>;
}

export async function distributeDeal(token: string, dealId: string) {
  return fetchWithAuth(`/api/v1/notifications/deal/${dealId}/distribute`, token, { method: "POST" }) as Promise<{ results: Record<string, boolean> }>;
}

// ─── Public Deals (no auth required) ────────────────────────────────────────

export async function getPublicDeals(limit = 20, offset = 0) {
  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return fetchPublic(`/api/v1/arbitrage/deals/public?${qs.toString()}`, {
    method: "GET",
  }) as Promise<ArbitrageDeal[]>;
}

export async function clickAffiliatePublic(data: {
  url: string;
  retailer?: string;
  asin?: string;
  deal_id?: string;
}) {
  return fetchPublic("/api/v1/affiliate/click/public", {
    method: "POST",
    body: JSON.stringify(data),
  }) as Promise<{
    affiliate_url: string;
    original_url: string;
    retailer: string;
    tracked: boolean;
  }>;
}