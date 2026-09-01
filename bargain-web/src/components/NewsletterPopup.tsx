"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "bh_newsletter_dismissed";
const SHOW_DELAY_MS = 8000; // Show after 8 seconds
const SHOW_KEY = "bh_newsletter_shown";

export default function NewsletterPopup() {
  const [visible, setVisible] = useState(false);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    // Don't show if previously dismissed
    const dismissed = localStorage.getItem(STORAGE_KEY);
    if (dismissed) return;

    // Don't show if already shown this session
    const shown = sessionStorage.getItem(SHOW_KEY);
    if (shown) return;

    const timer = setTimeout(() => {
      setVisible(true);
      sessionStorage.setItem(SHOW_KEY, "1");
    }, SHOW_DELAY_MS);

    return () => clearTimeout(timer);
  }, []);

  function dismiss() {
    setVisible(false);
    localStorage.setItem(STORAGE_KEY, "1");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !email.includes("@")) {
      setStatus("error");
      setErrorMsg("Please enter a valid email address");
      return;
    }

    setStatus("loading");
    setErrorMsg("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://api.bargainhuntrs.com";
      const resp = await fetch(`${apiUrl}/api/v1/newsletter/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (resp.ok) {
        setStatus("success");
        localStorage.setItem(STORAGE_KEY, "1");
        // Auto-close after 3 seconds
        setTimeout(() => setVisible(false), 3000);
      } else {
        const data = await resp.json().catch(() => ({}));
        if (data.detail && String(data.detail).toLowerCase().includes("already")) {
          setStatus("success"); // Already subscribed = success
          localStorage.setItem(STORAGE_KEY, "1");
          setTimeout(() => setVisible(false), 3000);
        } else {
          setStatus("error");
          setErrorMsg(data.detail || "Something went wrong. Please try again.");
        }
      }
    } catch {
      setStatus("error");
      setErrorMsg("Network error. Please try again.");
    }
  }

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={dismiss}>
      <div
        className="relative w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl dark:bg-zinc-900"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={dismiss}
          className="absolute right-4 top-4 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
          aria-label="Close"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {status === "success" ? (
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900">
              <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">You&apos;re in!</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
              Check your inbox for the best deals delivered daily.
            </p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                Get the Best Deals Daily
              </h2>
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                Join thousands of deal hunters. Price glitches, clearance finds, and 75%+ discounts
                delivered to your inbox. Free forever.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 px-4 py-3 text-zinc-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
                required
              />
              {status === "error" && (
                <p className="text-sm text-red-600 dark:text-red-400">{errorMsg}</p>
              )}
              <button
                type="submit"
                disabled={status === "loading"}
                className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {status === "loading" ? "Subscribing..." : "Get Free Deal Alerts"}
              </button>
            </form>

            <p className="mt-4 text-center text-xs text-zinc-400">
              No spam. Unsubscribe anytime. We respect your privacy.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
