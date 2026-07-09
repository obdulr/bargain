import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

// ─── Data ──────────────────────────────────────────────────────────────────

const features = [
  {
    icon: "⚡",
    tag: "Glitch Detection",
    title: "Catch price errors before they're fixed",
    description:
      "Our engine scans for anomalies — retailer pricing mistakes, flash glitches, and clearance mis-tags — and fires an alert within seconds. Tactical Arbitrage doesn't have this. BrickSeek doesn't have this. We do.",
    accent: "text-amber-500",
  },
  {
    icon: "🔄",
    tag: "Cross-Platform Arbitrage",
    title: "Buy anywhere. Sell anywhere.",
    description:
      "Amazon ↔ eBay. Walmart ↔ StockX. Target clearance → Facebook Marketplace. We surface profitable gaps between ANY two platforms — not just Amazon FBA. This is the gap every other tool ignores.",
    accent: "text-blue-500",
  },
  {
    icon: "📡",
    tag: "Real-Time Scanning",
    title: "500+ retailers. One dashboard.",
    description:
      "Continuous scans across Amazon, Walmart, Target, Best Buy, Home Depot, Costco, and 500+ more. Price history charts, trend lines, and a live feed of what just dropped.",
    accent: "text-emerald-500",
  },
  {
    icon: "📊",
    tag: "True Profit Math",
    title: "See your real margin before you buy",
    description:
      "We auto-calculate marketplace fees, shipping, sales tax, return risk, and storage costs. You see net profit — not gross spread. No more spreadsheets, no more surprises at payout.",
    accent: "text-violet-500",
  },
  {
    icon: "🔔",
    tag: "Smart Alerts",
    title: "Get notified before the deal is gone",
    description:
      "Email, SMS, or push. Set a target price, a minimum margin, or a glitch threshold — we watch 24/7 and ping you the moment conditions are met. Free users get daily digests. Paid users get instant.",
    accent: "text-rose-500",
  },
  {
    icon: "🏁",
    tag: "Flip Workflow",
    title: "Find it → buy it → list it → track ROI",
    description:
      "Every other tool stops at \"found it\". BargainHuntrs gives you the full loop: deal discovery, profit calc, one-click buy link, resale listing templates, and a dashboard that tracks your actual ROI over time.",
    accent: "text-orange-500",
  },
];

const competitors = [
  {
    name: "Tactical Arbitrage",
    price: "$59–$129/mo",
    weaknesses: ["Amazon FBA only", "No glitch detection", "Steep learning curve", "No profit workflow"],
    verdict: "Powerful scanner, but you need hours to learn it and it only works for Amazon.",
  },
  {
    name: "BuyBotPro",
    price: "$12–$83/mo",
    weaknesses: ["Analyzes deals, doesn't find them", "Chrome extension only", "Amazon-centric", "No cross-platform"],
    verdict: "Great analyzer once you already have a lead. Useless for finding opportunities.",
  },
  {
    name: "BrickSeek",
    price: "$9.99–$99.99/mo",
    weaknesses: ["Consumer app, not reseller tool", "US retail only", "No profit math", "No online arbitrage"],
    verdict: "Solid for finding clearance, but it won't tell you if it's actually worth buying.",
  },
  {
    name: "Keepa / CamelCamelCamel",
    price: "Free / $0",
    weaknesses: ["Price history only", "No alerts for arbitrage gaps", "No cross-platform", "Dated UI"],
    verdict: "The charts are great. The arbitrage intelligence is nonexistent.",
  },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Dip your toes in. No card required.",
    cta: "Start free",
    href: "/signup",
    highlight: false,
    features: ["5 watchlist items", "Daily price checks", "Email alerts", "30-day price history"],
  },
  {
    name: "Hustler",
    price: "$29",
    period: "/mo",
    description: "For side-hustlers ready to flip consistently.",
    cta: "Go Hustler",
    href: "/signup",
    highlight: true,
    badge: "Most popular",
    features: [
      "100 watchlist items",
      "Hourly price checks",
      "Email + SMS alerts",
      "Full price history",
      "Arbitrage alerts",
      "Glitch detection",
    ],
  },
  {
    name: "Pro",
    price: "$79",
    period: "/mo",
    description: "For power sellers who run this as a real business.",
    cta: "Go Pro",
    href: "/signup",
    highlight: false,
    features: [
      "500 watchlist items",
      "5-min price checks",
      "Priority alerts",
      "True profit calculator",
      "Multi-platform sell data",
      "API access",
    ],
  },
  {
    name: "Agency",
    price: "$199",
    period: "/mo",
    description: "For teams managing multiple reseller accounts.",
    cta: "Go Agency",
    href: "/signup",
    highlight: false,
    features: [
      "Unlimited watchlist items",
      "1-min price checks",
      "10 team seats",
      "White-label reports",
      "Dedicated support",
      "Custom integrations",
    ],
  },
];

const testimonials = [
  {
    quote:
      "I found a $400 glitch on a Nintendo Switch bundle at 2am. Made $280 profit. The Hustler plan paid for itself 10x in the first week.",
    author: "Marcus T.",
    role: "Full-time reseller, eBay + Amazon",
    avatar: "MT",
  },
  {
    quote:
      "Every other tool just tracks price history. BargainHuntrs actually tells me the spread between what I can buy it for and what I can sell it for. That's the whole game.",
    author: "Priya K.",
    role: "Side hustler, Walmart → eBay",
    avatar: "PK",
  },
  {
    quote:
      "We run three eBay stores. The Agency plan's team seats and white-label reports have saved us hours every week. Highly recommend.",
    author: "Jason & Sarah L.",
    role: "Agency plan — 3 stores, 6 figures/year",
    avatar: "JL",
  },
];

const stats = [
  { stat: "500+", label: "Retailers tracked" },
  { stat: "$2.4M+", label: "Profit surfaced for users" },
  { stat: "< 60s", label: "Average alert delivery" },
  { stat: "10K+", label: "Active deal hunters" },
];

// ─── Page ──────────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      {/* Impact site verification (content method) */}
      <span hidden aria-hidden="true" style={{ display: "none" }}>
        Impact-Site-Verification: 5ffce628-360e-460e-a608-358e7d45f463
      </span>
      <Header />

      <main className="flex-1 flex flex-col">

        {/* ── Hero ─────────────────────────────────────────────────────── */}
        <section className="relative flex flex-1 items-center justify-center overflow-hidden px-6 py-32 bg-gradient-to-b from-white via-zinc-50/60 to-zinc-100/40 dark:from-zinc-950 dark:via-zinc-900/80 dark:to-zinc-900">
          {/* Background grid decoration */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#e4e4e720_1px,transparent_1px),linear-gradient(to_bottom,#e4e4e720_1px,transparent_1px)] bg-[size:48px_48px] dark:bg-[linear-gradient(to_right,#27272a30_1px,transparent_1px),linear-gradient(to_bottom,#27272a30_1px,transparent_1px)]"
          />

          <div className="relative max-w-4xl text-center">
            {/* Live badge */}
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-white/80 backdrop-blur px-4 py-1.5 text-xs font-medium text-zinc-600 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80 dark:text-zinc-400">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Scanning 500+ retailers right now
            </div>

            <h1 className="text-5xl font-bold tracking-tight text-zinc-900 sm:text-7xl dark:text-zinc-50 leading-[1.08]">
              The arbitrage edge<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 via-emerald-400 to-teal-400">
                your competition doesn&apos;t have.
              </span>
            </h1>

            <p className="mt-6 text-lg leading-8 text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
              BargainHuntrs scans hundreds of retailers in real time, catches pricing glitches within seconds, 
              and shows you the <em>exact profit spread</em> before you spend a dollar.{" "}
              <strong className="font-semibold text-zinc-900 dark:text-zinc-100">
                Every other tool gives you data. We give you deals.
              </strong>
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/signup"
                className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-zinc-900 px-8 py-4 text-sm font-semibold text-white transition-all hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200 shadow-lg"
              >
                Start hunting for free
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              </Link>
              <Link
                href="#vs-competitors"
                className="rounded-xl border border-zinc-300 px-8 py-4 text-sm font-semibold text-zinc-900 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-50 dark:hover:bg-zinc-900"
              >
                See how we compare
              </Link>
            </div>

            <p className="mt-4 text-xs text-zinc-400 dark:text-zinc-600">
              Free plan forever. No credit card. Cancel paid plans anytime.
            </p>
          </div>
        </section>

        {/* ── Stats strip ──────────────────────────────────────────────── */}
        <section className="border-y border-zinc-200 bg-zinc-50/80 px-6 py-8 dark:border-zinc-800 dark:bg-zinc-900/60">
          <div className="mx-auto max-w-6xl flex flex-wrap justify-center gap-10 text-center">
            {stats.map(({ stat, label }) => (
              <div key={label}>
                <p className="text-3xl font-bold text-zinc-900 dark:text-zinc-50 tabular-nums">{stat}</p>
                <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-500">{label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── How it works ─────────────────────────────────────────────── */}
        <section className="px-6 py-24">
          <div className="mx-auto max-w-6xl">
            <div className="text-center mb-16">
              <span className="inline-block rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 mb-4">
                How it works
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-4xl">
                Four steps from scan to profit
              </h2>
            </div>

            <div className="grid gap-0 sm:grid-cols-4">
              {[
                {
                  step: "01",
                  title: "We scan",
                  body: "Our crawlers monitor 500+ retailers every minute, watching for price drops, glitches, and arbitrage gaps.",
                },
                {
                  step: "02",
                  title: "You get alerted",
                  body: "The moment an opportunity hits your criteria — price, margin, platform — we fire an alert to your phone or inbox.",
                },
                {
                  step: "03",
                  title: "Check the math",
                  body: "Our profit calculator shows you true net margin after fees, shipping, and taxes. No surprises.",
                },
                {
                  step: "04",
                  title: "Flip it",
                  body: "Buy through our direct link, then track your resale and ROI right inside BargainHuntrs.",
                },
              ].map(({ step, title, body }, i) => (
                <div key={step} className="relative flex flex-col items-start px-6 py-8">
                  {i < 3 && (
                    <div className="hidden sm:block absolute right-0 top-10 h-px w-full border-t border-dashed border-zinc-300 dark:border-zinc-700" />
                  )}
                  <span className="mb-4 text-4xl font-black text-zinc-200 dark:text-zinc-800 tabular-nums leading-none">
                    {step}
                  </span>
                  <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">{title}</h3>
                  <p className="mt-2 text-sm text-zinc-600 leading-relaxed dark:text-zinc-400">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────────────────────── */}
        <section id="features" className="border-t border-zinc-200 px-6 py-24 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30">
          <div className="mx-auto max-w-6xl">
            <div className="text-center mb-16">
              <span className="inline-block rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 mb-4">
                Features
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-4xl">
                Built for resellers who move fast
              </h2>
              <p className="mt-4 text-base text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto">
                Every feature was built because a competitor doesn&apos;t have it.
              </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {features.map((f) => (
                <div
                  key={f.title}
                  className="group rounded-2xl border border-zinc-200 bg-white p-6 transition-all hover:border-zinc-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">{f.icon}</span>
                    <span className={`text-xs font-semibold uppercase tracking-wider ${f.accent}`}>
                      {f.tag}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                    {f.title}
                  </h3>
                  <p className="mt-2 text-sm text-zinc-600 leading-relaxed dark:text-zinc-400">
                    {f.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── vs Competitors ───────────────────────────────────────────── */}
        <section id="vs-competitors" className="border-t border-zinc-200 px-6 py-24 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl">
            <div className="text-center mb-16">
              <span className="inline-block rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 mb-4">
                vs. The competition
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-4xl">
                We built the tool everyone else forgot to build
              </h2>
              <p className="mt-4 text-base text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
                Tactical Arbitrage is great if you only flip on Amazon. BrickSeek is great if you only shop
                in stores. Keepa is great if charts are your hobby. BargainHuntrs is for people who want to
                make money — on any platform, from any source.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-12">
              {competitors.map((c) => (
                <div
                  key={c.name}
                  className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-50">{c.name}</h3>
                  <p className="mt-0.5 text-xs text-zinc-500">{c.price}</p>
                  <ul className="mt-3 space-y-1.5">
                    {c.weaknesses.map((w) => (
                      <li key={w} className="flex items-start gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
                        <span className="mt-0.5 text-rose-400">✕</span>
                        {w}
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 text-xs text-zinc-500 italic leading-relaxed dark:text-zinc-400">
                    {c.verdict}
                  </p>
                </div>
              ))}
            </div>

            {/* BargainHuntrs "wins" row */}
            <div className="rounded-2xl border-2 border-emerald-500 bg-emerald-50 dark:bg-emerald-950/20 p-6">
              <div className="flex flex-wrap items-center gap-4">
                <span className="text-lg font-bold text-zinc-900 dark:text-zinc-50">BargainHuntrs</span>
                <span className="rounded-full bg-emerald-500 px-2 py-0.5 text-xs font-semibold text-white">
                  From $29/mo
                </span>
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  "✓ Glitch & price-error detection",
                  "✓ Cross-platform arbitrage (any → any)",
                  "✓ True net profit calculator",
                  "✓ 500+ retailers tracked",
                  "✓ Full flip workflow end-to-end",
                  "✓ Instant alerts (< 60 seconds)",
                ].map((item) => (
                  <div key={item} className="flex items-center gap-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Pricing preview ──────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 bg-zinc-50 px-6 py-24 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="mx-auto max-w-6xl">
            <div className="text-center mb-16">
              <span className="inline-block rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900/60 dark:text-zinc-400 mb-4">
                Pricing
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-4xl">
                Priced for hustlers, not hedge funds
              </h2>
              <p className="mt-4 text-base text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto">
                Tactical Arbitrage starts at $59. BuyBotPro starts at $12 and finds you nothing.
                We start at <strong>free</strong> and actually give you deals.
              </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {plans.map((plan) => (
                <div
                  key={plan.name}
                  className={`relative rounded-2xl border p-6 flex flex-col ${
                    plan.highlight
                      ? "border-zinc-900 bg-zinc-900 dark:border-zinc-50 dark:bg-zinc-50"
                      : "border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
                  }`}
                >
                  {"badge" in plan && plan.badge && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="rounded-full bg-emerald-500 px-3 py-0.5 text-xs font-semibold text-white whitespace-nowrap">
                        {plan.badge}
                      </span>
                    </div>
                  )}
                  <h3
                    className={`text-lg font-bold ${
                      plan.highlight
                        ? "text-white dark:text-zinc-900"
                        : "text-zinc-900 dark:text-zinc-50"
                    }`}
                  >
                    {plan.name}
                  </h3>
                  <div className="mt-1 flex items-baseline gap-0.5">
                    <span
                      className={`text-4xl font-bold tabular-nums ${
                        plan.highlight
                          ? "text-white dark:text-zinc-900"
                          : "text-zinc-900 dark:text-zinc-50"
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
                    className={`mt-2 text-xs leading-relaxed ${
                      plan.highlight ? "text-zinc-300 dark:text-zinc-600" : "text-zinc-500"
                    }`}
                  >
                    {plan.description}
                  </p>
                  <ul className="mt-4 space-y-2 flex-1">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-2 text-xs">
                        <span className="mt-0.5 text-emerald-500">✓</span>
                        <span
                          className={
                            plan.highlight
                              ? "text-zinc-200 dark:text-zinc-700"
                              : "text-zinc-600 dark:text-zinc-400"
                          }
                        >
                          {feat}
                        </span>
                      </li>
                    ))}
                  </ul>
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
                </div>
              ))}
            </div>

            <div className="mt-8 text-center">
              <Link
                href="/pricing"
                className="text-sm font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50 underline underline-offset-4 transition-colors"
              >
                Compare all features in detail →
              </Link>
            </div>
          </div>
        </section>

        {/* ── Testimonials ─────────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 px-6 py-24 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl">
            <div className="text-center mb-16">
              <span className="inline-block rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs font-medium text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 mb-4">
                Real results
              </span>
              <h2 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-4xl">
                From the deal hunters themselves
              </h2>
            </div>

            <div className="grid gap-6 sm:grid-cols-3">
              {testimonials.map((t) => (
                <div
                  key={t.author}
                  className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <span key={i} className="text-amber-400 text-sm">★</span>
                    ))}
                  </div>
                  <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                    &ldquo;{t.quote}&rdquo;
                  </p>
                  <div className="mt-4 flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-900 text-xs font-bold text-white dark:bg-zinc-50 dark:text-zinc-900 shrink-0">
                      {t.avatar}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">{t.author}</p>
                      <p className="text-xs text-zinc-500">{t.role}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Final CTA ────────────────────────────────────────────────── */}
        <section className="border-t border-zinc-200 dark:border-zinc-800">
          <div className="bg-zinc-900 dark:bg-zinc-50 px-6 py-28 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white dark:text-zinc-900 sm:text-5xl leading-tight">
              The deal you missed last week<br />
              <span className="text-emerald-400 dark:text-emerald-600">was already in our feed.</span>
            </h2>
            <p className="mt-5 text-base text-zinc-400 dark:text-zinc-600 max-w-xl mx-auto">
              Join 10,000+ resellers who never miss a glitch, never overpay, and always know their
              margin before they buy. Start free — no card, no commitment.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/signup"
                className="rounded-xl bg-emerald-500 px-8 py-4 text-sm font-semibold text-white transition-colors hover:bg-emerald-400 shadow-lg shadow-emerald-500/20"
              >
                Start hunting for free →
              </Link>
              <Link
                href="/contact"
                className="rounded-xl border border-zinc-700 dark:border-zinc-300 px-8 py-4 text-sm font-semibold text-zinc-300 dark:text-zinc-700 transition-colors hover:border-zinc-500 hover:text-white dark:hover:text-zinc-900"
              >
                Join the waitlist
              </Link>
            </div>
            <p className="mt-4 text-xs text-zinc-600 dark:text-zinc-500">
              7-day money-back guarantee on first paid month.
            </p>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
