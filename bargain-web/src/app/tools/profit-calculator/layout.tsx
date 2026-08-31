import type { Metadata } from "next";

const TITLE =
  "Arbitrage Profit Calculator — Free eBay, Amazon Flip Calculator | BargainHuntrs";
const DESCRIPTION =
  "Free arbitrage profit calculator. Calculate your net profit, ROI, and fees for eBay, Amazon, Facebook Marketplace, and more. Find out if a deal is worth flipping.";
const URL = "https://www.bargainhuntrs.com/tools/profit-calculator";

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  keywords: [
    "arbitrage calculator",
    "ebay profit calculator",
    "amazon flip calculator",
    "resale profit calculator",
    "flip calculator",
    "arbitrage profit calculator",
    "online arbitrage calculator",
    "retail arbitrage calculator",
  ],
  alternates: { canonical: "/tools/profit-calculator" },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: URL,
    siteName: "BargainHuntrs",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
};

export default function ProfitCalculatorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
