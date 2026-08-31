import type { Metadata } from "next";
import HomePageContent from "@/app/HomePageContent";

export const metadata: Metadata = {
  title: "BargainHuntrs — Find It, Flip It, Profit | Deal Discovery & Arbitrage",
  description:
    "Discover the best deals, discounts, clearance items, and arbitrage opportunities. Track prices, get alerts, and maximize your profits.",
  alternates: { canonical: "/" },
  openGraph: {
    title: "BargainHuntrs — Find It, Flip It, Profit | Deal Discovery & Arbitrage",
    description:
      "Discover the best deals, discounts, clearance items, and arbitrage opportunities. Track prices, get alerts, and maximize your profits.",
    url: "/",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "BargainHuntrs",
  url: "https://www.bargainhuntrs.com",
  logo: "https://www.bargainhuntrs.com/og-image.png",
  description:
    "Discover the best deals, discounts, clearance items, and arbitrage opportunities from Amazon, Walmart, and more.",
  sameAs: [
    "https://twitter.com/bargain4huntrs",
  ],
};

const dealsJsonLd = {
  "@context": "https://schema.org",
  "@type": "ItemList",
  name: "Today's Top Deals",
  url: "https://www.bargainhuntrs.com",
  description:
    "Live arbitrage deals and price errors from major retailers, updated throughout the day.",
};

export default function HomePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(dealsJsonLd) }}
      />
      <HomePageContent />
    </>
  );
}
// Auto-deploy test: Sun Aug 30 17:11:31 PDT 2026
