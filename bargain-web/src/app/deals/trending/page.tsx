import type { Metadata } from "next";
import TrendingDealsClient from "./TrendingDealsClient";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Trending Deals — Biggest Price Drops & Best Flips | BargainHuntrs",
  description:
    "See the hottest deals trending right now. Biggest price drops, highest profit margins, and most popular deals updated in real time.",
  alternates: { canonical: "/deals/trending" },
  openGraph: {
    type: "website",
    siteName: "BargainHuntrs",
    title: "Trending Deals — Biggest Price Drops & Best Flips | BargainHuntrs",
    description:
      "See the hottest deals trending right now. Biggest price drops, highest profit margins, and most popular deals updated in real time.",
    url: "/deals/trending",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Trending Deals — Biggest Price Drops & Best Flips | BargainHuntrs",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title: "Trending Deals — Biggest Price Drops & Best Flips | BargainHuntrs",
    description:
      "See the hottest deals trending right now. Biggest price drops, highest profit margins, and most popular deals updated in real time.",
    images: ["/og-image.png"],
  },
};

export default function TrendingDealsPage() {
  return <TrendingDealsClient />;
}
