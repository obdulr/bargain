// Cloudflare Pages Function: Dynamic sitemap
// Runs on Cloudflare's edge network, fetches active deals from the API at request time

const BASE_URL = "https://www.bargainhuntrs.com";
const API_URL = "https://api.bargainhuntrs.com";
const MAX_LIMIT = 200;

export async function onRequestGet() {
  const now = new Date().toISOString();

  const staticUrls = [
    { loc: `${BASE_URL}/`, lastmod: now, changefreq: "hourly", priority: "1.0" },
    { loc: `${BASE_URL}/deals`, lastmod: now, changefreq: "hourly", priority: "0.9" },
    { loc: `${BASE_URL}/deals/best`, lastmod: now, changefreq: "daily", priority: "0.8" },
    { loc: `${BASE_URL}/deals/amazon`, lastmod: now, changefreq: "daily", priority: "0.8" },
    { loc: `${BASE_URL}/deals/today`, lastmod: now, changefreq: "hourly", priority: "0.9" },
    { loc: `${BASE_URL}/deals/amazon-deals`, lastmod: now, changefreq: "hourly", priority: "0.8" },
    { loc: `${BASE_URL}/deals/walmart-deals`, lastmod: now, changefreq: "hourly", priority: "0.8" },
    { loc: `${BASE_URL}/deals/clearance`, lastmod: now, changefreq: "hourly", priority: "0.8" },
    { loc: `${BASE_URL}/deals/trending`, lastmod: now, changefreq: "daily", priority: "0.7" },
    { loc: `${BASE_URL}/deals/retailers`, lastmod: now, changefreq: "weekly", priority: "0.6" },
    { loc: `${BASE_URL}/retailers`, lastmod: now, changefreq: "weekly", priority: "0.8" },
    { loc: `${BASE_URL}/deals/calendar`, lastmod: now, changefreq: "monthly", priority: "0.7" },
    { loc: `${BASE_URL}/community`, lastmod: now, changefreq: "daily", priority: "0.7" },
    { loc: `${BASE_URL}/seller`, lastmod: now, changefreq: "weekly", priority: "0.6" },
    { loc: `${BASE_URL}/pricing`, lastmod: now, changefreq: "monthly", priority: "0.5" },
    { loc: `${BASE_URL}/coupons`, lastmod: now, changefreq: "daily", priority: "0.6" },
    { loc: `${BASE_URL}/tools/profit-calculator`, lastmod: now, changefreq: "monthly", priority: "0.7" },
    { loc: `${BASE_URL}/tools/listing-generator`, lastmod: now, changefreq: "monthly", priority: "0.7" },
    { loc: `${BASE_URL}/guides`, lastmod: now, changefreq: "weekly", priority: "0.8" },
    { loc: `${BASE_URL}/guides/how-to-find-price-glitches`, lastmod: now, changefreq: "monthly", priority: "0.8" },
    { loc: `${BASE_URL}/guides/amazon-arbitrage-guide`, lastmod: now, changefreq: "monthly", priority: "0.8" },
    { loc: `${BASE_URL}/guides/retail-arbitrage-for-beginners`, lastmod: now, changefreq: "monthly", priority: "0.8" },
    { loc: `${BASE_URL}/guides/best-times-to-find-deals`, lastmod: now, changefreq: "monthly", priority: "0.7" },
  ];

  // Fetch active deals from the public API (paginate, max 200 per request)
  let dealUrls: any[] = [];
  try {
    for (let offset = 0; offset < 2000; offset += MAX_LIMIT) {
      const res = await fetch(
        `${API_URL}/api/v1/arbitrage/deals/public?limit=${MAX_LIMIT}&offset=${offset}`,
        { headers: { "User-Agent": "BargainHuntrs-Sitemap/1.0" } }
      );
      if (!res.ok) break;
      const deals = await res.json();
      if (!Array.isArray(deals) || deals.length === 0) break;
      dealUrls.push(
        ...deals.map((deal: any) => ({
          loc: `${BASE_URL}/deals/${deal.id}`,
          lastmod: deal.detected_at || deal.updated_at || now,
          changefreq: "daily",
          priority: "0.7",
        }))
      );
      if (deals.length < MAX_LIMIT) break;
    }
  } catch {
    // If API is unreachable, return static pages only
  }

  const allUrls = [...staticUrls, ...dealUrls];

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allUrls
  .map(
    (u) =>
      `  <url>\n    <loc>${u.loc}</loc>\n    <lastmod>${u.lastmod}</lastmod>\n    <changefreq>${u.changefreq}</changefreq>\n    <priority>${u.priority}</priority>\n  </url>`
  )
  .join("\n")}
</urlset>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
      "X-Sitemap-Deals": String(dealUrls.length),
    },
  });
}
