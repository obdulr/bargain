// Shared pricing plan data used by both the server-rendered pricing page
// (comparison table / FAQ) and the client-side plan cards (Stripe checkout).
//
// `planId` maps each frontend plan to a backend subscription plan id
// ("free" | "pro" | "enterprise") used by the /subscriptions/create-checkout-session
// endpoint. The actual Stripe price is configured via env vars on the backend.

export interface PlanFeature {
  label: string;
  value: string;
}

export interface Plan {
  name: string;
  planId: "free" | "pro" | "enterprise";
  price: string;
  period: string;
  tagline: string;
  description: string;
  cta: string;
  href: string;
  highlight: boolean;
  badge: string | null;
  features: PlanFeature[];
}

export const plans: Plan[] = [
  {
    name: "Free",
    planId: "free",
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
    planId: "pro",
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
    planId: "enterprise",
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
    planId: "enterprise",
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
