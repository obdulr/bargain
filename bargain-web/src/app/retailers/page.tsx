import type { Metadata } from "next";
import RetailersClient from "./RetailersClient";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Tracked Retailers — 30+ Stores Scanned for Deals | BargainHuntrs",
  description:
    "Browse deals from Amazon, Walmart, Target, Best Buy, and 30+ other retailers. We scan for price drops, glitches, and clearance deals in real time.",
  alternates: { canonical: "/retailers" },
  openGraph: {
    type: "website",
    siteName: "BargainHuntrs",
    title: "Tracked Retailers — 30+ Stores Scanned for Deals | BargainHuntrs",
    description:
      "Browse deals from Amazon, Walmart, Target, Best Buy, and 30+ other retailers. We scan for price drops, glitches, and clearance deals in real time.",
    url: "/retailers",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Tracked Retailers — 30+ Stores Scanned for Deals | BargainHuntrs",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title: "Tracked Retailers — 30+ Stores Scanned for Deals | BargainHuntrs",
    description:
      "Browse deals from Amazon, Walmart, Target, Best Buy, and 30+ other retailers. We scan for price drops, glitches, and clearance deals in real time.",
    images: ["/og-image.png"],
  },
};

export default function RetailersPage() {
  return <RetailersClient />;
}
