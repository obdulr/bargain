/**
 * BargainHuntrs Discord Webhook Proxy
 * 
 * Deploy this as a Cloudflare Worker to bypass Discord's Cloudflare
 * IP ban on Render's server IPs. The Worker forwards webhook requests
 * from Render to Discord using Cloudflare's network (which isn't banned).
 * 
 * Deploy:
 * 1. Go to https://dash.cloudflare.com → Workers & Pages
 * 2. Click "Create application" → "Create Worker"
 * 3. Name it "discord-proxy"
 * 4. Replace the code with this file's contents
 * 5. Click "Deploy"
 * 6. Copy the Worker URL (e.g. https://discord-proxy.your-subdomain.workers.dev)
 * 7. Set DISCORD_PROXY_URL in Render env vars to that URL
 * 
 * Usage:
 *   POST https://your-worker.workers.dev/?webhook=ENCODED_WEBHOOK_URL
 *   Body: same JSON you'd send to Discord
 *   Headers: Content-Type: application/json
 * 
 * Security:
 *   - Only accepts POST requests
 *   - Only forwards to discord.com webhook URLs
 *   - Returns 403 for any non-Discord URL
 */

export default {
  async fetch(request, env) {
    // Only allow POST
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Get the webhook URL from query param
    const url = new URL(request.url);
    const webhookEncoded = url.searchParams.get("webhook");
    if (!webhookEncoded) {
      return new Response("Missing webhook parameter", { status: 400 });
    }

    const webhookUrl = decodeURIComponent(webhookEncoded);

    // Security: only allow Discord webhook URLs
    if (!webhookUrl.startsWith("https://discord.com/api/webhooks/") && 
        !webhookUrl.startsWith("https://discordapp.com/api/webhooks/")) {
      return new Response("Only Discord webhook URLs are allowed", { status: 403 });
    }

    try {
      // Forward the request to Discord
      const body = await request.text();
      const response = await fetch(webhookUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "User-Agent": "BargainHuntrs/1.0 (via Cloudflare Worker)",
        },
        body: body,
      });

      // Return the Discord response
      return new Response(response.body, {
        status: response.status,
        headers: {
          "Content-Type": response.headers.get("Content-Type") || "text/plain",
        },
      });
    } catch (err) {
      return new Response(`Proxy error: ${err.message}`, { status: 502 });
    }
  },
};
