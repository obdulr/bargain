"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useAuth } from "@/context/AuthContext";
import { authService } from "@/lib/authService";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.bargainhuntrs.com";

interface SubscriptionInfo {
  success: boolean;
  tier: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  status: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export default function BillingPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();
  const [sub, setSub] = useState<SubscriptionInfo | null>(null);
  const [error, setError] = useState("");
  const [canceling, setCanceling] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login?next=/billing");
      return;
    }
    if (idToken) {
      loadSubscription(idToken);
    }
  }, [user, loading, idToken, router]);

  async function loadSubscription(token: string) {
    try {
      const res = await fetch(`${API_URL}/api/v1/subscriptions/current`, {
        method: "GET",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || "Failed to load subscription");
      }
      setSub(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load subscription");
    }
  }

  async function handleCancel() {
    if (!idToken || !sub?.stripe_subscription_id) return;
    if (!confirm("Cancel your subscription at the end of the current billing period?")) return;
    setCanceling(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/v1/subscriptions/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({ subscription_id: sub.stripe_subscription_id }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || "Failed to cancel subscription");
      }
      await loadSubscription(idToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel subscription");
    } finally {
      setCanceling(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center bg-white dark:bg-zinc-950">
        <p className="text-zinc-600 dark:text-zinc-400">Loading…</p>
      </div>
    );
  }

  const tier = sub?.tier || "free";

  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />

      <main className="flex-1 mx-auto max-w-3xl w-full px-6 py-16">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          Billing
        </h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          Manage your subscription and payment method.
        </p>

        {error && (
          <div className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950/40 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Current plan */}
        <div className="mt-8 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Current plan</h2>
              <p className="mt-1 text-2xl font-semibold capitalize text-zinc-900 dark:text-zinc-50">
                {tier}
              </p>
              {sub?.status && (
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                  Status: <span className="capitalize">{sub.status}</span>
                  {sub.current_period_end &&
                    ` · Renews ${new Date(sub.current_period_end).toLocaleDateString()}`}
                </p>
              )}
              {sub?.cancel_at_period_end && (
                <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                  Your subscription will cancel at the end of the current billing period.
                </p>
              )}
            </div>
            <Link
              href="/pricing"
              className="rounded-xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Change plan
            </Link>
          </div>
        </div>

        {/* Manage subscription */}
        {sub?.stripe_subscription_id && (
          <div className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Cancel subscription</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Cancel your subscription at the end of the current billing period. You&apos;ll keep
              access until then.
            </p>
            <button
              type="button"
              onClick={handleCancel}
              disabled={canceling || sub.cancel_at_period_end}
              className="mt-4 rounded-xl border border-red-300 px-4 py-2 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950/40"
            >
              {sub.cancel_at_period_end
                ? "Cancellation scheduled"
                : canceling
                ? "Canceling…"
                : "Cancel subscription"}
            </button>
          </div>
        )}

        {/* Account */}
        <div className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Account</h2>
          <p className="mt-2 text-sm text-zinc-900 dark:text-zinc-50">{user?.email}</p>
          <button
            type="button"
            onClick={() => {
              authService.logout();
              router.push("/");
            }}
            className="mt-4 rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Log out
          </button>
        </div>
      </main>

      <Footer />
    </div>
  );
}
