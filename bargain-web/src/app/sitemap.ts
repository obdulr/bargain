import type { MetadataRoute } from "next";

const BASE_URL = "https://www.bargainhuntrs.com";
const API_URL = "https://api.bargainhuntrs.com";

interface ApiDeal {
  id: string;
  detected_at?: string;
}

/**
 * Generates the sitemap at /sitemap.xml.
 *
 * Includes the static marketing pages plus a dynamic entry for every active
 * deal surfaced by the public arbitrage deals endpoint.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();

  const staticPages: MetadataRoute.Sitemap = [
    { url: `${BASE_URL}/`, lastModified: now, changeFrequency: "hourly", priority: 1 },
    { url: `${BASE_URL}/deals`, lastModified: now, changeFrequency: "hourly", priority: 0.9 },
    { url: `${BASE_URL}/deals/best`, lastModified: now, changeFrequency: "daily", priority: 0.8 },
    { url: `${BASE_URL}/deals/amazon`, lastModified: now, changeFrequency: "daily", priority: 0.8 },
    { url: `${BASE_URL}/deals/retailers`, lastModified: now, changeFrequency: "weekly", priority: 0.6 },
    { url: `${BASE_URL}/community`, lastModified: now, changeFrequency: "daily", priority: 0.7 },
    { url: `${BASE_URL}/seller`, lastModified: now, changeFrequency: "weekly", priority: 0.6 },
    { url: `${BASE_URL}/admin`, lastModified: now, changeFrequency: "monthly", priority: 0.3 },
  ];

  // Dynamic deal pages — fetch active deals from the public API.
  let dealPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`${API_URL}/api/v1/arbitrage/deals?limit=500`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const deals: ApiDeal[] = await res.json();
      dealPages = deals.map((deal) => ({
        url: `${BASE_URL}/deals/${deal.id}`,
        lastModified: deal.detected_at ? new Date(deal.detected_at) : now,
        changeFrequency: "daily",
        priority: 0.7,
      }));
    }
  } catch {
    // If the API is unreachable, fall back to static pages only.
  }

  return [...staticPages, ...dealPages];
}
