"""X (Twitter) Auto-Posting via Chrome (Silent/Headless).

Uses a dedicated Chrome profile that stays logged in to @bargain4huntrs.
The first run requires a one-time manual login (visible browser).
All subsequent runs are headless and completely silent — no browser
window appears, no screen interruption.

Profile setup:
    python -m app.services.x_browser_poster --login

This opens Chrome once for you to log in to X. After that, all
posting is done silently in the background.
"""
import asyncio
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Dedicated profile for X posting — separate from user's personal Chrome
X_PROFILE_DIR = os.path.expanduser("~/.bargainhuntrs/x_chrome_profile")
DEBUG_PORT = 9223  # Different port to avoid conflicts


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
        "overstock": "Overstock",
        "bhphoto": "B&H Photo",
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
    """Check if the dedicated X profile exists (i.e., login has been done)."""
    return os.path.exists(os.path.join(X_PROFILE_DIR, "Default", "Cookies")) or \
           os.path.exists(os.path.join(X_PROFILE_DIR, "Default", "Network", "Cookies"))


async def login_interactive() -> bool:
    """One-time login: opens Chrome visibly so you can log in to X.

    After logging in, the session is saved to the dedicated profile.
    All future posts use this profile in headless mode (no visible window).
    """
    from playwright.async_api import async_playwright

    os.makedirs(X_PROFILE_DIR, exist_ok=True)

    # Kill any Chrome using our debug port
    subprocess.run(["pkill", "-f", f"remote-debugging-port={DEBUG_PORT}"],
                   capture_output=True)
    await asyncio.sleep(1)

    # Launch Chrome with remote debugging using the dedicated profile
    chrome_proc = subprocess.Popen(
        [
            CHROME_PATH,
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={X_PROFILE_DIR}",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
            "https://x.com/login",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("Chrome opened — log in to @bargain4huntrs in the browser window.")
    print("You have 3 minutes. The session will be saved automatically.")
    print()

    try:
        async with async_playwright() as p:
            # Wait for Chrome to start
            await asyncio.sleep(8)

            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
            context = browser.contexts[0] if browser.contexts else None
            if not context:
                print("No browser context found")
                return False

            page = context.pages[0] if context.pages else await context.new_page()

            # Wait for login (up to 3 minutes)
            logged_in = False
            for i in range(36):
                await asyncio.sleep(5)
                try:
                    compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')
                    if compose:
                        logged_in = True
                        print(f"\nLogin detected after {(i+1)*5}s! Session saved.")
                        break
                    if "x.com/home" in page.url:
                        logged_in = True
                        print(f"\nLogin detected (home page) after {(i+1)*5}s! Session saved.")
                        break
                    print(f"  Waiting for login... ({(i+1)*5}s)")
                except Exception:
                    print(f"  Waiting... ({(i+1)*5}s)")

            if not logged_in:
                print("\nLogin not detected — saving profile anyway.")

            # Close browser connection (profile is auto-saved by Chrome)
            return True

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()


async def post_tweet_via_chrome(tweet_text: str, headless: bool = True) -> XPostResult:
    """Post a tweet using the dedicated X Chrome profile.

    Args:
        tweet_text: The tweet text to post.
        headless: If True, runs completely invisibly (no browser window).
                  If False, shows the browser window (for debugging).

    Returns:
        XPostResult with success status and tweet URL.
    """
    from playwright.async_api import async_playwright

    if not is_configured():
        return XPostResult(
            success=False,
            error="X profile not found. Run: python -m app.services.x_browser_poster --login",
        )

    # Kill any Chrome using our debug port
    subprocess.run(["pkill", "-f", f"remote-debugging-port={DEBUG_PORT}"],
                   capture_output=True)
    await asyncio.sleep(1)

    # Launch Chrome with remote debugging
    # In headless mode, Chrome runs without any visible window
    chrome_args = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={X_PROFILE_DIR}",
        "--no-first-run",
        "--disable-blink-features=AutomationControlled",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-popup-blocking",
    ]

    if headless:
        chrome_args.append("--headless=new")
        chrome_args.append("--window-size=1280,800")

    chrome_args.append("https://x.com/home")

    chrome_proc = subprocess.Popen(
        chrome_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for Chrome to start and load X
        await asyncio.sleep(10 if headless else 8)

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

            # Wait for X to load
            await asyncio.sleep(5)

            # Check if logged in
            compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')
            if not compose:
                await asyncio.sleep(10)
                compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')

            if not compose:
                return XPostResult(
                    success=False,
                    error="Not logged in. Run: python -m app.services.x_browser_poster --login",
                )

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
    """Format a deal as a tweet and post it to X silently (headless).

    No browser window appears. Runs completely in the background.
    """
    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    result = await post_tweet_via_chrome(tweet_text, headless=True)

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


if __name__ == "__main__":
    import sys

    if "--login" in sys.argv:
        # One-time login (visible browser)
        print("Starting one-time X login...")
        asyncio.run(login_interactive())
    elif "--test" in sys.argv:
        # Test post (headless)
        print("Posting test tweet (headless)...")
        result = asyncio.run(post_deal_to_x(
            title="Test Deal — Samsung Galaxy Buds2 Pro",
            deal_price=99.99,
            original_price=199.99,
            discount_percent=50,
            retailer="amazon",
            deal_url="https://www.amazon.com/dp/B0BPYPZ953?tag=bargain0ae-20",
            deal_tier="clearance",
        ))
        print(result)
    else:
        print("Usage:")
        print("  python -m app.services.x_browser_poster --login   # One-time login (visible)")
        print("  python -m app.services.x_browser_poster --test    # Test post (headless)")
