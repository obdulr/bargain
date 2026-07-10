"""Capture X session using a persistent browser profile.

Uses Playwright's persistent context so the login session is saved
to a user data directory. The user logs in once, and future runs
of the poster will reuse the same profile without needing to log
in again.

Usage:
    python capture_x_session.py

The script will:
1. Open a browser with a persistent profile
2. Navigate to x.com
3. Wait for you to log in (up to 3 minutes)
4. Keep the profile saved for future automated posting
"""
import asyncio
import os
from playwright.async_api import async_playwright

# Persistent profile directory — survives between runs
PROFILE_DIR = os.path.expanduser("~/.bargainhuntrs/x_browser_profile")
X_URL = "https://x.com"


async def capture_session():
    os.makedirs(os.path.dirname(PROFILE_DIR), exist_ok=True)

    async with async_playwright() as p:
        # Launch with persistent context — saves login session
        context = await p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(navigator, "webdriver", { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        print("Opening X...")
        print("If you see a login page, log in to @bargain4huntrs.")
        print("If you're already logged in, just wait — the script will detect it.")
        print("You have 3 minutes.")
        print()

        try:
            await page.goto(X_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Navigation warning: {e}")
            # Try anyway — page may have loaded partially

        await asyncio.sleep(5)

        # Check if already logged in
        logged_in = False
        for i in range(36):  # 36 * 5s = 180s = 3 minutes
            try:
                # Check for compose button (only visible when logged in)
                compose = await page.query_selector('a[data-testid="SideNav_NewTweet_Button"]')
                if compose:
                    logged_in = True
                    print(f"\nLogged in detected after {(i+1)*5}s!")
                    break
                # Check for the home timeline
                if "x.com/home" in page.url:
                    # Might be logged in but compose button not loaded yet
                    timeline = await page.query_selector('div[data-testid="primaryColumn"]')
                    if timeline:
                        logged_in = True
                        print(f"\nLogged in detected (home timeline) after {(i+1)*5}s!")
                        break
                # Check if we're on a login page
                login_input = await page.query_selector('input[autocomplete="username"]')
                if login_input and i == 0:
                    print("  Login page detected — please enter your credentials.")
                print(f"  Waiting... ({(i+1)*5}s elapsed)")
            except Exception:
                print(f"  Waiting... ({(i+1)*5}s elapsed)")

            await asyncio.sleep(5)

        if logged_in:
            print(f"\nSuccess! Session saved to {PROFILE_DIR}")
            print("You can now run the automated poster.")
        else:
            print("\nLogin not detected within 3 minutes.")
            print("The profile is still saved — if you logged in, it should work.")

        # Close the context to flush the profile to disk
        await context.close()


if __name__ == "__main__":
    asyncio.run(capture_session())
