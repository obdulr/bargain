import type { Metadata } from "next";
import CalendarClient from "./CalendarClient";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Deal Calendar 2026 — Best Times to Buy & Sell | BargainHuntrs",
  description:
    "Track every major sale event in 2026. Know when to buy for maximum discounts and when to sell for maximum profit. Black Friday, Prime Day, Memorial Day, and more.",
  alternates: { canonical: "/deals/calendar" },
  openGraph: {
    type: "website",
    siteName: "BargainHuntrs",
    title: "Deal Calendar 2026 — Best Times to Buy & Sell | BargainHuntrs",
    description:
      "Track every major sale event in 2026. Know when to buy for maximum discounts and when to sell for maximum profit. Black Friday, Prime Day, Memorial Day, and more.",
    url: "/deals/calendar",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Deal Calendar 2026 — Best Times to Buy & Sell | BargainHuntrs",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title: "Deal Calendar 2026 — Best Times to Buy & Sell | BargainHuntrs",
    description:
      "Track every major sale event in 2026. Know when to buy for maximum discounts and when to sell for maximum profit. Black Friday, Prime Day, Memorial Day, and more.",
    images: ["/og-image.png"],
  },
};

export default function CalendarPage() {
  return <CalendarClient />;
}
