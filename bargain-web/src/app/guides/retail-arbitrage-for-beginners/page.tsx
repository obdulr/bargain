import type { Metadata } from "next";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export const dynamic = "force-static";

export const metadata: Metadata = {
  title: "Retail Arbitrage for Beginners: Start Flipping in 2026 | BargainHuntrs",
  description:
    "New to retail arbitrage? This beginner-friendly guide covers everything: what to buy, where to sell, how to calculate profit, and how to avoid common mistakes. Start flipping today.",
  alternates: { canonical: "/guides/retail-arbitrage-for-beginners" },
  openGraph: {
    type: "article",
    siteName: "BargainHuntrs",
    title: "Retail Arbitrage for Beginners: Start Flipping in 2026",
    description:
      "New to retail arbitrage? This beginner-friendly guide covers everything: what to buy, where to sell, how to calculate profit.",
    url: "/guides/retail-arbitrage-for-beginners",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Retail Arbitrage for Beginners" }],
  },
  twitter: {
    card: "summary_large_image",
    site: "@bargain4huntrs",
    creator: "@bargain4huntrs",
    title: "Retail Arbitrage for Beginners: Start Flipping in 2026",
    description: "New to retail arbitrage? This beginner-friendly guide covers everything you need to know.",
    images: ["/og-image.png"],
  },
};

export default function RetailArbitrageBeginners() {
  return (
    <div className="flex flex-col min-h-full bg-white dark:bg-zinc-950">
      <Header />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-12 sm:px-6 lg:px-8">
        <nav className="mb-8 text-sm text-zinc-500">
          <Link href="/" className="hover:text-zinc-900 dark:hover:text-zinc-100">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/guides" className="hover:text-zinc-900 dark:hover:text-zinc-100">Guides</Link>
          <span className="mx-2">/</span>
          <span className="text-zinc-900 dark:text-zinc-100">Retail Arbitrage for Beginners</span>
        </nav>

        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-4xl">
          Retail Arbitrage for Beginners
        </h1>
        <p className="mt-4 text-lg text-zinc-600 dark:text-zinc-400">
          Everything you need to start buying low and selling high. No experience required.
        </p>

        <div className="mt-8 prose prose-zinc dark:prose-invert max-w-none">
          <h2>What is Retail Arbitrage?</h2>
          <p>
            Retail arbitrage is simple: you buy products at a low price from one source (a retail
            store, an online deal, a clearance sale) and resell them at a higher price somewhere
            else (Amazon, eBay, Facebook Marketplace). The profit is the difference between what
            you paid and what you sold it for, minus any fees.
          </p>
          <p>
            It&apos;s one of the most accessible side hustles because:
          </p>
          <ul>
            <li>You can start with as little as $50</li>
            <li>No special skills or training needed</li>
            <li>You can do it from your phone</li>
            <li>It&apos;s scalable — start small, grow as you learn</li>
          </ul>

          <h2>Where to Find Deals to Flip</h2>
          <h3>Online Sources</h3>
          <ul>
            <li><strong>Amazon</strong> — Price glitches, Lightning Deals, Warehouse Deals</li>
            <li><strong>Walmart</strong> — Clearance, Rollback deals, online-only markdowns</li>
            <li><strong>Target</strong> — Clearance sections, Cartwheel offers</li>
            <li><strong>ADOR</strong> — Fashion deals with 50%+ discounts</li>
            <li><Link href="/" className="text-blue-600 hover:text-blue-700">BargainHuntrs</Link> — Scans all of these and more in real time</li>
          </ul>

          <h3>In-Store Sources</h3>
          <ul>
            <li><strong>Walmart clearance aisles</strong> — Yellow-tagged items with deep discounts</li>
            <li><strong>Target dollar spot</strong> — Seasonal items that resell well</li>
            <li><strong>TJ Maxx / Marshalls</strong> — Brand-name products below retail</li>
            <li><strong>Goodwill / thrift stores</strong> — Vintage and brand-name finds</li>
            <li><strong>Garage sales</strong> — Best for collectibles and unique items</li>
          </ul>

          <h2>Where to Sell</h2>
          <ul>
            <li><strong>Amazon FBA</strong> — Highest fees but easiest to scale. Amazon handles shipping and customer service.</li>
            <li><strong>eBay</strong> — Best for unique/collectible items. Lower fees than Amazon.</li>
            <li><strong>Facebook Marketplace</strong> — No fees, local pickup. Best for bulky items.</li>
            <li><strong>Poshmark / Mercari</strong> — Best for clothing and fashion.</li>
            <li><strong>Your own website</strong> — Highest margins but requires marketing.</li>
          </ul>

          <h2>How to Calculate Profit</h2>
          <p>
            Before buying anything, calculate your profit using this formula:
          </p>
          <p className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-900">
            <strong>Profit = Sell Price - Buy Price - Platform Fees - Shipping - Other Costs</strong>
          </p>
          <p>
            Use the <Link href="/tools/profit-calculator" className="text-blue-600 hover:text-blue-700">BargainHuntrs
            Profit Calculator</Link> to automate this. It factors in Amazon FBA fees, eBay fees,
            and shipping costs.
          </p>
          <p>
            <strong>Rule of thumb:</strong> Aim for at least 30% ROI and $10 minimum profit per
            item. If a deal doesn&apos;t meet both criteria, skip it.
          </p>

          <h2>Best Categories for Beginners</h2>
          <ul>
            <li><strong>Electronics accessories</strong> — Phone cases, chargers, cables. Small, lightweight, high demand.</li>
            <li><strong>Beauty &amp; personal care</strong> — Skincare, hair products. Consistent demand.</li>
            <li><strong>Home &amp; kitchen</strong> — Small appliances, cookware. Good margins.</li>
            <li><strong>Toys</strong> — Especially during Q4 (holiday season).</li>
            <li><strong>Books</strong> — Textbooks and niche non-fiction. Easy to source.</li>
          </ul>

          <h2>5 Tips for Success</h2>
          <ol>
            <li><strong>Start small.</strong> Buy 3-5 items first. Learn the process before scaling.</li>
            <li><strong>Always check the selling price</strong> on your target platform before buying.</li>
            <li><strong>Factor in all fees.</strong> The deal isn&apos;t profitable if fees eat your margin.</li>
            <li><strong>Use deal alerts.</strong> <Link href="/signup" className="text-blue-600 hover:text-blue-700">Sign up for BargainHuntrs</Link> to get notified when profitable deals appear.</li>
            <li><strong>Keep good records.</strong> Track every purchase and sale for tax purposes.</li>
          </ol>

          <h2>Common Beginner Mistakes</h2>
          <ul>
            <li>Buying without checking the current selling price</li>
            <li>Forgetting about shipping costs</li>
            <li>Buying items with high return rates (clothing sizes vary)</li>
            <li>Not accounting for Amazon&apos;s long-term storage fees</li>
            <li>Buying too many of one product before testing demand</li>
          </ul>

          <h2>Ready to Start?</h2>
          <p>
            <Link href="/signup" className="text-blue-600 hover:text-blue-700">Create a free BargainHuntrs account</Link> to
            start finding profitable deals. Use the{" "}
            <Link href="/tools/profit-calculator" className="text-blue-600 hover:text-blue-700">profit calculator</Link> to
            check margins, and the{" "}
            <Link href="/tools/listing-generator" className="text-blue-600 hover:text-blue-700">listing generator</Link> to
            create resale listings.
          </p>
          <div className="mt-8 rounded-xl bg-blue-50 p-6 dark:bg-blue-950">
            <p className="text-center">
              <Link href="/signup" className="text-lg font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400">
                Get Started for Free →
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-12 border-t border-zinc-200 pt-8 dark:border-zinc-800">
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">Related Guides</h2>
          <ul className="mt-4 space-y-2">
            <li><Link href="/guides/amazon-arbitrage-guide" className="text-blue-600 hover:text-blue-700">Amazon Arbitrage: Complete Guide</Link></li>
            <li><Link href="/guides/how-to-find-price-glitches" className="text-blue-600 hover:text-blue-700">How to Find Price Glitches</Link></li>
            <li><Link href="/guides/best-times-to-find-deals" className="text-blue-600 hover:text-blue-700">Best Times to Find Deals Online</Link></li>
          </ul>
        </div>
      </main>
      <Footer />
    </div>
  );
}
