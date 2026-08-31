import type { Metadata } from "next";
import { getPublicDeals, type ArbitrageDeal } from "@/lib/api";
import { discountPercent, savingsAmount, isToday } from "@/lib/seo-helpers";
import SeoPageLayout from "@/components/SeoPageLayout";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Today's Best Deals — Daily Deals Updated Hourly | BargainHuntrs",
  description:
    "Find the best deals today across Amazon, Walmart, and more. Today's top deals with savings percentages, retailer names, and affiliate links. Updated hourly.",
  alternates: { canonical: "/deals/today" },
  openGraph: {
    type: "website",
    siteName: "BargainHuntrs",
    title: "Today's Best Deals — Daily Deals Updated Hourly | BargainHuntrs",
    description:
      "Find the best deals today across Amazon, Walmart, and more. Today's top deals with savings percentages, retailer names, and affiliate links. Updated hourly.",
    url: "/deals/today",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Today's Best Deals" }],
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title: "Today's Best Deals — Daily Deals Updated Hourly | BargainHuntrs",
    description:
      "Find the best deals today across Amazon, Walmart, and more. Updated hourly.",
    images: ["/og-image.png"],
  },
};

const RELATED_LINKS = [
  { href: "/deals/amazon-deals", label: "Amazon Deals" },
  { href: "/deals/walmart-deals", label: "Walmart Deals" },
  { href: "/deals/price-drops", label: "Price Drops" },
  { href: "/deals/over-50-off", label: "Over 50% Off" },
  { href: "/deals/under-10", label: "Deals Under $10" },
  { href: "/deals/clearance", label: "Clearance Deals" },
];

const FAQS = [
  {
    question: "How often are today's deals updated?",
    answer:
      "Our scanners run continuously throughout the day, detecting new deals, price drops, and clearance items as they go live. The list on this page is refreshed hourly to show you the most current opportunities.",
  },
  {
    question: "Are these deals available for a limited time?",
    answer:
      "Yes. Most deals are temporary and can sell out or expire quickly. Price glitches and clearance items especially tend to disappear within hours. We recommend acting fast on any deal that interests you.",
  },
  {
    question: "Do I need to pay to see today's deals?",
    answer:
      "No. Browsing today's deals is completely free. You can view deal titles, retailers, and savings percentages without an account. Sign up for a free account to unlock full pricing details and instant alerts.",
  },
  {
    question: "Which retailers are included in today's deals?",
    answer:
      "We scan over 500 retailers including Amazon, Walmart, Target, Best Buy, Home Depot, Costco, Lowe's, eBay, Newegg, and many more. Deals from all of these retailers appear on this page.",
  },
];

export default async function TodayDealsPage() {
  let deals: ArbitrageDeal[] = [];
  let error = "";
  try {
    const data = await getPublicDeals(200, 0);
    deals = data
      .filter((d) => isToday(d.detected_at) || discountPercent(d) > 0)
      .sort((a, b) => discountPercent(b) - discountPercent(a) || savingsAmount(b) - savingsAmount(a))
      .slice(0, 48);
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load deals";
  }

  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQS.map((f) => ({
      "@type": "Question",
      name: f.question,
      acceptedAnswer: { "@type": "Answer", text: f.answer },
    })),
  };

  const itemListJsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Today's Best Deals",
    url: "https://www.bargainhuntrs.com/deals/today",
    description:
      "Curated list of today's top deals with savings percentages and retailer names.",
  };

  return (
    <SeoPageLayout
      config={{
        title: "Today's Best Deals",
        description:
          "A curated list of today's top deals across Amazon, Walmart, Target, and more. Savings percentages, retailer names, and direct affiliate links. Updated hourly.",
        source: "today_deals",
        showRank: true,
        faqs: FAQS,
        relatedLinks: RELATED_LINKS,
        jsonLd: [faqJsonLd, itemListJsonLd],
        introContent: (
          <>
            <p>
              Welcome to <strong>Today's Best Deals</strong> from BargainHuntrs. Every day,
              our scanners monitor over 500 retailers to find the biggest discounts, steepest
              price drops, and hidden clearance items. This page is updated hourly so you
              never miss a bargain.
            </p>
            <p>
              Each deal below includes the savings percentage, the retailer name, and a direct
              affiliate link so you can grab the deal before it's gone. Deals can sell out
              quickly, so act fast on anything that catches your eye.
            </p>
          </>
        ),
      }}
      deals={deals}
      error={error}
    />
  );
}
