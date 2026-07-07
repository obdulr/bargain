// Shared types and utilities for BargainHuntrs

export interface User {
  id: string;
  email: string;
  subscription_tier: 'free' | 'hustler' | 'pro' | 'agency';
  created_at: string;
}

export interface Alert {
  id: string;
  user_id: string;
  type: 'price_error' | 'clearance' | 'arbitrage';
  title: string;
  description: string;
  source_url: string;
  potential_profit: number;
  created_at: string;
}

export interface PriceSnapshot {
  id: string;
  item_id: string;
  retailer: string;
  price: number;
  currency: string;
  timestamp: string;
}

export interface WatchlistItem {
  id: string;
  user_id: string;
  item_name: string;
  target_price: number;
  current_price: number;
  retailers: string[];
}

export const SUBSCRIPTION_TIERS = {
  FREE: { name: 'Free', price: 0, alerts_per_day: 5, delay_hours: 24 },
  HUSTLER: { name: 'Hustler', price: 29, alerts_per_day: 50, delay_hours: 0 },
  PRO: { name: 'Pro', price: 79, alerts_per_day: -1, delay_hours: 0 },
  AGENCY: { name: 'Agency', price: 199, alerts_per_day: -1, delay_hours: 0, api_access: true }
} as const;

export const RETAILERS = [
  'amazon',
  'walmart',
  'target',
  'best_buy',
  'ebay',
  'home_depot',
  'lowes'
] as const;

export type Retailer = typeof RETAILERS[number];

// --- Arbitrage Types (Phase 1) ---

export type DealTier = 'glitch' | 'clearance' | 'arbitrage' | 'watch';
export type DealStatus = 'active' | 'alerted' | 'expired' | 'rejected';
export type SellPlatform = 'ebay' | 'amazon_fba' | 'stockx' | 'poshmark' | 'mercari';

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
  deal_tier: DealTier;
  net_profit?: number;
  roi?: number;
  total_costs?: number;
  platform_fee?: number;
  bsr?: number;
  category?: string;
  is_profitable: boolean;
  status: DealStatus;
  detected_at: string;
}

export interface ScanRequest {
  asin?: string;
  category?: string;
  min_discount?: number;
  max_price?: number;
  limit?: number;
  sell_platform?: SellPlatform;
}

export interface ScanResponse {
  scan_id: string;
  products_scanned: number;
  deals_found: number;
  deals: ArbitrageDeal[];
  message?: string;
}

export interface ScanRun {
  id: string;
  scan_type: string;
  products_scanned: number;
  deals_found: number;
  status: string;
  started_at: string;
  completed_at?: string;
}

export interface ArbitrageStats {
  total_profitable_deals: number;
  active_deals: number;
  tier_counts: Record<string, number>;
  recent_scans: ScanRun[];
}
