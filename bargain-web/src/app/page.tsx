"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { getPublicDeals, clickAffiliatePublic, type ArbitrageDeal } from "@/lib/api";

// ─── Deal card helpers ─────────────────────────────────────────────────────

function formatTier(tier: string): { label: string; color: string } {
  switch (tier) {
    case "glitch":
      return { label: "⚡ GLITCH", color: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400" };
    case "clearance":
      return { label: "CLEARANCE", color: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-400" };
    case "arbitrage":
      return { label: "DEAL", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400" };
    case "watch":
      return { label: "WATCH", color: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400" };
    default:
      return { label: "DEAL", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400" };
  }
}

function timeAgo(detectedAt: string): string {
  const diff = Date.now() - new Date(detectedAt).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function discountPercent(deal: ArbitrageDeal): number | null {
  if (deal.original_buy_price && deal.original_buy_price > deal.buy_price) {
    return Math.round((1 - deal.buy_price / deal.original_buy_price) * 100);
  }
  if (deal.historical_avg && deal.historical_avg > deal.buy_price) {
    return Math.round((1 - deal.buy_price / deal.historical_avg) * 100);
  }
  return null;
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function HomePage() {
  const [deals, setDeals] = useState<ArbitrageDeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [clickingDeal, setClickingDeal] = useState<string | null>(null);

  const loadDeals = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getPublicDeals(20, 0);
      setDeals(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load deals");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  const handleDealClick = useCallback(
    async (deal: ArbitrageDeal, e: React.MouseEvent) => {
      e.preventDefault();
      if (!deal.buy_url) return;
      setClickingDeal(deal.id);
      try {
        const result = await clickAffiliatePublic({
          url: deal.buy_url,
          retailer: "amazon",
          asin: deal.asin,
          deal_id: deal.id,
        });
        window.open(result.affiliate_url || deal.buy_url, "_blank", "noopener,noreferrer");
      } catch {
        window.open(deal.buy_url, "_blank", "noopener,noreferrer");
      } finally {
        setClickingDeal(null);
      }
    },
    []
  );

  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      {/* Impact site verification (content method) */}
      <div style={{ position: "absolute", left: "-9999px", top: "0", fontSize: "1px", color: "#fff" }} aria-hidden="true">
        Impact-Site-Verification: c2aacb17-49a0-4116-b515-be1a7e596103
      </div>
      <Header />

      <main className="flex-1 flex flex-col">
        {/* ── Compact hero ─────────────────────────────────────────────── */}
        <section className="px-6 py-12 text-center bg-gradient-to-b from-white via-zinc-50/60 to-zinc-100/40 dark:from-zinc-950 dark:via-zinc-900/80 dark:to-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white/80 backdrop-blur px-4 py-1.5 text-xs font-medium text-zinc-600 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80 dark:text-zinc-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            {deals.length > 0 ? `${deals.length} live deals right now` : "Scanning for deals..."}
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50 leading-[1.1]">
            The bargain edge<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 via-emerald-400 to-teal-400">
              before anyone else.
            </span>
          </h1>
          <p className="mt-4 text-base text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto">
            Real deals from real retailers. No fluff, no fake discounts.{" "}
            <Link href="/signup" className="font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400">
              Sign up for instant alerts →
            </Link>
          </p>
        </section>

        {/* ── Deals feed ───────────────────────────────────────────────── */}
        <section className="px-6 py-8 flex-1">
          <div className="mx-auto max-w-5xl">
            {error && (
              <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950 dark:text-red-400">
                {error}
              </div>
            )}

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-200 border-t-emerald-500" />
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Finding the best deals...</p>
              </div>
            ) : deals.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">No deals found right now</p>
                <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                  Our scanners are watching for price drops and glitches. Check back soon or{" "}
                  <Link href="/signup" className="text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 font-medium">
                    sign up for alerts
                  </Link>{" "}
                  so you never miss one.
                </p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    {deals.length} deal{deals.length !== 1 ? "s" : ""} found
                  </p>
                  <Link
                    href="/deals"
                    className="text-sm font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                  >
                    View all deals →
                  </Link>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {deals.map((deal) => {
                    const tier = formatTier(deal.deal_tier);
                    const discount = discountPercent(deal);
                    const savings = deal.original_buy_price
                      ? deal.original_buy_price - deal.buy_price
                      : deal.historical_avg
                      ? deal.historical_avg - deal.buy_price
                      : null;

                    return (
                      <div
                        key={deal.id}
                        className="group flex flex-col rounded-2xl border border-zinc-200 bg-white transition-all hover:border-zinc-300 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700 overflow-hidden"
                      >
                        {/* Image */}
                        {deal.image_url && (
                          <div className="relative aspect-square bg-zinc-50 dark:bg-zinc-800 overflow-hidden">
                            <img
                              src={deal.image_url}
                              alt={deal.title}
                              className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                            {discount && (
                              <div className="absolute top-3 left-3 rounded-lg bg-emerald-500 px-2.5 py-1 text-xs font-bold text-white shadow-md">
                                {discount}% OFF
                              </div>
                            )}
                          </div>
                        )}

                        {/* Content */}
                        <div className="flex flex-col flex-1 p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${tier.color}`}>
                              {tier.label}
                            </span>
                            <span className="text-xs text-zinc-400 dark:text-zinc-500">
                              {timeAgo(deal.detected_at)}
                            </span>
                          </div>

                          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 line-clamp-2 mb-2">
                            {deal.title}
                          </h3>

                          {/* Price */}
                          <div className="flex items-baseline gap-2 mb-3">
                            <span className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
                              ${deal.buy_price.toFixed(2)}
                            </span>
                            {deal.original_buy_price && deal.original_buy_price > deal.buy_price && (
                              <span className="text-sm text-zinc-400 line-through">
                                ${deal.original_buy_price.toFixed(2)}
                              </span>
                            )}
                          </div>

                          {/* Savings + profit */}
                          <div className="flex flex-wrap gap-3 text-xs mb-4">
                            {savings && (
                              <span className="font-medium text-emerald-600 dark:text-emerald-400">
                                Save ${savings.toFixed(2)}
                              </span>
                            )}
                            {deal.net_profit && (
                              <span className="font-medium text-zinc-500 dark:text-zinc-400">
                                Profit: ${deal.net_profit.toFixed(2)}
                              </span>
                            )}
                            {deal.applied_coupon_code && (
                              <span className="rounded-md bg-emerald-50 px-2 py-0.5 font-medium text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400">
                                🎫 {deal.applied_coupon_code}
                              </span>
                            )}
                          </div>

                          {/* CTA */}
                          <div className="mt-auto">
                            {deal.buy_url ? (
                              <button
                                onClick={(e) => handleDealClick(deal, e)}
                                disabled={clickingDeal === deal.id}
                                className="w-full rounded-xl bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-emerald-500 dark:hover:bg-emerald-400"
                              >
                                {clickingDeal === deal.id ? "Opening..." : "Get Deal →"}
                              </button>
                            ) : (
                              <Link
                                href="/signup"
                                className="block w-full rounded-xl bg-zinc-100 px-4 py-2.5 text-center text-sm font-semibold text-zinc-600 transition-colors hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
                              >
                                Sign up to view
                              </Link>
                            )}
                            <p className="mt-1.5 text-center text-xs text-zinc-400 dark:text-zinc-600">
                              Affiliate link — no extra cost to you
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </section>

        {/* ── Signup CTA ───────────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-6 py-16">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Get alerted the moment a deal drops.
            </h2>
            <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400 max-w-lg mx-auto">
              Free forever. Browse every deal, get daily alerts, and save money from day one.
              Upgrade to Hunter for instant alerts for just $9.99/mo.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-4">
              <Link
                href="/signup"
                className="rounded-xl bg-emerald-500 px-7 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-400 shadow-lg shadow-emerald-500/20"
              >
                Start for free
              </Link>
              <Link
                href="/pricing"
                className="rounded-xl border border-zinc-300 px-7 py-3.5 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-50 dark:hover:bg-zinc-800"
              >
                See pricing
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
