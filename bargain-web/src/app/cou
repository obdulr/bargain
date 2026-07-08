"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  getCoupons,
  searchCoupons,
  getCouponRetailers,
  scrapeCoupons,
  type Coupon,
} from "@/lib/api";

export default function CouponsPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();

  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [retailers, setRetailers] = useState<string[]>([]);
  const [selectedRetailer, setSelectedRetailer] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [loadingCoupons, setLoadingCoupons] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState<string>("");
  const [error, setError] = useState("");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  const loadCoupons = useCallback(async () => {
    if (!idToken) return;
    setLoadingCoupons(true);
    setError("");
    try {
      const data = await getCoupons(idToken, {
        retailer: selectedRetailer || undefined,
        verified_only: verifiedOnly,
        limit: 100,
      });
      setCoupons(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load coupons");
    } finally {
      setLoadingCoupons(false);
    }
  }, [idToken, selectedRetailer, verifiedOnly]);

  const loadRetailers = useCallback(async () => {
    if (!idToken) return;
    try {
      const data = await getCouponRetailers(idToken);
      setRetailers(data);
    } catch {
      // Non-critical
    }
  }, [idToken]);

  useEffect(() => {
    if (idToken) {
      loadCoupons();
      loadRetailers();
    }
  }, [idToken, loadCoupons, loadRetailers]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!idToken || !searchQuery.trim()) return;
    setLoadingCoupons(true);
    try {
      const data = await searchCoupons(idToken, searchQuery, selectedRetailer || undefined);
      setCoupons(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoadingCoupons(false);
    }
  }

  async function handleScrape() {
    if (!idToken) return;
    setScraping(true);
    setScrapeResult("");
    setError("");
    try {
      const result = await scrapeCoupons(idToken, selectedRetailer ? [selectedRetailer] : undefined);
      setScrapeResult(`Scraped ${result.scraped} coupons, saved ${result.saved}, errors: ${result.errors}`);
      await loadCoupons();
      await loadRetailers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scrape failed");
    } finally {
      setScraping(false);
    }
  }

  function copyCode(code: string) {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  }

  function formatDiscount(coupon: Coupon): string {
    if (coupon.discount_type === "percentage") {
      return `${coupon.discount_value}% off`;
    } else if (coupon.discount_type === "fixed") {
      return `$${coupon.discount_value} off`;
    } else if (coupon.discount_type === "free_shipping") {
      return "Free shipping";
    }
    return "Discount";
  }

  function formatExpiry(expiresAt?: string): string {
    if (!expiresAt) return "No expiry";
    const expiry = new Date(expiresAt);
    const now = new Date();
    const diffHours = Math.round((expiry.getTime() - now.getTime()) / (1000 * 60 * 60));
    if (diffHours < 0) return "Expired";
    if (diffHours < 1) return "Expires soon";
    if (diffHours < 24) return `Expires in ${diffHours}h`;
    const diffDays = Math.round(diffHours / 24);
    return `Expires in ${diffDays}d`;
  }

  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />

      <main className="flex-1">
        {/* Header section */}
        <section className="px-6 py-10 border-b border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                  Coupon Codes
                </h1>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                  Scraped promo codes to stack on top of deals for extra savings.
                </p>
              </div>
              <button
                onClick={handleScrape}
                disabled={scraping}
                className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20"
              >
                {scraping ? "Scraping..." : "Scrape New Coupons"}
              </button>
            </div>

            {scrapeResult && (
              <p className="mt-3 text-sm text-emerald-600 dark:text-emerald-400">{scrapeResult}</p>
            )}
            {error && (
              <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>
            )}
          </div>
        </section>

        {/* Filters */}
        <section className="px-6 py-6 border-b border-zinc-100 dark:border-zinc-800/60">
          <div className="mx-auto max-w-6xl flex flex-wrap items-center gap-4">
            {/* Retailer filter */}
            <select
              value={selectedRetailer}
              onChange={(e) => setSelectedRetailer(e.target.value)}
              className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">All retailers</option>
              {retailers.map((r) => (
                <option key={r} value={r}>
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </option>
              ))}
            </select>

            {/* Verified toggle */}
            <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400 cursor-pointer">
              <input
                type="checkbox"
                checked={verifiedOnly}
                onChange={(e) => setVerifiedOnly(e.target.checked)}
                className="h-4 w-4 rounded border-zinc-300 text-emerald-500 focus:ring-emerald-500"
              />
              Verified only
            </label>

            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1 min-w-[200px] flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search coupons..."
                className="flex-1 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-700 placeholder:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <button
                type="submit"
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-50 dark:text-zinc-900"
              >
                Search
              </button>
            </form>

            {(searchQuery || selectedRetailer || verifiedOnly) && (
              <button
                onClick={() => {
                  setSearchQuery("");
                  setSelectedRetailer("");
                  setVerifiedOnly(false);
                }}
                className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
              >
                Clear filters
              </button>
            )}
          </div>
        </section>

        {/* Coupon grid */}
        <section className="px-6 py-8">
          <div className="mx-auto max-w-6xl">
            {loadingCoupons ? (
              <div className="flex justify-center py-20">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-200 border-t-emerald-500" />
              </div>
            ) : coupons.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  No coupons found. Click &quot;Scrape New Coupons&quot; to fetch the latest codes.
                </p>
              </div>
            ) : (
              <>
                <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
                  {coupons.length} coupon{coupons.length !== 1 ? "s" : ""}
                </p>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {coupons.map((coupon) => (
                    <div
                      key={coupon.id}
                      className="rounded-xl border border-zinc-200 bg-white p-5 transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
                    >
                      {/* Retailer badge + source */}
                      <div className="flex items-center justify-between mb-3">
                        <span className="inline-block rounded-md bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                          {coupon.retailer}
                        </span>
                        <span className="text-xs text-zinc-400 dark:text-zinc-600">
                          via {coupon.source}
                        </span>
                      </div>

                      {/* Title */}
                      <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 line-clamp-2 mb-1">
                        {coupon.title}
                      </h3>

                      {/* Discount */}
                      <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400 mb-2">
                        {formatDiscount(coupon)}
                      </p>

                      {/* Description */}
                      {coupon.description && (
                        <p className="text-xs text-zinc-500 dark:text-zinc-400 line-clamp-2 mb-3">
                          {coupon.description}
                        </p>
                      )}

                      {/* Code + copy */}
                      <div className="flex items-center gap-2 mb-3">
                        <code className="flex-1 rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-3 py-2 text-sm font-mono font-bold text-zinc-900 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100">
                          {coupon.code}
                        </code>
                        <button
                          onClick={() => copyCode(coupon.code)}
                          className="rounded-lg bg-zinc-900 px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900"
                        >
                          {copiedCode === coupon.code ? "Copied!" : "Copy"}
                        </button>
                      </div>

                      {/* Footer: expiry + verified */}
                      <div className="flex items-center justify-between text-xs">
                        <span className={`text-zinc-500 dark:text-zinc-400`}>
                          {formatExpiry(coupon.expires_at)}
                        </span>
                        {coupon.verified && (
                          <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                            </svg>
                            Verified
                          </span>
                        )}
                      </div>

                      {/* Product link */}
                      {coupon.product_url && (
                        <a
                          href={coupon.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 block text-xs font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400"
                        >
                          View deal →
                        </a>
                      )}
                    </div>
                  ))}
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
