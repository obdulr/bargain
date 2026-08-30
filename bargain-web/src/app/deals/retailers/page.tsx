import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { getPublicDeals, type ArbitrageDeal } from "@/lib/api";

export const metadata: Metadata = {
  title: "Browse Deals by Retailer | BargainHuntrs",
  description:
    "Browse deals by retailer — Amazon, Walmart, Lowe's, Best Buy, and more. Find arbitrage opportunities from your favorite stores.",
  alternates: { canonical: "/deals/retailers" },
  openGraph: {
    title: "Browse Deals by Retailer | BargainHuntrs",
    description:
      "Browse deals by retailer — Amazon, Walmart, Lowe's, Best Buy, and more.",
    url: "/deals/retailers",
  },
};

const RETAILER_META: Record<
  string,
  { name: string; emoji: string; color: string }
> = {
  amazon: { name: "Amazon", emoji: "📦", color: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400" },
  walmart: { name: "Walmart", emoji: "🛒", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" },
  target: { name: "Target", emoji: "🎯", color: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400" },
  best_buy: { name: "Best Buy", emoji: "🔌", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" },
  bestbuy: { name: "Best Buy", emoji: "🔌", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" },
  home_depot: { name: "Home Depot", emoji: "🔨", color: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400" },
  homedepot: { name: "Home Depot", emoji: "🔨", color: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400" },
  lowes: { name: "Lowe's", emoji: "🪚", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" },
  costco: { name: "Costco", emoji: "🏬", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" },
  ebay: { name: "eBay", emoji: "🏷️", color: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400" },
  newegg: { name: "Newegg", emoji: "🥚", color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400" },
  woot: { name: "Woot", emoji: "🎉", color: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400" },
  bhphoto: { name: "B&H Photo", emoji: "📷", color: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400" },
  overstock: { name: "Overstock", emoji: "🛋️", color: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400" },
  corsair: { name: "Corsair", emoji: "🎮", color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400" },
  lenovo: { name: "Lenovo", emoji: "💻", color: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400" },
};

function retailerMeta(key: string) {
  return (
    RETAILER_META[key.toLowerCase()] || {
      name: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " "),
      emoji: "🏷️",
      color: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
    }
  );
}

export default async function RetailersPage() {
  let deals: ArbitrageDeal[] = [];
  let error = "";
  try {
    deals = await getPublicDeals(200, 0);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load deals";
  }

  // Count deals per retailer
  const counts = new Map<string, number>();
  for (const deal of deals) {
    const key = (deal.retailer || "amazon").toLowerCase();
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const retailers = Array.from(counts.entries())
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />

      <main className="flex-1 px-6 py-10">
        <div className="mx-auto max-w-5xl">
          <Link
            href="/deals"
            className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
          >
            ← Back to all deals
          </Link>

          <h1 className="mt-4 text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Browse Deals by Retailer
          </h1>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            Find arbitrage opportunities from your favorite stores. Deal counts
            update in real time as our scanners find new bargains.
          </p>

          {error ? (
            <div className="mt-8 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950 dark:text-red-400">
              {error}
            </div>
          ) : retailers.length === 0 ? (
            <div className="mt-12 text-center">
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                No retailers with deals available right now. Check back soon.
              </p>
            </div>
          ) : (
            <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {retailers.map(({ key, count }) => {
                const meta = retailerMeta(key);
                return (
                  <Link
                    key={key}
                    href={`/deals?retailer=${encodeURIComponent(key)}`}
                    className="group flex flex-col items-center justify-center rounded-2xl border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
                  >
                    <span className="text-4xl">{meta.emoji}</span>
                    <span className={`mt-3 rounded-md px-2 py-0.5 text-xs font-medium ${meta.color}`}>
                      {meta.name}
                    </span>
                    <span className="mt-2 text-2xl font-bold text-zinc-900 dark:text-zinc-50">
                      {count}
                    </span>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {count === 1 ? "deal" : "deals"}
                    </span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
