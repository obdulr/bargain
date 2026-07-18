"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { authService } from "@/lib/authService";
import {
  getCurrentUser,
  getWatchlist,
  addWatchlistItem,
  refreshWatchlistItem,
  deleteWatchlistItem,
  getMyNiches,
  updateMyNiches,
  updateMyPhone,
  getReferralStats,
  type Niche,
} from "@/lib/api";

interface UserData {
  id: string;
  email: string;
  subscription_tier: string;
  phoneNumber?: string | null;
}

interface WatchlistItem {
  id: string;
  item_name: string;
  target_price: number | null;
  current_price: number | null;
  retailers: { url: string; price?: number | null }[];
  created_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", url: "", target: "" });
  const [adding, setAdding] = useState(false);
  const [availableNiches, setAvailableNiches] = useState<Niche[]>([]);
  const [subscribedNiches, setSubscribedNiches] = useState<string[]>([]);
  const [savingNiches, setSavingNiches] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [savingPhone, setSavingPhone] = useState(false);
  const [phoneSaved, setPhoneSaved] = useState(false);
  const [referralCount, setReferralCount] = useState<number | null>(null);
  const [referralAura, setReferralAura] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
      return;
    }

    if (idToken) {
      getCurrentUser(idToken).then((data) => {
        setUserData(data);
        setPhoneNumber(data.phoneNumber || "");
      }).catch((err) => setError(err.message));
      loadItems();
      loadNiches();
      getReferralStats(idToken)
        .then((stats) => {
          setReferralCount(stats.referral_count);
          setReferralAura(stats.total_aura_earned);
        })
        .catch(() => {
          // Non-critical
        });
    }
  }, [user, loading, idToken, router]);

  async function loadItems() {
    if (!idToken) return;
    try {
      const data = await getWatchlist(idToken);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load watchlist");
    }
  }

  async function loadNiches() {
    if (!idToken) return;
    try {
      const data = await getMyNiches(idToken);
      setAvailableNiches(data.available_niches);
      setSubscribedNiches(data.subscribed_niches);
    } catch {
      // Non-critical
    }
  }

  function toggleNiche(key: string) {
    setSubscribedNiches((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  }

  async function saveNiches() {
    if (!idToken) return;
    setSavingNiches(true);
    try {
      await updateMyNiches(idToken, subscribedNiches);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save niche preferences");
    } finally {
      setSavingNiches(false);
    }
  }

  async function savePhone() {
    if (!idToken) return;
    setSavingPhone(true);
    setPhoneSaved(false);
    try {
      await updateMyPhone(idToken, phoneNumber);
      setPhoneSaved(true);
      setTimeout(() => setPhoneSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save phone number");
    } finally {
      setSavingPhone(false);
    }
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!idToken) return;
    setError("");
    setAdding(true);
    try {
      await addWatchlistItem(
        idToken,
        form.name,
        form.url,
        form.target ? parseFloat(form.target) : undefined
      );
      setForm({ name: "", url: "", target: "" });
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setAdding(false);
    }
  }

  async function handleRefresh(itemId: string) {
    if (!idToken) return;
    try {
      await refreshWatchlistItem(idToken, itemId);
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh");
    }
  }

  async function handleDelete(itemId: string) {
    if (!idToken) return;
    try {
      await deleteWatchlistItem(idToken, itemId);
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  async function handleLogout() {
    authService.logout();
    router.push("/");
  }

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <p className="text-zinc-600 dark:text-zinc-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-zinc-50 dark:bg-zinc-950">
      <header className="border-b border-zinc-200 bg-white px-6 py-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              {userData?.email || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-50 dark:hover:bg-zinc-800"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12">
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}

        <div className="grid gap-6 sm:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Plan</h2>
            <p className="mt-2 text-2xl font-semibold capitalize text-zinc-900 dark:text-zinc-50">
              {userData?.subscription_tier || "Free"}
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Watchlist</h2>
            <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{items.length} items</p>
          </div>
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Alerts</h2>
            <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">0 new</p>
          </div>
          <Link
            href="/referrals"
            className="rounded-2xl border border-indigo-200 bg-indigo-50 p-6 transition-colors hover:bg-indigo-100 dark:border-indigo-900 dark:bg-indigo-950 dark:hover:bg-indigo-900/40"
          >
            <h2 className="text-sm font-medium text-indigo-700 dark:text-indigo-400">Referrals</h2>
            <p className="mt-2 text-2xl font-semibold text-indigo-900 dark:text-indigo-300">
              {referralCount !== null ? referralCount : "—"} invites
            </p>
            <p className="mt-1 text-xs text-indigo-700 dark:text-indigo-400">
              {referralAura !== null ? `${referralAura} Aura earned` : "Invite friends →"}
            </p>
          </Link>
          <Link
            href="/coupons"
            className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 transition-colors hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950 dark:hover:bg-emerald-900/40"
          >
            <h2 className="text-sm font-medium text-emerald-700 dark:text-emerald-400">Coupon Codes</h2>
            <p className="mt-2 text-2xl font-semibold text-emerald-900 dark:text-emerald-300">
              Browse →
            </p>
          </Link>
          <Link
            href="/deals"
            className="rounded-2xl border border-amber-200 bg-amber-50 p-6 transition-colors hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950 dark:hover:bg-amber-900/40"
          >
            <h2 className="text-sm font-medium text-amber-700 dark:text-amber-400">Deal Feed</h2>
            <p className="mt-2 text-2xl font-semibold text-amber-900 dark:text-amber-300">
              Live →
            </p>
          </Link>
        </div>

        <div className="mt-8 rounded-2xl border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Your Niches</h2>
            <button
              onClick={saveNiches}
              disabled={savingNiches}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {savingNiches ? "Saving..." : "Save preferences"}
            </button>
          </div>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            Pick the categories you want deal alerts for. Leave all unchecked to receive every niche.
          </p>
          {availableNiches.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">Loading niches...</p>
          ) : (
            <div className="mt-5 flex flex-wrap gap-2">
              {availableNiches.map((n) => {
                const selected = subscribedNiches.includes(n.key);
                return (
                  <button
                    key={n.key}
                    onClick={() => toggleNiche(n.key)}
                    title={n.description}
                    className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                      selected
                        ? "bg-emerald-600 text-white"
                        : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
                    }`}
                  >
                    <span className="mr-1">{n.emoji}</span>
                    {n.name}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Phone number for SMS alerts (Hunter tier) */}
        <div className="mt-8 rounded-2xl border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">SMS Alerts</h2>
            {(userData?.subscription_tier || "free").toLowerCase() !== "hunter" && (
              <Link href="/pricing" className="text-sm font-medium text-blue-600 hover:text-blue-700">
                Upgrade to Hunter →
              </Link>
            )}
          </div>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
            {(userData?.subscription_tier || "free").toLowerCase() === "hunter"
              ? "Enter your phone number to receive instant SMS deal alerts."
              : "SMS alerts are a Hunter plan feature. Upgrade to get instant deal notifications via text."}
          </p>
          <div className="mt-5 flex gap-3">
            <input
              type="tel"
              placeholder="+1234567890"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              disabled={(userData?.subscription_tier || "free").toLowerCase() !== "hunter"}
              className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <button
              onClick={savePhone}
              disabled={savingPhone || (userData?.subscription_tier || "free").toLowerCase() !== "hunter"}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {savingPhone ? "Saving..." : phoneSaved ? "Saved!" : "Save number"}
            </button>
          </div>
        </div>

        {/* Notification settings link */}
        <Link
          href="/settings/notifications"
          className="mt-8 block rounded-2xl border border-blue-200 bg-blue-50 p-6 transition-colors hover:bg-blue-100 dark:border-blue-900 dark:bg-blue-950 dark:hover:bg-blue-900/40"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-blue-700 dark:text-blue-400">Notification Settings</h2>
              <p className="mt-1 text-sm text-blue-900 dark:text-blue-300">
                Manage alert channels, niches, and delivery preferences.
              </p>
            </div>
            <span className="text-2xl font-semibold text-blue-900 dark:text-blue-300">→</span>
          </div>
        </Link>

        <div className="mt-12 rounded-2xl border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Add a product</h2>
          <form onSubmit={handleAdd} className="mt-6 grid gap-4 sm:grid-cols-4">
            <input
              type="text"
              placeholder="Product name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 sm:col-span-2"
            />
            <input
              type="url"
              placeholder="Retailer URL"
              required
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Target price"
              value={form.target}
              onChange={(e) => setForm({ ...form, target: e.target.value })}
              className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
            />
            <button
              type="submit"
              disabled={adding}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200 sm:col-span-4"
            >
              {adding ? "Adding..." : "Add to watchlist"}
            </button>
          </form>
        </div>

        <div className="mt-8 rounded-2xl border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Your watchlist</h2>
          {items.length === 0 ? (
            <p className="mt-4 text-sm text-zinc-600 dark:text-zinc-400">No items yet. Add your first product above.</p>
          ) : (
            <ul className="mt-6 divide-y divide-zinc-200 dark:divide-zinc-800">
              {items.map((item) => (
                <li key={item.id} className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-zinc-900 dark:text-zinc-50">{item.item_name}</p>
                      <p className="text-sm text-zinc-600 dark:text-zinc-400">
                        Current: ${item.current_price ?? "—"}
                        {item.target_price ? ` · Target: $${item.target_price}` : ""}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleRefresh(item.id)}
                        className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-50 dark:hover:bg-zinc-800"
                      >
                        Refresh
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 transition-colors hover:bg-red-50 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
