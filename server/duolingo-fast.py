from playwright.async_api import async_playwright
from urllib.parse import urlparse
import argparse
import asyncio
import json
import os

from duolingo import (
    BROWSER_USER_AGENT,
    JS_SOLVER_SCRIPT,
    LESSON_READY_SELECTOR,
    LOGIN_SELECTOR,
    TARGET_LESSON_URL,
)


script_dir = os.path.dirname(os.path.abspath(__file__))

DEFAULT_TARGET_LESSON_URL = TARGET_LESSON_URL
DEFAULT_STATE_FILE = os.path.join(script_dir, "duolingo_state.json")
DEFAULT_JWT_FILE = os.path.join(script_dir, "duolingo_jwt.txt")
HOME_URL = "https://www.duolingo.com/learn"
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
BLOCKED_HOST_PARTS = (
    "googletagmanager.com",
    "google-analytics.com",
    "doubleclick.net",
    "facebook.net",
    "zombie.duolingo.com",
)


def is_completion_url(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return parsed.netloc == "www.duolingo.com" and path in ("/learn", "/practice-hub")


def load_state(state_file):
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def write_jwt_from_state(state, jwt_file):
    for cookie in state.get("cookies", []):
        if cookie.get("name") == "jwt_token":
            with open(jwt_file, "w", encoding="utf-8") as f:
                f.write(cookie.get("value", ""))
            return True
    return False


async def locator_is_visible(page, selector, timeout=1000):
    try:
        return await page.locator(selector).first.is_visible(timeout=timeout)
    except Exception:
        return False


async def get_page_diagnostics(page):
    try:
        title = await page.title()
    except Exception:
        title = "<unavailable>"

    try:
        body_text = await page.locator("body").inner_text(timeout=2000)
        body_text = " ".join(body_text.split())[:500]
    except Exception:
        body_text = "<unavailable>"

    try:
        html_length = len(await page.content())
    except Exception:
        html_length = -1

    return f"url={page.url!r}, title={title!r}, html_length={html_length}, body={body_text!r}"


async def wait_for_lesson_ready(page, timeout_ms):
    deadline = asyncio.get_running_loop().time() + timeout_ms / 1000

    while asyncio.get_running_loop().time() < deadline:
        if await locator_is_visible(page, LOGIN_SELECTOR) or page.url == "https://www.duolingo.com/":
            raise RuntimeError("login page detected while opening lesson")

        if is_completion_url(page.url):
            return False

        if await locator_is_visible(page, LESSON_READY_SELECTOR):
            return True

        await asyncio.sleep(0.5)

    return False


async def block_low_value_resources(route):
    request = route.request
    host = urlparse(request.url).netloc
    if request.resource_type in BLOCKED_RESOURCE_TYPES:
        await route.abort()
        return
    if any(part in host for part in BLOCKED_HOST_PARTS):
        await route.abort()
        return
    await route.continue_()


async def create_context(browser, state_file, block_assets):
    context = await browser.new_context(
        storage_state=state_file,
        viewport={"width": 1280, "height": 800},
        user_agent=BROWSER_USER_AGENT,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    context.set_default_timeout(10000)
    context.set_default_navigation_timeout(45000)
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    if block_assets:
        await context.route("**/*", block_low_value_resources)
    return context


async def ensure_login(page, worker_id):
    await page.goto(HOME_URL, timeout=60000, wait_until="domcontentloaded")
    if await locator_is_visible(page, LOGIN_SELECTOR) or page.url == "https://www.duolingo.com/":
        diagnostics = await get_page_diagnostics(page)
        raise RuntimeError(f"[W{worker_id:02d}] login state not detected: {diagnostics}")


async def run_one_loop(page, loop_id, worker_id, target_url, lesson_timeout_ms):
    prefix = f"[W{worker_id:02d} L{loop_id:03d}]"
    print(f"{prefix} opening lesson...")

    for attempt in range(1, 3):
        response = await page.goto(target_url, timeout=45000, wait_until="domcontentloaded")
        if response:
            print(f"{prefix} document response: {response.status} {response.url}")

        if is_completion_url(page.url):
            print(f"{prefix} already at completion page: {page.url}")
            return True

        if await wait_for_lesson_ready(page, timeout_ms=25000):
            print(f"{prefix} lesson ready; injecting solver")
            await page.evaluate(JS_SOLVER_SCRIPT)
            await page.evaluate(
                "setTimeout(() => { if (typeof window.startAutoSolve === 'function') window.startAutoSolve(); }, 0);"
            )
            try:
                await page.wait_for_url(is_completion_url, timeout=lesson_timeout_ms)
                print(f"{prefix} finished: {page.url}")
                return True
            except Exception as exc:
                print(f"{prefix} timed out or stuck: {exc}")
                try:
                    await page.evaluate("if(typeof window.stopAutoSolve === 'function') window.stopAutoSolve();")
                except Exception:
                    pass
                await page.goto(HOME_URL, timeout=30000, wait_until="domcontentloaded")
                return False

        if is_completion_url(page.url):
            print(f"{prefix} reached completion page: {page.url}")
            return True

        diagnostics = await get_page_diagnostics(page)
        print(f"{prefix} not ready on attempt {attempt}/2: {diagnostics}")
        await page.goto(HOME_URL, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

    print(f"{prefix} skipped; lesson did not become ready")
    return False


async def worker(worker_id, queue, context, args):
    page = await context.new_page()

    try:
        if args.verify_login:
            print(f"[W{worker_id:02d}] verifying login state...")
            await ensure_login(page, worker_id)

        while True:
            try:
                loop_id = queue.get_nowait()
            except asyncio.QueueEmpty:
                return

            try:
                await run_one_loop(
                    page,
                    loop_id,
                    worker_id,
                    args.target_url,
                    args.lesson_timeout * 1000,
                )
            except Exception as exc:
                print(f"[W{worker_id:02d} L{loop_id:03d}] failed: {exc}")
            finally:
                queue.task_done()
    finally:
        await page.close()


async def run_fast(args):
    if not os.path.exists(args.state_file):
        raise FileNotFoundError(f"state file not found: {args.state_file}")

    state = load_state(args.state_file)
    if write_jwt_from_state(state, args.jwt_file):
        print(f"✅ JWT extracted from state and saved to '{os.path.basename(args.jwt_file)}'")
    else:
        print("⚠️ jwt_token not found in state file")

    queue = asyncio.Queue()
    for loop_id in range(1, args.count + 1):
        queue.put_nowait(loop_id)

    async with async_playwright() as p:
        print(f"🚀 Starting {args.workers} tab(s) in one shared browser context...")
        browser = await p.chromium.launch(
            headless=not args.headed,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
            ],
        )
        try:
            context = await create_context(browser, args.state_file, args.block_assets)
            workers = [
                asyncio.create_task(worker(worker_id, queue, context, args))
                for worker_id in range(1, args.workers + 1)
            ]
            try:
                await asyncio.gather(*workers)
            finally:
                await context.close()
        finally:
            await browser.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Fast concurrent Duolingo auto-lesson script")
    parser.add_argument("-c", "--count", type=int, default=1, help="Total loop count")
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=3,
        help="Concurrent tabs in one shared browser context; use 10 only if the server has enough CPU/RAM",
    )
    parser.add_argument(
        "--target-url",
        default=DEFAULT_TARGET_LESSON_URL,
        help=f"Lesson URL to run (default: {DEFAULT_TARGET_LESSON_URL})",
    )
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE_FILE,
        help=f"Playwright storage state file (default: {DEFAULT_STATE_FILE})",
    )
    parser.add_argument(
        "--jwt-file",
        default=DEFAULT_JWT_FILE,
        help=f"JWT output file (default: {DEFAULT_JWT_FILE})",
    )
    parser.add_argument(
        "--lesson-timeout",
        type=int,
        default=90,
        help="Seconds to wait for each lesson to finish",
    )
    parser.add_argument(
        "--no-block-assets",
        action="store_false",
        dest="block_assets",
        help="Do not block image/media/font/analytics requests",
    )
    parser.add_argument(
        "--verify-login",
        action="store_true",
        help="Open /learn once per worker before starting loops to verify login state",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show the Chromium window so concurrent tabs are visible",
    )
    parser.set_defaults(block_assets=True)
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be >= 1")
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.workers > 10:
        parser.error("--workers must be <= 10")

    args.state_file = os.path.abspath(args.state_file)
    args.jwt_file = os.path.abspath(args.jwt_file)
    args.workers = min(args.workers, args.count)
    return args


if __name__ == "__main__":
    asyncio.run(run_fast(parse_args()))
