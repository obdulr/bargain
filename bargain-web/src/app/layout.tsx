import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import PwaInstallPrompt from "@/components/PwaInstallPrompt";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const title = "Bargain Huntrs - Discover Deals, Glitches & Price Drops";
const description =
  "Find the best Amazon, Walmart, Target, and eBay deals, price errors, and clearance bargains. Join our deal-hunting community.";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.bargainhuntrs.com"),
  title,
  description,
  openGraph: {
    type: "website",
    url: "https://www.bargainhuntrs.com",
    title,
    description,
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title,
    description,
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#18181b" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Bargain Huntrs" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <meta name="impact-site-verification" content="c2aacb17-49a0-4116-b515-be1a7e596103" />
        <meta name="Impact-Site-Verification" content="c2aacb17-49a0-4116-b515-be1a7e596103" />
      </head>
      <body className="min-h-full flex flex-col">
        {/* Impact tracking script for affiliate verification */}
        <Script
          id="impact-tracking"
          type="text/javascript"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(i,m,p,a,c,t){c.ire_o=p;c[p]=c[p]||function(){(c[p].a=c[p].a||[]).push(arguments)};t=a.createElement(m);var z=a.getElementsByTagName(m)[0];t.async=1;t.src=i;z.parentNode.insertBefore(t,z)})('https://utt.impactcdn.com/P-A1208408-03fa-4fd4-a07a-20e974bc746d1.js','script','impactStat',document,window);impactStat('transformLinks');impactStat('trackImpression');`,
          }}
        />
        <AuthProvider>{children}</AuthProvider>
        <PwaInstallPrompt />
      </body>
    </html>
  );
}
