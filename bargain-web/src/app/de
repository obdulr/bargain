"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  getDeals,
  getDealStats,
  type ArbitrageDeal,
} from "@/lib/api";

export default function DealsPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();

  const [deals, setDeals] = useState<ArbitrageDeal[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [selectedTier, setSelectedTier] = useState<string>("");
  const [minProfit, setMinProfit] = useState<string>("");
  const [loadingDeals, setLoadingDeals] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const loadDeals = useCallback(async () => {
    if (!idToken) return;
    setLoadingDeals(true);
    setError("");
    try {
      const data = await getDeals(idToken, {
        tier: selectedTier || undefined,
        min_profit: minProfit ? parseFloat(minProfit) : undefined,
        limit: 100,
      });
      setDeals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load deals");
    } finally {
      setLoadingDeals(false);
    }
  }, [idToken, selectedTier, minProfit]);

  const loadStats = useCallback(async () => {
    if (!idToken) return;
    try {
      const data = await getDealStats(idToken);
      setStats(data);
    } catch {
      // Non-critical
    }
  }, [idToken]);

  useEffect(() => {
    if (idToken) {
      loadDeals();
      loadStats();
    }
  }, [idToken, loadDeals, loadStats]);

  function formatTier(tier: string): { label: string; color: string } {
    switch (tier) {
      case "glitch":
        return { label: "⚡ GLITCH", color: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400" };
      case "clearance":
        return { label: "CLEARANCE", color: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400" };
      case "arbitrage":
        return { label: "ARBITRAGE", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400" };
      case "watch":
        return { label: "WATCH", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" };
      default:
        return { label: tier.toUpperCase(), color: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400" };
    }
  }

  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />

      <main className="flex-1">
        {/* Header */}
        <section className="px-6 py-10 border-b border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Deal Feed
            </h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Live arbitrage opportunities scraped from 500+ retailers. Sorted by profit.
            </p>

            {/* Stats */}
            {stats && (
              <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Total Deals</p>
                  <p className="mt-1 text-xl font-bold text-zinc-900 dark:text-zinc-50">
                    {stats.total_profitable_deals ?? 0}
                  </p>
                </div>
                <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Active</p>
                  <p className="mt-1 text-xl font-bold text-emerald-600 dark:text-emerald-400">
                    {stats.active_deals ?? 0}
                  </p>
                </div>
                {stats.tier_counts &&
                  Object.entries(stats.tier_counts).map(([tier, count]: [string, any]) => (
                    <div key={tier} className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
                      <p className="text-xs text-zinc-500 dark:text-zinc-400">{tier}</p>
                      <p className="mt-1 text-xl font-bold text-zinc-900 dark:text-zinc-50">{count}</p>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </section>

        {/* Filters */}
        <section className="px-6 py-4 border-b border-zinc-100 dark:border-zinc-800/60">
          <div className="mx-auto max-w-6xl flex flex-wrap items-center gap-4">
            <select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All tiers</option>
              <option value="glitch">⚡ Glitch</option>
              <option value="clearance">Clearance</option>
              <option value="arbitrage">Arbitrage</option>
              <option value="watch">Watch</option>
            </select>

            <input
              type="number"
              value={minProfit}
              onChange={(e) => setMinProfit(e.target.value)}
              placeholder="Min profit $"
              className="w-32 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />

            {(selectedTier || minProfit) && (
              <button
                onClick={() => {
                  setSelectedTier("");
                  setMinProfit("");
                }}
                className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
              >
                Clear filters
              </button>
            )}
          </div>
        </section>

        {/* Deals list */}
        <section className="px-6 py-8">
          <div className="mx-auto max-w-6xl">
            {error && (
              <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950 dark:text-red-400">
                {error}
              </div>
            )}

            {loadingDeals ? (
              <div className="flex justify-center py-20">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-200 border-t-emerald-500" />
              </div>
            ) : deals.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  No deals found yet. Deals appear here when the scanner finds profitable arbitrage opportunities.
                </p>
              </div>
            ) : (
              <>
                <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
                  {deals.length} deal{deals.length !== 1 ? "s" : ""}
                </p>
                <div className="space-y-3">
                  {deals.map((deal) => {
                    const tier = formatTier(deal.deal_tier);
                    return (
                      <div
                        key={deal.id}
                        className="rounded-xl border border-zinc-200 bg-white p-5 transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
                      >
                        <div className="flex gap-4">
                          {/* Image */}
                          {deal.image_url && (
                            <img
                              src={deal.image_url}
                              alt={deal.title}
                              className="h-20 w-20 rounded-lg object-cover flex-shrink-0"
                            />
                          )}

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div className="min-w-0">
                                <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${tier.color} mb-1`}>
                                  {tier.label}
                                </span>
                                <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 truncate">
                                  {deal.title}
                                </h3>
                                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                                  ASIN: {deal.asin}
                                  {deal.category && ` · ${deal.category}`}
                                  {deal.bsr && ` · BSR #${deal.bsr.toLocaleString()}`}
                                </p>
                              </div>
                            </div>

                            {/* Price + profit */}
                            <div className="mt-3 flex flex-wrap items-center gap-4 text-sm">
                              <div>
                                <span className="text-zinc-500 dark:text-zinc-400">Buy: </span>
                                <span className="font-bold text-zinc-900 dark:text-zinc-50">
                                  ${deal.buy_price.toFixed(2)}
                                </span>
                                {deal.original_buy_price && (
                                  <span className="ml-1 text-xs text-zinc-400 line-through">
                                    ${deal.original_buy_price.toFixed(2)}
                                  </span>
                                )}
                              </div>
                              <div>
                                <span className="text-zinc-500 dark:text-zinc-400">Sell: </span>
                                <span className="font-bold text-zinc-900 dark:text-zinc-50">
                                  ${deal.sell_price.toFixed(2)}
                                </span>
                              </div>
                              {deal.net_profit && (
                                <div>
                                  <span className="text-zinc-500 dark:text-zinc-400">Profit: </span>
                                  <span className="font-bold text-emerald-600 dark:text-emerald-400">
                                    ${deal.net_profit.toFixed(2)}
                                  </span>
                                  {deal.roi && (
                                    <span className="ml-1 text-xs text-emerald-500">
                                      ({(deal.roi * 100).toFixed(0)}% ROI)
                                    </span>
                                  )}
                                </div>
                              )}
                              {deal.applied_coupon_code && (
                                <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400">
                                  🎫 {deal.applied_coupon_code}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Action */}
                          {deal.buy_url && (
                            <a
                              href={deal.buy_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex-shrink-0 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 self-center"
                            >
                              View →
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
