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
