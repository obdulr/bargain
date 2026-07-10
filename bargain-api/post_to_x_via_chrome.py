"""Post to X using the user's real Chrome profile.

Launches Chrome with the user's actual profile directory (where they're
already logged in to X) and posts a tweet. Requires Chrome to be closed
first (Chrome locks its profile when running).

Usage:
    python post_to_x_via_chrome.py
"""
import asyncio
import os
from playwright.async_api import async_playwright

CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")


async def post_tweet(tweet_text: str) -> dict:
    """Post a tweet using the real Chrome profile."""
    async with async_playwright() as p:
        # Launch Chrome with the real user profile
        # channel="chrome" uses the actual Chrome binary
        context = await p.chromium.launch_persistent_context(
            CHROME_USER_DATA,
            headless=False,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--profile-directory=Profile 10",
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            no_viewport=False,
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, "webdriver", { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        print("Opening X home page...")
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
        print("Page loaded, waiting for UI...")
        await asyncio.sleep(5)

        # Check if logged in
        compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')
        if not compose:
            print("Compose button not found — waiting 15 more seconds...")
            await asyncio.sleep(15)
            compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')

        if not compose:
            # Take screenshot for debugging
            await page.screenshot(path="/tmp/x_debug.png")
            print(f"Not logged in or page didn't load. Screenshot saved to /tmp/x_debug.png")
            print(f"Current URL: {page.url}")
            await context.close()
            return {"status": "error", "error": "Not logged in to X"}

        print("Logged in! Composing tweet...")

        # Click compose button
        await compose.click()
        await asyncio.sleep(2)

        # Find the text editor
        editor = await page.query_selector('div[data-testid="tweetTextarea_0"]')
        if not editor:
            editor = await page.query_selector('div[contenteditable="true"][role="textbox"]')

        if not editor:
            await page.screenshot(path="/tmp/x_debug.png")
            print(f"Could not find tweet editor. Screenshot: /tmp/x_debug.png")
            await context.close()
            return {"status": "error", "error": "Could not find tweet editor"}

        await editor.click()
        await asyncio.sleep(1)

        # Type the tweet
        print(f"Typing tweet ({len(tweet_text)} chars)...")
        await page.keyboard.type(tweet_text, delay=30)
        await asyncio.sleep(2)

        # Click post button
        print("Posting...")
        post_btn = await page.query_selector('button[data-testid="tweetButton"]')
        if not post_btn:
            post_btn = await page.query_selector('button[data-testid="tweetButtonInline"]')

        if not post_btn:
            await page.screenshot(path="/tmp/x_debug.png")
            print(f"Could not find post button. Screenshot: /tmp/x_debug.png")
            await context.close()
            return {"status": "error", "error": "Could not find post button"}

        is_disabled = await post_btn.get_attribute("disabled")
        if is_disabled is not None:
            await page.screenshot(path="/tmp/x_debug.png")
            print(f"Post button disabled. Screenshot: /tmp/x_debug.png")
            await context.close()
            return {"status": "error", "error": "Post button disabled"}

        await post_btn.click()
        await asyncio.sleep(4)

        # Try to capture tweet URL
        tweet_url = None
        try:
            link = await page.query_selector('a[href*="/bargain4huntrs/status/"]')
            if link:
                href = await link.get_attribute("href")
                if href:
                    tweet_url = f"https://x.com{href}" if href.startswith("/") else href
        except Exception:
            pass

        await context.close()

        print(f"Posted! URL: {tweet_url or '(not captured)'}")
        return {"status": "success", "url": tweet_url, "tweet_text": tweet_text}


if __name__ == "__main__":
    tweet = "🔥 50% OFF\nSamsung Galaxy Buds2 Pro True Wireless Earbuds\n$100 (was $200) at Amazon\nSave $100\n\nhttps://www.amazon.com/dp/B0BPYPZ953?tag=bargain0ae-20\n\n#deals #clearance"
    result = asyncio.run(post_tweet(tweet))
    print(result)
