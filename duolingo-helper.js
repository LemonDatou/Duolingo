(async function initUltimateSolver() {
    // ==========================================
    // 1. 带控制面板的可视化日志系统
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
            <button id="dlp-start-btn" style="flex:1; padding: 8px; background: #34C759; color: #000; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">▶️ 开启全自动</button>
            <button id="dlp-stop-btn" style="flex:1; padding: 8px; background: #FF3B30; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">⏹️ 停止</button>
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

    logMsg("🚀 终极挂机 (修复灰按钮误判) 已注入！", "#00bfff");
    logMsg("👉 进入练习或故事后，点击开始即可", "#ccc");

    // ==========================================
    // 2. 状态与拟人化延迟
    // ==========================================
    window.isAutoMode = false;
    const randomDelay = (min, max) => new Promise(r => setTimeout(r, Math.random() * (max - min) + min));

    // 严密判断按钮是否真的可以点击 (核心修复点)
    function isClickable(btn) {
        if (!btn) return false;
        if (btn.disabled === true) return false; // 拦截原生 disabled
        if (btn.getAttribute('aria-disabled') === 'true') return false; // 拦截 aria disabled
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
    // 3. 数据提取 
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
    // 4. 拦截广告与独立过场推进
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
                logMsg("🛡️ 自动处理弹窗/开局...", "#ffaa00");
                btn.click();
                await randomDelay(300, 500);
            }
        }

        // 使用 isClickable() 拦截不可点击的灰按钮
        let storyContinue = document.querySelector('[data-test="stories-player-continue"]');
        if (isClickable(storyContinue)) {
            logMsg("💬 故事对话推进...", "#00ffff");
            storyContinue.click();
            await randomDelay(400, 600);
            return true;
        }

        let storyDone = document.querySelector('[data-test="stories-player-done"]');
        if (isClickable(storyDone)) {
            logMsg("🎉 故事完成，点击结束...", "#00ffff");
            storyDone.click();
            await randomDelay(800, 1200);
            return true;
        }

        let nextBtn = document.querySelector('[data-test="player-next"]');
        if (isClickable(nextBtn)) {
            if (!extractData()) {
                logMsg("⏭️ 结算过场，点击继续...", "#00ffff");
                nextBtn.click();
                await randomDelay(800, 1200);
                return true;
            }
        }
        return false;
    }

    // ==========================================
    // 5. 单题解决引擎
    // ==========================================
    async function solveOneQuestion() {
        const sol = extractData();
        if (!sol) return false;

        logMsg(`⚡ 破解题型: [${sol.type}]`, "#ffff00");

        try {
            // ---- 1. 听力/口语题跳过 ----
            const skipBtn = document.querySelector('button[data-test="player-skip"]');
            const solTypeLower = sol.type.toLowerCase();
            if (skipBtn && (solTypeLower.includes('speak') || solTypeLower.includes('listen') || solTypeLower.includes('dictation'))) {
                skipBtn.click(); 
                await randomDelay(260, 400);
                return true; 
            }
            
            // ---- 2. 故事模式专属题型 ----
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

            // ---- 3. 常规练习题型 ----
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

            // ====== 常规题的点击检查与继续 ======
            await randomDelay(150, 300); 
            let nextBtn = document.querySelector('[data-test="player-next"]');
            
            // 只有当“检查”按钮真正亮起时才点
            if (isClickable(nextBtn)) {
                nextBtn.click(); 
                await randomDelay(300, 600); 
                nextBtn = document.querySelector('[data-test="player-next"]'); 
                if(isClickable(nextBtn)) nextBtn.click(); 
                return true;
            }
            return false;
        } catch (err) {
            logMsg(`❌ 报错: ${err.message}`, "#ff4444");
            return false;
        }
    }

    // ==========================================
    // 6. 全自动挂机主循环 
    // ==========================================
    window.startAutoSolve = async function() {
        if (window.isAutoMode) return;
        window.isAutoMode = true;
        logMsg("▶️ 开始极速答题...", "#34C759");

        while (window.isAutoMode) {
            let handledPopup = await handlePopupsAndEndScreens();
            if (handledPopup) continue; 

            if (window.location.pathname === '/learn') {
                logMsg("🏁 本单元/故事已完成，已回到主页！", "#34C759");
                window.stopAutoSolve();
                break;
            }

            await randomDelay(600, 1000); 
            if (window.isAutoMode && window.location.pathname !== '/learn') {
                await solveOneQuestion();
            }
        }
    };

    window.stopAutoSolve = function() {
        if (!window.isAutoMode) return;
        window.isAutoMode = false;
        logMsg("⏹️ 任务已终止。", "#FF3B30");
    };

})();