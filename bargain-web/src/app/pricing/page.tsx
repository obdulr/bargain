import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { PricingPlans } from "./PricingPlans";
import { plans } from "./plans";

export const metadata: Metadata = {
  title: "Pricing – BargainHuntrs",
  description:
    "Simple, transparent pricing for every level of arbitrage hustle. Start free, scale when ready.",
};

// ─── Data ──────────────────────────────────────────────────────────────────

const comparisonRows = [
  { feature: "Glitch & price-error detection", free: false, hustler: true, pro: true, agency: true },
  { feature: "Cross-platform arbitrage alerts", free: false, hustler: true, pro: true, agency: true },
  { feature: "True profit calculator (fees + tax + shipping)", free: false, hustler: false, pro: true, agency: true },
  { feature: "Risk score per deal", free: false, hustler: false, pro: true, agency: true },
  { feature: "Multi-platform sell price data (eBay, StockX…)", free: false, hustler: false, pro: true, agency: true },
  { feature: "Price check frequency", free: "Daily", hustler: "Hourly", pro: "5 min", agency: "1 min" },
  { feature: "Watchlist items", free: "5", hustler: "100", pro: "500", agency: "Unlimited" },
  { feature: "Price history depth", free: "30 days", hustler: "Full", pro: "Full", agency: "Full" },
  { feature: "Email alerts", free: true, hustler: true, pro: true, agency: true },
  { feature: "SMS alerts", free: false, hustler: true, pro: true, agency: true },
  { feature: "API access", free: false, hustler: false, pro: true, agency: true },
  { feature: "Team seats", free: "1", hustler: "1", pro: "3", agency: "10" },
  { feature: "White-label reports", free: false, hustler: false, pro: false, agency: true },
  { feature: "Custom integrations", free: false, hustler: false, pro: false, agency: true },
  { feature: "Dedicated support", free: false, hustler: false, pro: false, agency: true },
];

const faqs = [
  {
    q: "Can I cancel or change my plan?",
    a: "Anytime. Upgrades are immediate and prorated; downgrades apply at period end. No lock-in.",
  },
  {
    q: "Is there a free trial?",
    a: "The Free plan is forever. Paid plans have a 7-day money-back guarantee on your first month.",
  },
  {
    q: "What retailers do you track?",
    a: "500+ including Amazon, Walmart, Target, Best Buy, Home Depot, Costco, Newegg, eBay, and more. New retailers added monthly.",
  },
  {
    q: "How are you different from Tactical Arbitrage?",
    a: "TA only does Amazon FBA at $59/mo. We work across any platform, start free, and detect price glitches no competitor offers.",
  },
  {
    q: "Arbitrage alerts vs. glitch detection?",
    a: "Arbitrage = buy low on one platform, sell high on another. Glitch = retailer pricing errors corrected within hours.",
  },
  {
    q: "How fast are alerts?",
    a: "Free: daily. Hustler: hourly. Pro: 5 min. Agency: 1 min. Glitch alerts push immediately on all paid plans.",
  },
  {
    q: "Is the profit calculator accurate?",
    a: "Factors in marketplace fees, shipping, sales tax, and return risk. Customize your carrier costs in Settings.",
  },
  {
    q: "Annual billing?",
    a: "Coming soon with 20% off. Join the waitlist to be notified.",
  },
];

// ─── Cell helper ───────────────────────────────────────────────────────────

function Cell({ value, highlighted }: { value: boolean | string; highlighted?: boolean }) {
  if (typeof value === "boolean") {
    return value ? (
      <span className={`text-emerald-500 font-semibold text-sm`}>✓</span>
    ) : (
      <span className="text-zinc-300 dark:text-zinc-700 text-sm">—</span>
    );
  }
  return (
    <span
      className={`text-xs font-medium tabular-nums ${
        highlighted ? "text-white dark:text-zinc-900" : "text-zinc-700 dark:text-zinc-300"
      }`}
    >
      {value}
    </span>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function PricingPage() {
  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />

      <main className="flex-1">

        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <section className="px-6 py-20 text-center bg-gradient-to-b from-white to-zinc-50 dark:from-zinc-950 dark:to-zinc-900">
          <span className="inline-block rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 mb-6">
            Pricing
          </span>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl">
            Priced for hustlers,<br />not hedge funds.
          </h1>
          <p className="mt-4 text-base text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
            Tactical Arbitrage starts at $59. SourceMogul is £79.99. OAGenius is $175.{" "}
            <strong className="text-zinc-900 dark:text-zinc-50">We start at free.</strong>{" "}
            No annual commitment, no seat taxes, no gotchas.
          </p>
        </section>

        {/* ── Plan cards ───────────────────────────────────────────────── */}
        <PricingPlans />

        {/* ── Detailed comparison table ─────────────────────────────────── */}
        <section className="border-t border-zinc-200 px-6 py-20 dark:border-zinc-800 overflow-x-auto">
          <div className="mx-auto max-w-6xl">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 mb-10 text-center">
              Full feature comparison
            </h2>
            <table className="w-full text-left border-collapse min-w-[600px]">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800">
                  <th className="py-3 pr-6 text-xs font-semibold text-zinc-500 uppercase tracking-wider w-1/3">
                    Feature
                  </th>
                  {plans.map((plan) => (
                    <th
                      key={plan.name}
                      className={`py-3 px-3 text-center text-xs font-bold uppercase tracking-wider ${
                        plan.highlight
                          ? "text-zinc-900 dark:text-zinc-50"
                          : "text-zinc-500"
                      }`}
                    >
                      {plan.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisonRows.map((row, i) => (
                  <tr
                    key={row.feature}
                    className={`border-b ${
                      i % 2 === 0
                        ? "border-zinc-100 dark:border-zinc-800/60"
                        : "border-zinc-200/60 dark:border-zinc-800"
                    }`}
                  >
                    <td className="py-3 pr-6 text-xs text-zinc-600 dark:text-zinc-400">
                      {row.feature}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <Cell value={row.free} />
                    </td>
                    <td className="py-3 px-3 text-center bg-zinc-900/[0.03] dark:bg-zinc-50/[0.02]">
                      <Cell value={row.hustler} highlighted />
                    </td>
                    <td className="py-3 px-3 text-center">
                      <Cell value={row.pro} />
                    </td>
                    <td className="py-3 px-3 text-center">
                      <Cell value={row.agency} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Risk reversal banner ─────────────────────────────────────── */}
        <section className="border-t border-zinc-200 dark:border-zinc-800 bg-emerald-50 dark:bg-emerald-950/20 px-6 py-12">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
              7-day money-back guarantee.
            </p>
            <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto">
              Try any paid plan for your first month. If you haven&apos;t found a single deal worth your
              subscription cost, we&apos;ll refund you in full. No questions, no forms, no fight.
              <br />
              We back the product because it works.
            </p>
          </div>
        </section>

        {/* ── FAQ ──────────────────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 px-6 py-16 dark:border-zinc-800">
          <div className="mx-auto max-w-5xl">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 text-center mb-8">
              Frequently asked questions
            </h2>
            <dl className="grid grid-cols-1 gap-x-10 gap-y-6 sm:grid-cols-2">
              {faqs.map((faq) => (
                <div key={faq.q}>
                  <dt className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{faq.q}</dt>
                  <dd className="mt-1 text-sm text-zinc-600 leading-snug dark:text-zinc-400">
                    {faq.a}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 dark:border-zinc-800 bg-zinc-900 dark:bg-zinc-50 px-6 py-20 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-white dark:text-zinc-900">
            Not sure which plan is right?
          </h2>
          <p className="mt-3 text-sm text-zinc-400 dark:text-zinc-600 max-w-lg mx-auto">
            Start with Free and upgrade the moment you find your first deal. Most hustlers upgrade
            within their first week. Or{" "}
            <Link
              href="/contact"
              className="font-medium underline underline-offset-4 text-zinc-300 dark:text-zinc-700 hover:text-white dark:hover:text-zinc-900 transition-colors"
            >
              get in touch
            </Link>{" "}
            — we&apos;ll help you pick.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/signup"
              className="rounded-xl bg-emerald-500 px-7 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-400 shadow-lg shadow-emerald-500/20"
            >
              Start for free
            </Link>
            <Link
              href="/contact"
              className="rounded-xl border border-zinc-700 dark:border-zinc-300 px-7 py-3.5 text-sm font-semibold text-zinc-300 dark:text-zinc-700 transition-colors hover:border-zinc-500 hover:text-white dark:hover:text-zinc-900"
            >
              Talk to us first
            </Link>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
