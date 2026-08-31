"use client";

import { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";
import { saleEvents, buyByCategory, sellByCategory, type SaleEvent, type EventTier } from "./data";

const tierConfig: Record<EventTier, { label: string; dot: string; badge: string; ring: string }> = {
  major: {
    label: "Major",
    dot: "bg-red-500",
    badge: "bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-400",
    ring: "hover:border-red-300 dark:hover:border-red-800",
  },
  moderate: {
    label: "Moderate",
    dot: "bg-amber-400",
    badge: "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400",
    ring: "hover:border-amber-300 dark:hover:border-amber-800",
  },
  minor: {
    label: "Minor",
    dot: "bg-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400",
    ring: "hover:border-emerald-300 dark:hover:border-emerald-800",
  },
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function CalendarClient() {
  const [selected, setSelected] = useState<SaleEvent | null>(null);

  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />

      <main className="flex-1">
        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <section className="px-6 py-16 text-center bg-gradient-to-b from-white to-zinc-50 dark:from-zinc-950 dark:to-zinc-900">
          <span className="inline-block rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 mb-6">
            Deal Calendar
          </span>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
            Deal Calendar 2026
          </h1>
          <p className="mt-4 text-base text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
            Never miss a sale. Track the biggest retail events and know exactly when to buy and flip.
          </p>

          {/* Legend */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs text-zinc-600 dark:text-zinc-400">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> Major sale event
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400" /> Moderate
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Minor / niche
            </span>
          </div>
        </section>

        {/* ── Monthly grid ─────────────────────────────────────────────── */}
        <section className="px-6 py-12 border-t border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {MONTHS.map((month, idx) => {
              const events = saleEvents.filter((e) => e.month === idx);
              return (
                <div
                  key={month}
                  className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900 flex flex-col"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                      {month}
                    </h2>
                    <span className="text-xs font-medium text-zinc-400 dark:text-zinc-600">
                      {events.length} event{events.length !== 1 ? "s" : ""}
                    </span>
                  </div>

                  {events.length === 0 ? (
                    <p className="text-xs text-zinc-400 dark:text-zinc-600 py-4">No major events</p>
                  ) : (
                    <ul className="space-y-2">
                      {events.map((ev) => {
                        const t = tierConfig[ev.tier];
                        return (
                          <li key={ev.id}>
                            <button
                              onClick={() => setSelected(ev)}
                              className={`w-full text-left rounded-lg border border-zinc-200 dark:border-zinc-800 px-3 py-2 transition-colors ${t.ring} hover:bg-zinc-50 dark:hover:bg-zinc-800/60`}
                            >
                              <div className="flex items-start gap-2">
                                <span className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${t.dot}`} />
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50 truncate">
                                    {ev.name}
                                  </p>
                                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                                    {ev.date}
                                  </p>
                                </div>
                              </div>
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Best times to buy ────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 px-6 py-16 dark:border-zinc-800 overflow-x-auto">
          <div className="mx-auto max-w-4xl">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 mb-2 text-center">
              Best Times to Buy by Category
            </h2>
            <p className="text-sm text-zinc-500 dark:text-zinc-400 text-center mb-8">
              Time your purchases to the deepest discounts of the year.
            </p>
            <table className="w-full text-left border-collapse min-w-[600px]">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800">
                  <th className="py-3 pr-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Category</th>
                  <th className="py-3 pr-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Best Month</th>
                  <th className="py-3 pr-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Expected Discount</th>
                  <th className="py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Why</th>
                </tr>
              </thead>
              <tbody>
                {buyByCategory.map((row, i) => (
                  <tr
                    key={row.category}
                    className={`border-b ${i % 2 === 0 ? "border-zinc-100 dark:border-zinc-800/60" : "border-zinc-200/60 dark:border-zinc-800"}`}
                  >
                    <td className="py-3 pr-6 text-sm font-medium text-zinc-900 dark:text-zinc-50">{row.category}</td>
                    <td className="py-3 pr-6 text-sm text-zinc-600 dark:text-zinc-400">{row.month}</td>
                    <td className="py-3 pr-6 text-sm font-semibold text-emerald-600 dark:text-emerald-400">{row.discount}</td>
                    <td className="py-3 text-sm text-zinc-600 dark:text-zinc-400">{row.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Best times to sell ───────────────────────────────────────── */}
        <section className="border-t border-zinc-200 px-6 py-16 dark:border-zinc-800 overflow-x-auto">
          <div className="mx-auto max-w-4xl">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 mb-2 text-center">
              Best Times to Sell by Category
            </h2>
            <p className="text-sm text-zinc-500 dark:text-zinc-400 text-center mb-8">
              Maximize resale profit by listing when demand peaks.
            </p>
            <table className="w-full text-left border-collapse min-w-[500px]">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800">
                  <th className="py-3 pr-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Category</th>
                  <th className="py-3 pr-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Best Month</th>
                  <th className="py-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Why</th>
                </tr>
              </thead>
              <tbody>
                {sellByCategory.map((row, i) => (
                  <tr
                    key={row.category}
                    className={`border-b ${i % 2 === 0 ? "border-zinc-100 dark:border-zinc-800/60" : "border-zinc-200/60 dark:border-zinc-800"}`}
                  >
                    <td className="py-3 pr-6 text-sm font-medium text-zinc-900 dark:text-zinc-50">{row.category}</td>
                    <td className="py-3 pr-6 text-sm text-zinc-600 dark:text-zinc-400">{row.month}</td>
                    <td className="py-3 text-sm text-zinc-600 dark:text-zinc-400">{row.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 dark:border-zinc-800 bg-zinc-900 dark:bg-zinc-50 px-6 py-16 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white dark:text-zinc-900">
            Get alerted the moment prices drop.
          </h2>
          <p className="mt-3 text-sm text-zinc-400 dark:text-zinc-600 max-w-lg mx-auto">
            BargainHuntrs watches every major sale event so you don&apos;t have to. Sign up for instant alerts.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/signup"
              className="rounded-xl bg-emerald-500 px-7 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-400 shadow-lg shadow-emerald-500/20"
            >
              Start for free
            </Link>
            <Link
              href="/deals/trending"
              className="rounded-xl border border-zinc-700 dark:border-zinc-300 px-7 py-3.5 text-sm font-semibold text-zinc-300 dark:text-zinc-700 transition-colors hover:border-zinc-500 hover:text-white dark:hover:text-zinc-900"
            >
              See trending deals
            </Link>
          </div>
        </section>
      </main>

      <Footer />

      {/* ── Event detail modal ─────────────────────────────────────────── */}
      {selected && (
        <EventModal event={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function EventModal({ event, onClose }: { event: SaleEvent; onClose: () => void }) {
  const t = tierConfig[event.tier];
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-start gap-3">
            <span className={`mt-1.5 h-3 w-3 flex-shrink-0 rounded-full ${t.dot}`} />
            <div>
              <h3 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
                {event.name}
              </h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-0.5">{event.date}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            aria-label="Close"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${t.badge}`}>
              <span className={`h-2 w-2 rounded-full ${t.dot}`} />
              {t.label} event
            </span>
            <span className="inline-flex items-center rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              {MONTHS[event.month]}
            </span>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1">What to buy</p>
            <p className="text-sm text-zinc-700 dark:text-zinc-300">{event.whatToBuy}</p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1">Expected discount</p>
            <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">{event.discount}</p>
          </div>

          <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-1">
              Best flip potential
            </p>
            <p className="text-sm text-emerald-900 dark:text-emerald-300">{event.flipNote}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
