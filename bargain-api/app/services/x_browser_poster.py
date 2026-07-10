"""X (Twitter) Auto-Posting via Chrome Browser Automation.

Posts deals to the @bargain4huntrs X account by automating the X web
interface using Chrome with CDP (Chrome DevTools Protocol). This avoids
the X API's pay-per-use costs ($0.20 per post with a link).

The approach:
1. Copy the user's Chrome profile (Profile 10 / Prime) to a temp dir
2. Launch Chrome with remote debugging on port 9222
3. Connect via Playwright CDP
4. Navigate to X, compose and post the tweet
5. Clean up the temp profile

This runs locally on the dev machine. For production, it would need
to run on a server with Chrome installed and an active X session.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")
SOURCE_PROFILE = os.path.join(CHROME_USER_DATA, "Profile 10")
DEBUG_PORT = 9222


@dataclass
class XPostResult:
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None
    tweet_text: str = ""


def _format_deal_tweet(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
) -> str:
    """Format a deal into a tweet (max 280 characters)."""
    retailer_names = {
        "amazon": "Amazon",
        "ebay": "eBay",
        "walmart": "Walmart",
        "home_depot": "Home Depot",
        "target": "Target",
        "best_buy": "Best Buy",
        "newegg": "Newegg",
        "costco": "Costco",
        "lowes": "Lowe's",
        "ace_hardware": "Ace Hardware",
        "corsair": "Corsair",
    }
    retailer_name = retailer_names.get(retailer, retailer.replace("_", " ").title())

    if deal_tier == "glitch":
        prefix = "⚡ PRICE ERROR"
        hashtags = "#priceerror #deal"
    elif deal_tier == "clearance":
        prefix = f"🔥 {discount_percent}% OFF"
        hashtags = "#deals #clearance"
    else:
        prefix = f"🔥 {discount_percent}% OFF"
        hashtags = "#deals #bargain"

    max_title_len = 80
    short_title = title[:max_title_len].strip()
    if len(title) > max_title_len:
        short_title += "…"

    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        price_line = f"${deal_price:.0f} (was ${original_price:.0f}) at {retailer_name}\nSave ${savings:.0f}"
    else:
        price_line = f"${deal_price:.0f} at {retailer_name}"

    tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}\n\n{hashtags}"

    if len(tweet) > 280:
        excess = len(tweet) - 280
        short_title = title[: max(20, max_title_len - excess - 1)].strip() + "…"
        tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}\n\n{hashtags}"
        if len(tweet) > 280:
            tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}"

    return tweet


def is_configured() -> bool:
    """Check if Chrome and the profile exist."""
    return os.path.exists(CHROME_PATH) and os.path.exists(SOURCE_PROFILE)


async def post_tweet_via_chrome(tweet_text: str) -> XPostResult:
    """Post a tweet using Chrome browser automation via CDP."""
    from playwright.async_api import async_playwright

    if not is_configured():
        return XPostResult(success=False, error="Chrome or profile not found")

    # Create temp profile
    temp_dir = tempfile.mkdtemp(prefix="chrome_x_")
    temp_profile = os.path.join(temp_dir, "Profile 10")

    try:
        shutil.copytree(
            SOURCE_PROFILE,
            temp_profile,
            ignore=shutil.ignore_patterns(
                "Cache*", "Code Cache", "GPUCache", "Service Worker",
                "Storage", "IndexedDB", "blob_storage", "File System",
            ),
            dirs_exist_ok=True,
        )
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return XPostResult(success=False, error=f"Failed to copy profile: {e}")

    # Kill any existing Chrome with debugging
    subprocess.run(["pkill", "-f", "remote-debugging-port"], capture_output=True)
    await asyncio.sleep(1)

    # Launch Chrome with remote debugging
    chrome_proc = subprocess.Popen(
        [
            CHROME_PATH,
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={temp_dir}",
            "--profile-directory=Profile 10",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
            "https://x.com/home",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        await asyncio.sleep(12)

        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
            contexts = browser.contexts
            if not contexts:
                return XPostResult(success=False, error="No browser contexts")

            pages = contexts[0].pages
            page = None
            for pg in pages:
                if "x.com" in pg.url:
                    page = pg
                    break
            if not page:
                page = pages[0] if pages else await contexts[0].new_page()

            await asyncio.sleep(5)

            # Check if logged in
            compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')
            if not compose:
                await asyncio.sleep(10)
                compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')

            if not compose:
                return XPostResult(success=False, error="Not logged in to X")

            # Compose tweet
            await compose.click()
            await asyncio.sleep(2)

            editor = await page.query_selector('div[data-testid="tweetTextarea_0"]')
            if not editor:
                editor = await page.query_selector('div[contenteditable="true"][role="textbox"]')
            if not editor:
                return XPostResult(success=False, error="Could not find tweet editor")

            await editor.click()
            await asyncio.sleep(1)
            await page.keyboard.type(tweet_text, delay=30)
            await asyncio.sleep(2)

            # Post
            post_btn = await page.query_selector('button[data-testid="tweetButton"]')
            if not post_btn:
                post_btn = await page.query_selector('button[data-testid="tweetButtonInline"]')
            if not post_btn:
                return XPostResult(success=False, error="Could not find post button")

            is_disabled = await post_btn.get_attribute("disabled")
            if is_disabled is not None:
                return XPostResult(success=False, error="Post button disabled")

            await post_btn.click(force=True)
            await asyncio.sleep(4)

            # Capture URL
            tweet_url = None
            try:
                link = await page.query_selector('a[href*="/bargain4huntrs/status/"]')
                if link:
                    href = await link.get_attribute("href")
                    if href:
                        tweet_url = f"https://x.com{href}" if href.startswith("/") else href
            except Exception:
                pass

            logger.info(f"Posted tweet: {tweet_url or '(URL not captured)'}")
            return XPostResult(success=True, url=tweet_url, tweet_text=tweet_text)

    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        return XPostResult(success=False, error=str(e), tweet_text=tweet_text)

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
        shutil.rmtree(temp_dir, ignore_errors=True)


async def post_deal_to_x(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
    image_url: Optional[str] = None,
) -> dict:
    """Format a deal as a tweet and post it to X via Chrome automation."""
    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    result = await post_tweet_via_chrome(tweet_text)

    if result.success:
        return {
            "status": "success",
            "url": result.url,
            "tweet_text": result.tweet_text,
        }
    else:
        return {
            "status": "error",
            "error": result.error,
            "tweet_text": result.tweet_text,
        }
