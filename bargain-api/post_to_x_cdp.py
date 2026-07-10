"""Post to X using a copied Chrome profile.

Copies the user's Chrome Profile 10 (Prime) to a temp directory,
then launches Chrome with remote debugging using the copied profile.
This avoids Chrome's restriction on debugging with the default profile.

Usage:
    1. Close Chrome
    2. Run: python post_to_x_cdp.py
"""
import asyncio
import os
import shutil
import subprocess
import tempfile

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")
SOURCE_PROFILE = os.path.join(CHROME_USER_DATA, "Profile 10")
DEBUG_PORT = 9222


async def post_tweet(tweet_text: str) -> dict:
    """Copy profile, launch Chrome with debugging, and post a tweet."""
    from playwright.async_api import async_playwright

    # Create a temp directory for the copied profile
    temp_dir = tempfile.mkdtemp(prefix="chrome_x_")
    temp_profile = os.path.join(temp_dir, "Profile 10")

    print("Copying Chrome profile (this may take a moment)...")
    # Copy the profile — exclude large caches to speed it up
    shutil.copytree(
        SOURCE_PROFILE,
        temp_profile,
        ignore=shutil.ignore_patterns(
            "Cache*", "Code Cache", "GPUCache", "Service Worker",
            "Storage", " IndexedDB", "blob_storage", "File System",
        ),
        dirs_exist_ok=True,
    )
    print(f"Profile copied to {temp_profile}")

    # Launch Chrome with remote debugging using the temp profile
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={temp_dir}",
        "--profile-directory=Profile 10",
        "--no-first-run",
        "--disable-blink-features=AutomationControlled",
        "https://x.com/home",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"Chrome launched (PID {chrome_proc.pid}), waiting for it to load...")
    await asyncio.sleep(12)

    try:
        async with async_playwright() as p:
            print("Connecting to Chrome via CDP...")
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")

            contexts = browser.contexts
            if not contexts:
                return {"status": "error", "error": "No browser contexts found"}

            pages = contexts[0].pages
            page = None
            for pg in pages:
                if "x.com" in pg.url:
                    page = pg
                    break
            if not page:
                page = pages[0] if pages else await contexts[0].new_page()

            print(f"Current URL: {page.url}")
            print("Waiting for X to fully load...")
            await asyncio.sleep(5)

            # Check if logged in
            compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')
            if not compose:
                print("Compose button not found — waiting 15 more seconds...")
                await asyncio.sleep(15)
                compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')

            if not compose:
                await page.screenshot(path="/tmp/x_debug.png")
                print(f"Not logged in. Screenshot: /tmp/x_debug.png, URL: {page.url}")
                return {"status": "error", "error": "Not logged in to X (cookies may be encrypted)"}

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
                return {"status": "error", "error": "Could not find post button"}

            is_disabled = await post_btn.get_attribute("disabled")
            if is_disabled is not None:
                await page.screenshot(path="/tmp/x_debug.png")
                print(f"Post button disabled. Screenshot: /tmp/x_debug.png")
                return {"status": "error", "error": "Post button disabled"}

            # Use force=True to bypass overlay interception
            await post_btn.click(force=True)
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

            print(f"Posted! URL: {tweet_url or '(not captured)'}")
            return {"status": "success", "url": tweet_url, "tweet_text": tweet_text}

    finally:
        # Close Chrome
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()

        # Clean up temp profile
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up {temp_dir}")
        except Exception:
            pass


if __name__ == "__main__":
    tweet = "🔥 50% OFF\nSamsung Galaxy Buds2 Pro True Wireless Earbuds\n$100 (was $200) at Amazon\nSave $100\n\nhttps://www.amazon.com/dp/B0BPYPZ953?tag=bargain0ae-20\n\n#deals #clearance"
    result = asyncio.run(post_tweet(tweet))
    print(result)
