import type { ArbitrageDeal } from "@/lib/api";

export function discountPercent(deal: ArbitrageDeal): number {
  if (deal.historical_avg && deal.historical_avg > deal.buy_price) {
    return Math.round((1 - deal.buy_price / deal.historical_avg) * 100);
  }
  if (deal.original_buy_price && deal.original_buy_price > deal.buy_price) {
    return Math.round((1 - deal.buy_price / deal.original_buy_price) * 100);
  }
  return 0;
}

export function savingsAmount(deal: ArbitrageDeal): number {
  if (deal.historical_avg && deal.historical_avg > deal.buy_price) {
    return deal.historical_avg - deal.buy_price;
  }
  if (deal.original_buy_price && deal.original_buy_price > deal.buy_price) {
    return deal.original_buy_price - deal.buy_price;
  }
  return 0;
}

export function retailerName(retailer?: string): string {
  if (!retailer) return "Amazon";
  const map: Record<string, string> = {
    amazon: "Amazon",
    walmart: "Walmart",
    target: "Target",
    best_buy: "Best Buy",
    bestbuy: "Best Buy",
    home_depot: "Home Depot",
    homedepot: "Home Depot",
    lowes: "Lowe's",
    costco: "Costco",
    ebay: "eBay",
    newegg: "Newegg",
    woot: "Woot",
    bhphoto: "B&H Photo",
  };
  return (
    map[retailer.toLowerCase()] ||
    retailer.charAt(0).toUpperCase() + retailer.slice(1).replace(/_/g, " ")
  );
}

export function timeAgo(detectedAt: string): string {
  const diff = Date.now() - new Date(detectedAt).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function isToday(detectedAt: string): boolean {
  const d = new Date(detectedAt);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export { addUtmParameters } from "@/lib/api";
