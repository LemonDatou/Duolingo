from playwright.sync_api import sync_playwright
import argparse
import os
import time


script_dir = os.path.dirname(os.path.abspath(__file__))

DEFAULT_STATE_FILE = os.path.join(script_dir, "duolingo_state.json")
DEFAULT_PROFILE_DIR = os.path.join(script_dir, "duolingo_login_profile")
LOGIN_SELECTOR = 'a[data-test="have-account"]'
HOME_URL = "https://www.duolingo.com/learn"
AUTH_PATH_PARTS = ("/log-in", "/register", "/welcome")


def get_duolingo_cookie_names(page):
    try:
        cookies = page.context.cookies()
        return sorted(
            cookie.get("name", "")
            for cookie in cookies
            if "duolingo.com" in cookie.get("domain", "")
        )
    except Exception:
        return []


def has_duolingo_local_storage(page):
    try:
        return page.evaluate(
            """() => Object.keys(window.localStorage)
                .some((key) => key.toLowerCase().includes('duolingo')
                    || key.toLowerCase().includes('jwt')
                    || key.toLowerCase().includes('user'))"""
        )
    except Exception:
        return False


def has_jwt_cookie(page):
    return "jwt_token" in get_duolingo_cookie_names(page)


def is_logged_in(page):
    try:
        normalized_url = page.url.rstrip("/")
        if normalized_url in ("https://www.duolingo.com", "https://www.duolingo.com/"):
            return False
        if any(part in page.url for part in AUTH_PATH_PARTS):
            return False
        if page.locator(LOGIN_SELECTOR).first.is_visible(timeout=1000):
            return False

        cookie_names = get_duolingo_cookie_names(page)
        if "jwt_token" in cookie_names:
            return True

        if page.url.startswith("https://www.duolingo.com/learn"):
            return True

        return has_duolingo_local_storage(page)
    except Exception:
        return False


def wait_for_login(page, timeout_seconds):
    deadline = time.monotonic() + timeout_seconds
    last_status_at = 0

    while time.monotonic() < deadline:
        if is_logged_in(page):
            return True

        now = time.monotonic()
        if now - last_status_at >= 10:
            cookie_names = get_duolingo_cookie_names(page)
            print(f"   still waiting: url={page.url}, cookies={cookie_names[:10]}")
            last_status_at = now
        time.sleep(1)

    return False


def generate_duolingo_state(state_file, profile_dir, timeout_seconds):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            timezone_id="Asia/Shanghai",
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            print("🌐 Opening Duolingo login page...")
            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)

            if not is_logged_in(page):
                print("🔐 Please log in manually in the opened browser window.")
                print(f"⏳ Waiting up to {timeout_seconds} seconds for login to complete...")
                if not wait_for_login(page, timeout_seconds):
                    print("❌ Timed out waiting for login. State file was not written.")
                    return False

            page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
            if not has_jwt_cookie(page):
                print("❌ Login page changed, but jwt_token cookie was not found. State file was not written.")
                print(f"🔎 Current URL: {page.url}")
                print(f"🔎 Duolingo cookies: {get_duolingo_cookie_names(page)}")
                return False

            page.context.storage_state(path=state_file)
            print(f"✅ Login state saved to: {state_file}")
            return True
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Duolingo Playwright storage state")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_STATE_FILE,
        help=f"Output state file path (default: {DEFAULT_STATE_FILE})",
    )
    parser.add_argument(
        "-p",
        "--profile-dir",
        default=DEFAULT_PROFILE_DIR,
        help=f"Temporary persistent login profile directory (default: {DEFAULT_PROFILE_DIR})",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=300,
        help="Seconds to wait for manual login (default: 300)",
    )
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    profile_path = os.path.abspath(args.profile_dir)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(profile_path, exist_ok=True)

    success = generate_duolingo_state(output_path, profile_path, args.timeout)
    raise SystemExit(0 if success else 1)
