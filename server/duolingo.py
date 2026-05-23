from playwright.sync_api import sync_playwright
import time
import argparse
import os
import json

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
TARGET_LESSON_URL = "https://www.duolingo.com/lesson/unit/674/level/1"  

LESSON_READY_SELECTOR = (
    '._3yE3H, '
    '[data-test="challenge-type"], '
    '[data-test="story-start"], '
    '[data-test="stories-player-continue"], '
    '[data-test="player-next"], '
    '[data-test="player-skip"]'
)
LOGIN_SELECTOR = 'a[data-test="have-account"]'
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def locator_is_visible(page, selector):
    try:
        return page.locator(selector).first.is_visible(timeout=1000)
    except Exception:
        return False


def get_page_diagnostics(page, recent_events=None):
    try:
        title = page.title()
    except Exception:
        title = "<unavailable>"

    try:
        body_text = page.locator("body").inner_text(timeout=2000)
        body_text = " ".join(body_text.split())[:500]
    except Exception:
        body_text = "<unavailable>"

    try:
        html_length = len(page.content())
    except Exception:
        html_length = -1

    event_text = ""
    if recent_events:
        event_text = f", recent_events={recent_events[-8:]!r}"

    return f"url={page.url!r}, title={title!r}, html_length={html_length}, body={body_text!r}{event_text}"


def setup_page_debugging(page):
    recent_events = []

    def remember(event):
        recent_events.append(event)
        del recent_events[:-20]

    page.on("console", lambda msg: remember(f"console:{msg.type}:{msg.text[:300]}"))
    page.on("pageerror", lambda err: remember(f"pageerror:{str(err)[:300]}"))
    page.on("requestfailed", lambda request: remember(
        f"requestfailed:{request.resource_type}:{request.url[:180]}:{request.failure}"
    ))
    page.on("response", lambda response: remember(
        f"response:{response.status}:{response.url[:180]}"
    ) if response.request.resource_type == "document" else None)

    return recent_events


def wait_for_lesson_ready(page, timeout_ms=25000):
    deadline = time.monotonic() + timeout_ms / 1000

    while time.monotonic() < deadline:
        if locator_is_visible(page, LOGIN_SELECTOR) or page.url == "https://www.duolingo.com/":
            raise RuntimeError("login page detected while opening lesson")

        if locator_is_visible(page, LESSON_READY_SELECTOR):
            return True

        time.sleep(0.5)

    return False

# ==========================================
# 1. Standalone JS Solver Script (Embedded as a string)
# ==========================================
JS_SOLVER_SCRIPT = """
(async function initUltimateSolver() {
    // ==========================================
    // 1. Visual Logger System with Control Panel
    // ==========================================
    let loggerUI = document.getElementById('dlp-logger-ui');
    if (!loggerUI) {
        loggerUI = document.createElement('div');
        loggerUI.id = 'dlp-logger-ui';
        loggerUI.style.cssText = `
            position: fixed; bottom: 20px; left: 20px; width: 350px; height: 300px;
            background: rgba(0, 0, 0, 0.85); color: #00ff00; font-family: monospace; 
            font-size: 13px; z-index: 999999; border-radius: 10px; border: 1px solid #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; flex-direction: column;
        `;
        
        let controlPanel = document.createElement('div');
        controlPanel.style.cssText = `padding: 10px; display: flex; gap: 10px; justify-content: space-between; border-bottom: 1px solid #444;`;
        controlPanel.innerHTML = `
            <button id="dlp-start-btn" style="flex:1; padding: 8px; background: #34C759; color: #000; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">▶️ Start Auto</button>
            <button id="dlp-stop-btn" style="flex:1; padding: 8px; background: #FF3B30; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">⏹️ Stop</button>
        `;

        let logArea = document.createElement('div');
        logArea.id = 'dlp-log-area';
        logArea.style.cssText = `padding: 10px; overflow-y: auto; flex: 1; line-height: 1.5;`;

        loggerUI.appendChild(controlPanel);
        loggerUI.appendChild(logArea);
        document.body.appendChild(loggerUI);

        document.getElementById('dlp-start-btn').onclick = () => window.startAutoSolve();
        document.getElementById('dlp-stop-btn').onclick = () => window.stopAutoSolve();
    }

    function logMsg(msg, color = "#00ff00") {
        let area = document.getElementById('dlp-log-area');
        let p = document.createElement('div');
        p.style.color = color;
        p.innerHTML = `> ${msg}`;
        area.appendChild(p);
        area.scrollTop = area.scrollHeight;
    }

    logMsg("🚀 Ultimate Solver (with disabled button fix) injected!", "#00bfff");
    logMsg("👉 Enter a lesson or story, then click Start.", "#ccc");

    // ==========================================
    // 2. State and Human-like Delays
    // ==========================================
    window.isAutoMode = false;
    const randomDelay = (min, max) => new Promise(r => setTimeout(r, Math.random() * (max - min) + min));

    // Reliably check if a button is truly clickable (core fix)
    function isClickable(btn) {
        if (!btn) return false;
        if (btn.disabled === true) return false; // Intercept native disabled
        if (btn.getAttribute('aria-disabled') === 'true') return false; // Intercept aria disabled
        return true;
    }

    async function humanType(inputElement, text) {
        const nativeSetter = Object.getOwnPropertyDescriptor(
            window[inputElement.tagName === "TEXTAREA" ? "HTMLTextAreaElement" : "HTMLInputElement"].prototype, "value"
        ).set;
        let currentText = "";
        for (let i = 0; i < text.length; i++) {
            currentText += text[i];
            nativeSetter.call(inputElement, currentText);
            inputElement.dispatchEvent(new Event('input', { bubbles: true }));
            await randomDelay(15, 40); 
        }
        inputElement.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // ==========================================
    // 3. Data Extraction 
    // ==========================================
    function extractData() {
        let marker = document.querySelector('[data-test="challenge-type"]') || 
                     document.querySelector('[data-test="stories-player-continue"]') || 
                     document.querySelector('[data-test="player-next"]') || 
                     document.querySelector('._3yE3H');
                     
        if (!marker) return null;
        
        let curr = marker;
        while(curr) {
            let key = Object.keys(curr).find(k => k.startsWith("__reactFiber$"));
            if(key) {
                let fiber = curr[key];
                for (let i = 0; i < 15; i++) {
                    if (fiber?.memoizedProps?.currentChallenge) return fiber.memoizedProps.currentChallenge;
                    if (fiber?.pendingProps?.currentChallenge) return fiber.pendingProps.currentChallenge;
                    if (fiber?.return) fiber = fiber.return;
                }
            }
            curr = curr.parentElement;
        }
        return null;
    }

    function getCleanText(button) {
        let clone = button.cloneNode(true);
        clone.querySelectorAll('rt').forEach(rt => rt.remove()); 
        return clone.textContent.trim().toLowerCase();
    }

    // ==========================================
    // 4. Popup/Ad Skipper and Transition Handler
    // ==========================================
    async function handlePopupsAndEndScreens() {
        const skipSelectors = [
            '[data-test="practice-hub-ad-no-thanks-button"]', 
            '[data-test="plus-no-thanks"]', 
            '._2V6ug._1ursp._7jW2t._28UWu._3h0lA._1S2uf._1E9sc',
            '[data-test="story-start"]' 
        ];
        for (let selector of skipSelectors) {
            let btn = document.querySelector(selector);
            if (btn) {
                logMsg("🛡️ Auto-handling popup/starter screen...", "#ffaa00");
                btn.click();
                await randomDelay(300, 500);
            }
        }

        // Use isClickable() to intercept non-clickable gray buttons
        let storyContinue = document.querySelector('[data-test="stories-player-continue"]');
        if (isClickable(storyContinue)) {
            logMsg("💬 Advancing story dialogue...", "#00ffff");
            storyContinue.click();
            await randomDelay(400, 600);
            return true;
        }

        let storyDone = document.querySelector('[data-test="stories-player-done"]');
        if (isClickable(storyDone)) {
            logMsg("🎉 Story complete, clicking to finish...", "#00ffff");
            storyDone.click();
            await randomDelay(800, 1200);
            return true;
        }

        let nextBtn = document.querySelector('[data-test="player-next"]');
        if (isClickable(nextBtn)) {
            if (!extractData()) {
                logMsg("⏭️ Handling summary screen, clicking continue...", "#00ffff");
                nextBtn.click();
                await randomDelay(800, 1200);
                return true;
            }
        }
        return false;
    }

    // ==========================================
    // 5. Single Challenge Solver Engine
    // ==========================================
    function isWaitingForTransition() {
        const nextBtn = document.querySelector('[data-test="player-next"]');
        if (!nextBtn) return false;

        const nextText = nextBtn.textContent.trim().toLowerCase();
        const isContinueButton = nextText.includes('continue') || nextText.includes('继续');
        return isContinueButton && !isClickable(nextBtn);
    }

    async function solveOneQuestion() {
        const sol = extractData();
        if (!sol) return false;
        if (isWaitingForTransition()) return false;

        logMsg(`⚡ Solving challenge type: [${sol.type}]`, "#ffff00");

        try {
            // ---- 1. Skip Listening/Speaking challenges ----
            const skipBtn = document.querySelector('button[data-test="player-skip"]');
            const solTypeLower = sol.type.toLowerCase();
            if (skipBtn && (solTypeLower.includes('speak') || solTypeLower.includes('listen') || solTypeLower.includes('dictation'))) {
                skipBtn.click(); 
                await randomDelay(260, 400);
                return true; 
            }
            
            // ---- 2. Story-specific challenge types ----
            if (sol.type === 'multiple-choice' || sol.type === 'select-phrases') {
                let choices = document.querySelectorAll('[data-test="stories-choice"]');
                if (choices[sol.correctAnswerIndex]) {
                    await randomDelay(200, 400);
                    choices[sol.correctAnswerIndex].click();
                }
            }
            else if (sol.type === 'arrange') {
                let choices = document.querySelectorAll('[data-test*="challenge-tap-token"]:not(span)');
                if (sol.phraseOrder) {
                    for (let i = 0; i < sol.phraseOrder.length; i++) {
                        let target = choices[sol.phraseOrder[i]];
                        if (target) { target.click(); await randomDelay(100, 250); }
                    }
                } else if (sol.correctTokens) {
                    let buttons = Array.from(choices);
                    for (let token of sol.correctTokens) {
                        let textToMatch = typeof token === 'string' ? token : (token.text || '');
                        textToMatch = textToMatch.trim().toLowerCase();
                        let targetBtn = buttons.find(btn => getCleanText(btn) === textToMatch && isClickable(btn));
                        if (targetBtn) { targetBtn.click(); await randomDelay(100, 250); }
                    }
                }
            }
            else if (sol.type === 'point-to-phrase') {
                let choices = document.querySelectorAll('[data-test="challenge-tap-token-text"]');
                let correctIndex = -1;
                for (let i = 0; i < sol.parts.length; i++) {
                    if (sol.parts[i].selectable === true) {
                        correctIndex += 1;
                        if (sol.correctAnswerIndex === i) {
                            if (choices[correctIndex] && choices[correctIndex].parentElement) {
                                await randomDelay(200, 400);
                                choices[correctIndex].parentElement.click();
                            }
                        }
                    }
                }
            }
            else if (sol.type === 'match' && sol.dictionary) {
                let nl = document.querySelectorAll('[data-test*="challenge-tap-token"]:not(span)');
                const textToElementMap = new Map();
                for (let i = 0; i < nl.length; i++) {
                    const text = getCleanText(nl[i]);
                    textToElementMap.set(text, nl[i]);
                }
                for (const key in sol.dictionary) {
                    if (sol.dictionary.hasOwnProperty(key)) {
                        const value = sol.dictionary[key];
                        const keyPart = key.split(":")[1].toLowerCase().trim();
                        const normalizedValue = value.toLowerCase().trim();
                        const element1 = textToElementMap.get(keyPart);
                        const element2 = textToElementMap.get(normalizedValue);
                        if (isClickable(element1)) { element1.click(); await randomDelay(100, 200); }
                        if (isClickable(element2)) { element2.click(); await randomDelay(100, 200); }
                    }
                }
            }

            // ---- 3. Regular challenge types ----
            else if (sol.type === 'patternTapComplete') {
                const correctText = sol.choices[sol.correctIndex || 0];
                const wordBank = document.querySelector('[data-test="word-bank"]') || document.querySelector('.eSgkc');
                let buttons = wordBank 
                    ? Array.from(wordBank.querySelectorAll('button[data-test*="challenge-tap-token"]'))
                    : Array.from(document.querySelectorAll('button[data-test*="challenge-tap-token"]'));
                
                const targetBtn = buttons.find(btn => getCleanText(btn) === correctText && isClickable(btn));
                if (targetBtn) { await randomDelay(100, 200); targetBtn.click(); }
            }
            else if (sol.correctIndices && sol.choices) {
                const wordBank = document.querySelector('[data-test="word-bank"]');
                let buttons = wordBank 
                    ? Array.from(wordBank.querySelectorAll('[data-test*="challenge-tap-token"]'))
                    : Array.from(document.querySelectorAll('button[data-test*="challenge-tap-token"]'));

                for (let idx of sol.correctIndices) {
                    let correctWord = (sol.choices[idx].text || sol.choices[idx]).trim().toLowerCase();
                    let targetBtn = buttons.find(btn => getCleanText(btn) === correctWord && isClickable(btn));
                    if (targetBtn) { targetBtn.click(); await randomDelay(60, 160); }
                }
            } 
            else if (sol.pairs) {
                let buttons = Array.from(document.querySelectorAll('button[data-test*="challenge-tap-token"]:not(span)'));
                for (let pair of sol.pairs) {
                    let leftStr = (pair.character || pair.learningToken).trim().toLowerCase();
                    let leftBtn = buttons.find(b => getCleanText(b) === leftStr && isClickable(b));
                    if (leftBtn) { leftBtn.click(); await randomDelay(50, 100); }

                    let rightStr = (pair.transliteration || pair.fromToken).trim().toLowerCase();
                    let rightBtn = buttons.find(b => getCleanText(b) === rightStr && isClickable(b));
                    if (rightBtn) { rightBtn.click(); await randomDelay(100, 200); }
                }
            }
            else if (sol.correctSolutions && !sol.displayTokens) {
                const inputElement = document.querySelector('[data-test="challenge-text-input"]') || document.querySelector('textarea');
                if (inputElement) {
                    await humanType(inputElement, sol.correctSolutions[0]);
                    await randomDelay(100, 230); 
                }
            }
            else if (sol.displayTokens && sol.displayTokens.some(t => t.damageStart !== undefined)) {
                const inputElement = document.querySelector('input[type="text"]');
                if (inputElement) {
                    let targetToken = sol.displayTokens.find(t => t.damageStart !== undefined);
                    await humanType(inputElement, targetToken.text.slice(targetToken.damageStart));
                    await randomDelay(100, 230); 
                }
            }
            else if (sol.correctIndex !== undefined) {
                const choices = document.querySelectorAll("[data-test='challenge-choice']");
                if (choices[sol.correctIndex]) {
                    await randomDelay(130, 330);
                    choices[sol.correctIndex].click();
                }
            }

            // ====== Check and continue for regular challenges ======
            await randomDelay(150, 300); 
            let nextBtn = document.querySelector('[data-test="player-next"]');
            
            // Only click the "Check" button when it's actually enabled
            if (isClickable(nextBtn)) {
                nextBtn.click(); 
                await randomDelay(300, 600); 
                nextBtn = document.querySelector('[data-test="player-next"]'); 
                if(isClickable(nextBtn)) nextBtn.click(); 
                return true;
            }
            return false;
        } catch (err) {
            logMsg(`❌ Error: ${err.message}`, "#ff4444");
            return false;
        }
    }

    // ==========================================
    // 6. Main Auto-Solver Loop 
    // ==========================================
    window.startAutoSolve = async function() {
        if (window.isAutoMode) return;
        window.isAutoMode = true;
        logMsg("▶️ Starting auto-solver...", "#34C759");

        let attemptsWithoutProgress = 0;
        const MAX_ATTEMPTS = 50; // Guard against infinite loop

        while (window.isAutoMode) {
            attemptsWithoutProgress++;
            if (attemptsWithoutProgress > MAX_ATTEMPTS) {
                logMsg("⚠️ Max attempts reached without progress. Stopping.", "#ff4444");
                window.stopAutoSolve();
                break;
            }

            let handledPopup = await handlePopupsAndEndScreens();
            if (handledPopup) {
                attemptsWithoutProgress = 0; // Reset on progress
                continue; 
            }

            if (window.location.pathname === '/learn') {
                logMsg("🏁 Lesson/Story complete!", "#34C759");
                window.stopAutoSolve();
                break;
            }

            await randomDelay(600, 1000); 
            if (window.isAutoMode && window.location.pathname !== '/learn') {
                if (await solveOneQuestion()) {
                    attemptsWithoutProgress = 0; // Reset on successful solve
                }
            }
        }
    };

    window.stopAutoSolve = function() {
        if (!window.isAutoMode) return;
        window.isAutoMode = false;
        logMsg("⏹️ Task has been stopped.", "#FF3B30");
    };
})();
"""

# ==========================================
# 2. Python Playwright Control Logic
# ==========================================
def run_duolingo_bot(loop_count):
    
    # All paths are now relative to the script's location
    profile_dir = os.path.join(script_dir, "duolingo_profile")
    state_file = os.path.join(script_dir, "duolingo_state.json")
    jwt_file = os.path.join(script_dir, "duolingo_jwt.txt")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir, 
            headless=True,
            viewport={"width": 1280, "height": 800},
            user_agent=BROWSER_USER_AGENT,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        browser.set_default_timeout(10000)
        browser.set_default_navigation_timeout(45000)
        page = browser.pages[0]
        recent_events = setup_page_debugging(page)
        page.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"""
        )

        try:  # Use try...finally to ensure the browser closes properly
            print("🌐 Opening Duolingo home page...")
            try:
                page.goto("https://www.duolingo.com/learn", timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"⚠️ Home page load timed out: {e}")

            # [Resilience] Check for login state without waiting indefinitely
            if locator_is_visible(page, LOGIN_SELECTOR) or page.url == "https://www.duolingo.com/":
                print("❌ Login state not detected!")
                if not os.path.exists(state_file):
                    print(f"❌ Fatal Error: '{os.path.basename(state_file)}' not found! Please generate it locally and place it in the script directory.")
                    return

                print(f"📄 Found '{os.path.basename(state_file)}', attempting to inject credentials...")
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                # Inject Cookies
                if "cookies" in state:
                    browser.add_cookies(state["cookies"])
                
                # Inject LocalStorage (part of Duolingo's state is stored here)
                if "origins" in state:
                    page.evaluate(
                        """(origins) => {
                            for (const origin of origins) {
                                if (origin.origin.includes('duolingo.com')) {
                                    for (const item of origin.localStorage) {
                                        window.localStorage.setItem(item.name, item.value);
                                    }
                                }
                            }
                        }""",
                        state["origins"]
                    )
                
                print("✅ Credentials injected! Refreshing page to apply login state...")
                page.reload(wait_until="domcontentloaded")
                time.sleep(3) # Give the page some time to react
            
            if locator_is_visible(page, LOGIN_SELECTOR) or page.url == "https://www.duolingo.com/":    
                print("❌ Fatal Error: Login state still not detected after attempting to inject credentials!")
                print("💡 Please log in manually in a browser first, then run this automation script. Exiting.")
                return 
            
            print(f"✅ Login confirmed. Starting {loop_count} loop(s)...")

            print("🔑 Extracting account JWT...")
            jwt_token_value = None
            # Get all cookies from the current context
            for cookie in browser.cookies():
                if cookie.get('name') == 'jwt_token':
                    jwt_token_value = cookie.get('value')
                    break
            
            if jwt_token_value:
                try:
                    # Write the JWT to a file in the same directory
                    with open(jwt_file, "w", encoding="utf-8") as f:
                        f.write(jwt_token_value)
                    print(f"✅ JWT successfully extracted and saved to '{os.path.basename(jwt_file)}' for other scripts to use!")
                except Exception as e:
                    print(f"⚠️ Failed to save JWT to file: {e}")
            else:
                print("⚠️ Could not find 'jwt_token' in cookies. Check if Duolingo has changed its cookie naming.")

            for i in range(1, loop_count + 1):
                print(f"\n" + "="*40)
                print(f"🔄 Starting loop {i}/{loop_count}...")
                print(f"="*40)
                
                lesson_ready = False
                for attempt in range(1, 3):
                    try:
                        response = page.goto(TARGET_LESSON_URL, timeout=45000, wait_until="domcontentloaded")
                        if response:
                            print(f"🌐 Lesson document response: {response.status} {response.url}")
                        if wait_for_lesson_ready(page, timeout_ms=25000):
                            lesson_ready = True
                            print("✨ Page content rendered!")
                            break

                        print(f"⚠️ Lesson did not become ready on attempt {attempt}/2.")
                        print(f"🔎 Page state: {get_page_diagnostics(page, recent_events)}")
                    except Exception as e:
                        print(f"⚠️ Page load exception on attempt {attempt}/2: {e}")
                        print(f"🔎 Page state: {get_page_diagnostics(page, recent_events)}")

                    try:
                        page.goto("https://www.duolingo.com/learn", timeout=30000, wait_until="domcontentloaded")
                    except Exception:
                        pass
                    time.sleep(2)

                if not lesson_ready:
                    print("⚠️ Lesson page still not ready after retry; skipping this loop.")
                    continue

                print("💉 Injecting JS solver engine...")
                try:
                    page.evaluate(JS_SOLVER_SCRIPT)
                    # Trigger the async solver without making Playwright wait for it to finish.
                    page.evaluate("setTimeout(() => { if (typeof window.startAutoSolve === 'function') window.startAutoSolve(); }, 0);")
                    print("🤖 Bot started, now solving...")
                except Exception as e:
                    print(f"❌ JS execution error: {e}")
                    continue

                # [Resilience] Shorten the wait time. If a normal round takes 2 minutes, 120000ms is a good timeout.
                # [Resilience] Shorten the wait time and handle timeout gracefully.
                try:
                    print("⏳ Waiting to return to the home page...")
                    page.wait_for_url("**/learn**", timeout=90000) 
                    print(f"🎉 Loop {i} finished successfully!")
                except Exception as e:
                    print(f"⚠️ Lesson timed out or got stuck: {e}")
                    # If we time out, we should try to stop the JS solver to be safe
                    try:
                        page.evaluate("if(typeof window.stopAutoSolve === 'function') window.stopAutoSolve();")
                    except:
                        pass
                    print("🔄 Reloading to recover state...")
                    page.reload(wait_until="domcontentloaded")

                # Cooldown buffer
                time.sleep(3)

        except KeyboardInterrupt:
            print("\n🛑 Script manually interrupted by user (Ctrl+C)!")
        except Exception as e:
            print(f"\n💥 An unexpected global error occurred: {e}")
        finally:
            print("\n🧹 Cleaning up and closing browser...")
            browser.close()
            print("🏁 Script finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Duolingo auto-lesson script")
    parser.add_argument("-c", "--count", type=int, default=1, help="Number of times to run the loop (default: 1)")
    args = parser.parse_args()
    
    run_duolingo_bot(args.count)
