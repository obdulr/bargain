import type { Metadata } from "next";
import DealPageClient from "./DealPageClient";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Deal Details | BargainHuntrs",
  description: "View this deal on BargainHuntrs — find it, flip it, profit.",
  openGraph: {
    type: "website",
    title: "Deal Details | BargainHuntrs",
    description: "View this deal on BargainHuntrs — find it, flip it, profit.",
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title: "Deal Details | BargainHuntrs",
    description: "View this deal on BargainHuntrs — find it, flip it, profit.",
  },
};

export default function DealDetailPage() {
  return <DealPageClient />;
}
