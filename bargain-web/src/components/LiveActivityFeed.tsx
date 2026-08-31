"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getPublicDeals, type ArbitrageDeal } from "@/lib/api";

// ─── Helpers ───────────────────────────────────────────────────────────────

const NAMES = [
  "Sarah", "Mike", "Jessica", "Tyler", "Ashley", "James", "Rachel",
  "Daniel", "Amanda", "Brandon", "Emma", "Jacob", "Olivia", "Noah",
  "Sophia", "Mason", "Ava", "Logan", "Grace", "Ethan",
];

const RETAILER_LABELS: Record<string, string> = {
  amazon: "Amazon",
  home_depot: "Home Depot",
  ace_hardware: "Ace Hardware",
  ace: "Ace Hardware",
  corsair: "Corsair",
  walmart: "Walmart",
  target: "Target",
  best_buy: "Best Buy",
  bestbuy: "Best Buy",
  costco: "Costco",
  lowes: "Lowe's",
  ebay: "eBay",
  ador: "ADOR",
  eufy: "Eufy",
  belkin: "Belkin",
  lenovo: "Lenovo",
  abebooks: "AbeBooks",
  barkbox: "BarkBox",
  golf_partner: "GOLF Partner",
  umbra: "Umbra",
  wine_express: "Wine Express",
  namecheap: "Namecheap",
  envato: "Envato",
  invideo: "InVideo",
  canva: "Canva",
  overstock: "Overstock",
  bhphoto: "B&H Photo",
  woot: "Woot",
  newegg: "Newegg",
  adorama: "Adorama",
  monoprice: "Monoprice",
};

function retailerLabel(retailer?: string): string {
  if (!retailer) return "Amazon";
  return RETAILER_LABELS[retailer.toLowerCase()] ||
    retailer.charAt(0).toUpperCase() + retailer.slice(1).replace(/_/g, " ");
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n).trimEnd() + "…";
}

function discountPercent(deal: ArbitrageDeal): number {
  if (deal.historical_avg && deal.historical_avg > deal.buy_price) {
    return Math.round((1 - deal.buy_price / deal.historical_avg) * 100);
  }
  if (deal.original_buy_price && deal.original_buy_price > deal.buy_price) {
    return Math.round((1 - deal.buy_price / deal.original_buy_price) * 100);
  }
  return 0;
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomTimeAgo(): string {
  const r = Math.random();
  if (r < 0.5) return `${Math.floor(Math.random() * 30) + 3}s ago`;
  if (r < 0.85) return `${Math.floor(Math.random() * 9) + 1}m ago`;
  return `${Math.floor(Math.random() * 3) + 1}m ago`;
}

interface ActivityNotification {
  icon: string;
  message: string;
  timeAgo: string;
}

function buildNotification(deal: ArbitrageDeal): ActivityNotification {
  const name = pick(NAMES);
  const title = truncate(deal.title, 40);
  const discount = discountPercent(deal);
  const retailer = retailerLabel(deal.retailer);
  const netProfit = deal.net_profit ?? 0;

  const templates: ActivityNotification[] = [];

  // 🔥 Hot deal (snagged)
  if (deal.historical_avg && deal.historical_avg > deal.buy_price) {
    templates.push({
      icon: "🔥",
      message: `${name} just snagged ${title} for $${deal.buy_price.toFixed(0)} (was $${deal.historical_avg.toFixed(0)})`,
      timeAgo: randomTimeAgo(),
    });
  }

  // 📦 New deal alert
  templates.push({
    icon: "📦",
    message: `New deal alert: ${title} dropped to $${deal.buy_price.toFixed(0)} at ${retailer}`,
    timeAgo: randomTimeAgo(),
  });

  // 💰 Profit
  if (netProfit > 0) {
    templates.push({
      icon: "💰",
      message: `${name} could profit $${netProfit.toFixed(0)} on ${truncate(deal.title, 30)}`,
      timeAgo: randomTimeAgo(),
    });
  }

  // 🏷️ Discount
  if (discount > 0) {
    templates.push({
      icon: "🏷️",
      message: `${discount}% off: ${title} — now $${deal.buy_price.toFixed(0)}`,
      timeAgo: randomTimeAgo(),
    });
  }

  return pick(templates.length ? templates : [{
    icon: "📦",
    message: `New deal alert: ${title} dropped to $${deal.buy_price.toFixed(0)} at ${retailer}`,
    timeAgo: randomTimeAgo(),
  }]);
}

// ─── Component ─────────────────────────────────────────────────────────────

export default function LiveActivityFeed() {
  const [deals, setDeals] = useState<ArbitrageDeal[]>([]);
  const [current, setCurrent] = useState<ActivityNotification | null>(null);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const indexRef = useRef(0);

  // Fetch deals on mount (fail silently — this is non-critical social proof)
  useEffect(() => {
    let cancelled = false;
    getPublicDeals(20, 0)
      .then((data) => {
        if (cancelled || !data || data.length === 0) return;
        setDeals(data);
      })
      .catch(() => {
        // Non-critical; do nothing
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Build a shuffled queue of notifications from the deals
  const queue = useMemo<ActivityNotification[]>(() => {
    if (deals.length === 0) return [];
    return deals.map((d) => buildNotification(d));
  }, [deals]);

  // Cycle through notifications
  useEffect(() => {
    if (dismissed || queue.length === 0) return;

    const showNext = () => {
      const idx = indexRef.current % queue.length;
      indexRef.current += 1;
      setCurrent(queue[idx]);
      setVisible(true);
    };

    // Initial show after a short delay
    const initialTimer = setTimeout(showNext, 1500);

    return () => clearTimeout(initialTimer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queue, dismissed]);

  // Auto-cycle every 4-5s with fade transition
  useEffect(() => {
    if (dismissed || queue.length === 0) return;

    const interval = setInterval(() => {
      // Fade out, then swap, then fade in
      setVisible(false);
      setTimeout(() => {
        const idx = indexRef.current % queue.length;
        indexRef.current += 1;
        setCurrent(queue[idx]);
        setVisible(true);
      }, 400);
    }, 4500);

    return () => clearInterval(interval);
  }, [queue, dismissed]);

  if (dismissed || !current) return null;

  return (
    <div
      className={`fixed bottom-4 left-4 z-50 hidden sm:block transition-all duration-400 ease-in-out ${
        visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2 pointer-events-none"
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3 rounded-xl bg-zinc-900/95 px-4 py-3 shadow-lg ring-1 ring-zinc-800 backdrop-blur-sm max-w-xs dark:bg-zinc-900/95 dark:ring-zinc-700">
        <span className="text-xl leading-none mt-0.5" aria-hidden="true">
          {current.icon}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white leading-snug">
            {current.message}
          </p>
          <p className="mt-0.5 text-xs text-zinc-400">
            {current.timeAgo}
          </p>
        </div>
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss notification"
          className="flex-shrink-0 -mt-0.5 -mr-1 rounded-md p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
