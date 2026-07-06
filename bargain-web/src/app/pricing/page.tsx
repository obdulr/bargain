import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Pricing – BargainHuntrs",
  description:
    "Simple, transparent pricing for every level of arbitrage hustle. Start free, scale when ready.",
};

// ─── Data ──────────────────────────────────────────────────────────────────

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    tagline: "Test drive the platform.",
    description:
      "No credit card. No tricks. Just enough to see if BargainHuntrs is right for you before spending a cent.",
    cta: "Start free",
    href: "/signup",
    highlight: false,
    badge: null,
    features: [
      { label: "Watchlist items", value: "5" },
      { label: "Price check frequency", value: "Daily" },
      { label: "Price history", value: "30 days" },
      { label: "Email alerts", value: "✓" },
      { label: "SMS alerts", value: "—" },
      { label: "Arbitrage alerts", value: "—" },
      { label: "Glitch detection", value: "—" },
      { label: "Profit calculator", value: "—" },
      { label: "Multi-platform sell data", value: "—" },
      { label: "Risk score per deal", value: "—" },
      { label: "API access", value: "—" },
      { label: "Team seats", value: "1" },
      { label: "Support", value: "Community" },
    ],
  },
  {
    name: "Hustler",
    price: "$29",
    period: "/ month",
    tagline: "For the consistent side hustler.",
    description:
      "Hourly scans + glitch detection. This is the plan that pays for itself within the first flip.",
    cta: "Start Hustler",
    href: "/signup",
    highlight: true,
    badge: "Most popular",
    features: [
      { label: "Watchlist items", value: "100" },
      { label: "Price check frequency", value: "Hourly" },
      { label: "Price history", value: "Full" },
      { label: "Email alerts", value: "✓" },
      { label: "SMS alerts", value: "✓" },
      { label: "Arbitrage alerts", value: "✓" },
      { label: "Glitch detection", value: "✓" },
      { label: "Profit calculator", value: "—" },
      { label: "Multi-platform sell data", value: "—" },
      { label: "Risk score per deal", value: "—" },
      { label: "API access", value: "—" },
      { label: "Team seats", value: "1" },
      { label: "Support", value: "Email" },
    ],
  },
  {
    name: "Pro",
    price: "$79",
    period: "/ month",
    tagline: "For power sellers at scale.",
    description:
      "5-minute scans, true profit math, risk scores, and multi-platform sell data. This is the full arsenal.",
    cta: "Start Pro",
    href: "/signup",
    highlight: false,
    badge: null,
    features: [
      { label: "Watchlist items", value: "500" },
      { label: "Price check frequency", value: "Every 5 min" },
      { label: "Price history", value: "Full" },
      { label: "Email alerts", value: "✓" },
      { label: "SMS alerts", value: "✓" },
      { label: "Arbitrage alerts", value: "✓" },
      { label: "Glitch detection", value: "✓" },
      { label: "Profit calculator", value: "✓" },
      { label: "Multi-platform sell data", value: "✓" },
      { label: "Risk score per deal", value: "✓" },
      { label: "API access", value: "✓" },
      { label: "Team seats", value: "3" },
      { label: "Support", value: "Priority email" },
    ],
  },
  {
    name: "Agency",
    price: "$199",
    period: "/ month",
    tagline: "For teams running multiple stores.",
    description:
      "Unlimited items, 1-minute checks, 10 seats, and white-label reports. Run your operation like a business.",
    cta: "Start Agency",
    href: "/signup",
    highlight: false,
    badge: "Best value per seat",
    features: [
      { label: "Watchlist items", value: "Unlimited" },
      { label: "Price check frequency", value: "Every 1 min" },
      { label: "Price history", value: "Full" },
      { label: "Email alerts", value: "✓" },
      { label: "SMS alerts", value: "✓" },
      { label: "Arbitrage alerts", value: "✓" },
      { label: "Glitch detection", value: "✓" },
      { label: "Profit calculator", value: "✓" },
      { label: "Multi-platform sell data", value: "✓" },
      { label: "Risk score per deal", value: "✓" },
      { label: "API access", value: "✓" },
      { label: "Team seats", value: "10" },
      { label: "Support", value: "Dedicated" },
    ],
  },
];

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
    q: "Can I cancel or change my plan at any time?",
    a: "Yes, always. Upgrades take effect immediately and are prorated. Downgrades take effect at the end of your current billing period. No lock-in, no penalties.",
  },
  {
    q: "Is there a free trial for paid plans?",
    a: "The Free plan is yours forever and is a great way to evaluate the platform. Paid plans come with a 7-day money-back guarantee on your first month — if you're not happy, we'll refund you, no questions asked.",
  },
  {
    q: "What retailers do you track?",
    a: "Currently 500+ including Amazon, Walmart, Target, Best Buy, Home Depot, Costco, Newegg, Sam's Club, eBay, and more. We add new retailers every month — paid users can request additions.",
  },
  {
    q: "How is BargainHuntrs different from Tactical Arbitrage or BuyBotPro?",
    a: "Tactical Arbitrage only works for Amazon FBA and starts at $59/mo. BuyBotPro analyzes deals you already found — it doesn't find them for you. We do both, across any platform, starting free. We also detect price glitches (pricing errors) which no major competitor currently does.",
  },
  {
    q: "What's the difference between 'Arbitrage alerts' and 'Glitch detection'?",
    a: "Arbitrage alerts fire when a product's buy price on one platform is significantly below its sell price on another (e.g., Walmart $12 → eBay $40). Glitch detection catches retailer pricing errors — items priced far below their actual value, usually due to a system mistake that gets corrected within hours.",
  },
  {
    q: "How quickly will I get alerted to a deal?",
    a: "Free: daily digest. Hustler: within the hour. Pro: within 5 minutes. Agency: within 1 minute. For glitch detection specifically, all paid plans receive push/SMS immediately when a glitch is detected — glitches can disappear in under 10 minutes so speed is everything.",
  },
  {
    q: "Is the profit calculator accurate?",
    a: "We factor in marketplace fees (Amazon, eBay, etc.), estimated shipping, sales tax by state, and return rate risk. It's as accurate as we can make it without knowing your exact carrier rates — you can customize your shipping costs in Settings.",
  },
  {
    q: "Do you offer annual billing?",
    a: "Annual billing is coming soon with a 20% discount. Join the waitlist on the Contact page to be notified when it launches.",
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
        <section className="px-6 py-12">
          <div className="mx-auto max-w-6xl grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative flex flex-col rounded-2xl border p-6 ${
                  plan.highlight
                    ? "border-zinc-900 bg-zinc-900 dark:border-zinc-50 dark:bg-zinc-50"
                    : "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900"
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className={`rounded-full px-3 py-0.5 text-xs font-semibold text-white whitespace-nowrap ${plan.highlight ? "bg-emerald-500" : "bg-zinc-700"}`}>
                      {plan.badge}
                    </span>
                  </div>
                )}

                <h2
                  className={`text-lg font-bold ${
                    plan.highlight ? "text-white dark:text-zinc-900" : "text-zinc-900 dark:text-zinc-50"
                  }`}
                >
                  {plan.name}
                </h2>

                <p
                  className={`mt-0.5 text-xs font-medium ${
                    plan.highlight ? "text-emerald-400 dark:text-emerald-600" : "text-emerald-600 dark:text-emerald-400"
                  }`}
                >
                  {plan.tagline}
                </p>

                <div className="mt-3 flex items-baseline gap-0.5">
                  <span
                    className={`text-4xl font-bold tabular-nums ${
                      plan.highlight ? "text-white dark:text-zinc-900" : "text-zinc-900 dark:text-zinc-50"
                    }`}
                  >
                    {plan.price}
                  </span>
                  <span
                    className={`text-xs ${
                      plan.highlight ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-500"
                    }`}
                  >
                    {plan.period}
                  </span>
                </div>

                <p
                  className={`mt-3 text-xs leading-relaxed ${
                    plan.highlight ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-500 dark:text-zinc-400"
                  }`}
                >
                  {plan.description}
                </p>

                <Link
                  href={plan.href}
                  className={`mt-6 block rounded-xl px-4 py-2.5 text-center text-sm font-semibold transition-colors ${
                    plan.highlight
                      ? "bg-white text-zinc-900 hover:bg-zinc-100 dark:bg-zinc-900 dark:text-zinc-50 dark:hover:bg-zinc-800"
                      : "bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
                  }`}
                >
                  {plan.cta}
                </Link>

                <ul className="mt-6 space-y-2.5">
                  {plan.features.map((feat) => (
                    <li key={feat.label} className="flex items-center justify-between text-xs gap-2">
                      <span
                        className={
                          plan.highlight
                            ? "text-zinc-300 dark:text-zinc-600"
                            : "text-zinc-500 dark:text-zinc-400"
                        }
                      >
                        {feat.label}
                      </span>
                      <span
                        className={`font-medium tabular-nums ${
                          feat.value === "—"
                            ? "text-zinc-300 dark:text-zinc-700"
                            : feat.value === "✓"
                            ? "text-emerald-500"
                            : plan.highlight
                            ? "text-white dark:text-zinc-900"
                            : "text-zinc-900 dark:text-zinc-50"
                        }`}
                      >
                        {feat.value}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <p className="mt-6 text-center text-xs text-zinc-400 dark:text-zinc-600">
            All prices in USD. Monthly billing. 7-day money-back guarantee on first paid month.
          </p>
        </section>

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
        <section className="border-t border-zinc-200 px-6 py-24 dark:border-zinc-800">
          <div className="mx-auto max-w-3xl">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 text-center mb-12">
              Frequently asked questions
            </h2>
            <dl className="space-y-8">
              {faqs.map((faq) => (
                <div key={faq.q} className="border-b border-zinc-100 dark:border-zinc-800 pb-8 last:border-0">
                  <dt className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{faq.q}</dt>
                  <dd className="mt-2 text-sm text-zinc-600 leading-relaxed dark:text-zinc-400">
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
