import type { MetadataRoute } from "next";

const BASE_URL = "https://www.bargainhuntrs.com";

export const dynamic = "force-static";

/**
 * Generates /robots.txt — allows all crawlers and points at the sitemap.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    sitemap: `${BASE_URL}/sitemap.xml`,
    host: BASE_URL,
  };
}
