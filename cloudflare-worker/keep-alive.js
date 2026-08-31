// Cloudflare Worker: Keep-alive ping for Render free-tier services
// Runs every 10 minutes via cron trigger to prevent Render spin-down

export default {
  async scheduled(event, env) {
    const services = [
      "https://api.bargainhuntrs.com/health",
      "https://api.settleinpeace.com/health",
    ];

    for (const url of services) {
      try {
        const res = await fetch(url, {
          method: "GET",
          headers: { "User-Agent": "Cloudflare-KeepAlive/1.0" },
        });
        console.log(`Pinged ${url}: ${res.status}`);
      } catch (e) {
        console.error(`Failed to ping ${url}: ${e}`);
      }
    }
  },

  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/ping") {
      const services = [
        "https://api.bargainhuntrs.com/health",
        "https://api.settleinpeace.com/health",
      ];
      const results = [];
      for (const svc of services) {
        try {
          const res = await fetch(svc, {
            headers: { "User-Agent": "Cloudflare-KeepAlive/1.0" },
          });
          results.push({ url: svc, status: res.status });
        } catch (e) {
          results.push({ url: svc, error: String(e) });
        }
      }
      return new Response(JSON.stringify({ results }, null, 2), {
        headers: { "Content-Type": "application/json" },
      });
    }
    return new Response("Keep-alive worker. Visit /ping to manually trigger.", {
      status: 200,
    });
  },
};
