"""HTTP client with anti-detection features for web scraping.

Provides rotating user agents, realistic browser headers, rate limiting,
retry logic, and optional proxy support. This is the foundation for all
scrapers — every HTTP request should go through this client.

Uses ``curl_cffi`` for TLS fingerprint impersonation when available, which
mimics real browser TLS handshakes and bypasses the JA3/JA4 fingerprinting
that sites like eBay and Amazon use to block ``httpx``/``requests``. Falls
back to plain ``httpx`` if ``curl_cffi`` is not installed.
"""
import asyncio
import random
import time
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Try to import curl_cffi for TLS fingerprint impersonation
try:
    from curl_cffi import requests as cffi_requests
    _HAS_CFFI = True
except ImportError:
    _HAS_CFFI = False
    logger.info("curl_cffi not installed — falling back to httpx (weaker anti-detection)")

# Realistic desktop browser user agents (Chrome, Firefox, Safari, Edge)
# Updated regularly to match current browser versions
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:131.0) Gecko/20100101 Firefox/131.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# Browser profiles for curl_cffi impersonation. We rotate through these so
# different requests look like different browsers.
IMPERSONATE_PROFILES = ["chrome", "firefox", "safari"]


def _build_headers(user_agent: str, referer: Optional[str] = None) -> dict:
    """Build realistic browser headers."""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    if referer:
        headers["Referer"] = referer
    return headers


class ScrapingClient:
    """Async HTTP client with anti-detection, rate limiting, and retries.

    Uses ``curl_cffi`` with browser TLS fingerprint impersonation when
    available (bypasses JA3/JA4 fingerprinting used by Amazon and eBay).
    Falls back to ``httpx`` otherwise.

    Usage:
        async with ScrapingClient() as client:
            html = await client.get_html("https://www.amazon.com/dp/B08N5WRWNW")
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        rate_limit_seconds: float = 2.0,
        proxy_url: Optional[str] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.rate_limit_seconds = rate_limit_seconds
        self.proxy_url = proxy_url
        self._last_request_time: dict[str, float] = {}  # per-domain rate limiting
        self._client: Optional[httpx.AsyncClient] = None  # httpx fallback
        self._cffi_session = None  # curl_cffi session

    async def __aenter__(self):
        if _HAS_CFFI:
            # curl_cffi sessions maintain cookies across requests (important
            # for Amazon/eBay which set session cookies on first visit).
            self._cffi_session = cffi_requests.Session()
        else:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                proxy=self.proxy_url,
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._cffi_session:
            try:
                self._cffi_session.close()
            except Exception:
                pass
            self._cffi_session = None

    async def _rate_limit(self, domain: str):
        """Enforce per-domain rate limiting."""
        now = time.time()
        last = self._last_request_time.get(domain, 0)
        elapsed = now - last
        if elapsed < self.rate_limit_seconds:
            wait = self.rate_limit_seconds - elapsed
            logger.debug(f"Rate limiting {domain}: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        self._last_request_time[domain] = time.time()

    def _do_cffi_request(self, url: str, headers: dict) -> tuple[int, str]:
        """Synchronous curl_cffi request. Returns (status_code, html).

        When using curl_cffi impersonation, the library sets its own
        User-Agent and TLS fingerprint to match the impersonated browser.
        We strip browser-identifying headers from ``headers`` so they don't
        conflict with the impersonation (mixing a Chrome TLS fingerprint
        with a Firefox User-Agent triggers bot detection).
        """
        profile = random.choice(IMPERSONATE_PROFILES)
        proxies = self.proxy_url if self.proxy_url else None
        # Remove headers that the impersonation profile sets itself.
        # Keeping these would create a mismatch between the TLS fingerprint
        # and the HTTP headers, which sites detect. curl_cffi sets User-Agent,
        # Accept-Encoding, sec-ch-ua, and Sec-Fetch-* headers to match the
        # impersonated browser — overriding any of them triggers detection.
        safe_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in (
                "user-agent",
                "accept-encoding",
                "sec-ch-ua",
                "sec-ch-ua-mobile",
                "sec-ch-ua-platform",
                "sec-fetch-dest",
                "sec-fetch-mode",
                "sec-fetch-site",
                "sec-fetch-user",
            )
        }
        response = self._cffi_session.get(
            url,
            headers=safe_headers,
            impersonate=profile,
            proxies=proxies,
            timeout=30,
            allow_redirects=True,
        )
        return response.status_code, response.text

    async def get_html(
        self,
        url: str,
        referer: Optional[str] = None,
        extra_headers: Optional[dict] = None,
    ) -> Optional[str]:
        """Fetch HTML with retries, rate limiting, and anti-detection.

        Returns HTML string or None if all retries fail.
        """
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        for attempt in range(self.max_retries):
            await self._rate_limit(domain)

            user_agent = random.choice(USER_AGENTS)
            headers = _build_headers(user_agent, referer)
            if extra_headers:
                headers.update(extra_headers)

            try:
                logger.debug(f"GET {url} (attempt {attempt + 1}/{self.max_retries})")

                if _HAS_CFFI and self._cffi_session:
                    # Run the synchronous curl_cffi request in a thread
                    # so it doesn't block the asyncio event loop.
                    status_code, html = await asyncio.to_thread(
                        self._do_cffi_request, url, headers
                    )
                else:
                    response = await self._client.get(url, headers=headers)
                    status_code = response.status_code
                    html = response.text

                # Check for common anti-bot responses
                if status_code == 429:
                    # Rate limited — wait longer
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limited (429) on {domain}, waiting {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue

                if status_code == 503:
                    # Service unavailable — often means bot detection
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 2)
                    logger.warning(f"503 on {domain} (possible bot detection), waiting {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue

                # 403/404 are often used as bot-detection responses (Amazon
                # returns 404 for blocked requests). Treat them as retryable
                # when the body looks like a captcha/robot page.
                if status_code in (403, 404):
                    if html and ("captcha" in html.lower() or "robot" in html.lower()
                                 or "automated" in html.lower()):
                        delay = self.base_delay * (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(
                            f"{status_code} with captcha/robot text on {domain}, "
                            f"waiting {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue
                    # Genuine 403/404 — no point retrying
                    logger.warning(f"HTTP {status_code} on {url} (not a captcha page)")
                    if attempt < self.max_retries - 1:
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        await asyncio.sleep(delay + random.uniform(0, 0.5))
                    continue

                if status_code >= 400:
                    logger.warning(f"HTTP {status_code} on {url}")
                    if attempt < self.max_retries - 1:
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        await asyncio.sleep(delay + random.uniform(0, 0.5))
                    continue

                # Check for captcha pages (even on 200 status — Amazon does this)
                if html and ("captcha" in html.lower()
                             or "Type the characters you see in this image" in html):
                    logger.warning(f"Captcha detected on {domain}")
                    # Wait longer and retry with different user agent
                    delay = self.base_delay * (2 ** attempt) + random.uniform(1, 3)
                    await asyncio.sleep(delay)
                    continue

                return html

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP {e.response.status_code} on {url}")
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay + random.uniform(0, 0.5))
            except httpx.RequestError as e:
                logger.warning(f"Request error on {url}: {e}")
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    await asyncio.sleep(delay + random.uniform(0, 0.5))
            except Exception as e:
                logger.error(f"Unexpected error on {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay)

        logger.error(f"All {self.max_retries} attempts failed for {url}")
        return None
