(function displayAnswerOnScreen() {
    // 1. 寻找 React 节点
    let typeMarker = document.querySelector('[data-test="challenge-type"]');
    let curr = typeMarker ? typeMarker : document.querySelector('._3yE3H');
    
    if (!curr) {
        alert("找不到题目节点，请确保在答题界面中！");
        return;
    }

    while(curr && !Object.keys(curr).some(k => k.startsWith("__reactFiber$"))) {
        curr = curr.parentElement;
    }
    
    let key = Object.keys(curr).find(k => k.startsWith("__reactFiber$"));
    if(!key) {
        alert("未找到 React 挂载点");
        return;
    }
    
    let fiber = curr[key];
    let sol = null;

    // 向上追溯 5 层寻找 currentChallenge
    for (let i = 0; i < 5; i++) {
        if (fiber?.memoizedProps?.currentChallenge) { sol = fiber.memoizedProps.currentChallenge; break; }
        if (fiber?.pendingProps?.currentChallenge) { sol = fiber.pendingProps.currentChallenge; break; }
        if (fiber?.return) fiber = fiber.return;
    }

    if (sol) {
        let answerText = "";
        
        // --- 核心解题解析模块 ---
        
        // 1. 翻译/整句填空 (Translate / Form)
        if (sol.correctSolutions && sol.correctSolutions.length > 0) {
            answerText = sol.correctSolutions.join("<br><span style='font-size:16px;opacity:0.8'>或</span><br>");
        } 
        // 2. 选词填空 (tapComplete 等，通过 correctIndices 数组去 choices 里找词)
        else if (sol.correctIndices && sol.choices) {
            let ansArray = sol.correctIndices.map(idx => {
                let choice = sol.choices[idx];
                return choice.text || choice.phrase || choice.val || choice;
            });
            answerText = ansArray.join(" "); // 拼成完整句子
        }
        // 3. 另一种选词填空 (直接给出 correctTokens)
        else if (sol.correctTokens && sol.correctTokens.length > 0) {
            answerText = sol.correctTokens.join(" ");
        } 
        // 4. 单选题 (Multiple Choice)
        else if (sol.correctIndex !== undefined && sol.choices) {
            let choice = sol.choices[sol.correctIndex];
            answerText = choice.text || choice.phrase || ("第 " + (sol.correctIndex + 1) + " 个选项");
        } 
        // 5. 连线匹配题 (Match)
        else if (sol.pairs) {
            answerText = sol.pairs.map(p => `${p.character || p.learningToken}  ➡️  ${p.transliteration || p.fromToken}`).join("<br>");
        }
        // 6. 单词局部残缺填空 (Type Cloze)
        else if (sol.displayTokens) {
            let blanks = sol.displayTokens.filter(t => t.isBlank || t.damageStart !== undefined);
            if (blanks.length > 0) {
                answerText = blanks.map(t => t.text).join(" | ");
            }
        }

        // 7. 兜底策略：如果上面全都没匹配上，强制提取关键字段转成文本显示在屏幕上
        if (!answerText) {
            let rawData = {
                choices: sol.choices?.map(c => c.text || c),
                answer: sol.correctSolutions || sol.correctTokens || sol.correctIndex || sol.correctIndices
            };
            answerText = "<span style='font-size:16px; color:#ffeb3b;'>解析格式不匹配，原生数据如下：</span><br><div style='font-size:14px; text-align:left; background:rgba(0,0,0,0.3); padding:10px; margin-top:10px; border-radius:8px; word-break:break-all;'>" + 
                         JSON.stringify(rawData).substring(0, 300) + "</div>";
        }

        // --- UI 显示模块 ---
        
        // 移除旧的横幅（如果连点多次）
        let oldBanner = document.getElementById('dlp-answer-banner');
        if (oldBanner) oldBanner.remove();

        // 注入新的横幅到屏幕中央
        let banner = document.createElement('div');
        banner.id = 'dlp-answer-banner';
        banner.style.cssText = `
            position: fixed; 
            top: 15%; 
            left: 50%; 
            transform: translateX(-50%); 
            background: #1cb0f6; 
            color: white; 
            padding: 25px 40px; 
            font-size: 28px; 
            font-weight: bold;
            font-family: sans-serif;
            z-index: 999999; 
            border-radius: 16px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            text-align: center;
            line-height: 1.5;
            min-width: 350px;
            border: 4px solid #1899d6;
        `;
        // 显示题型和提取到的答案
        banner.innerHTML = `🕵️‍♂️ <strong>拦截成功 (题型: ${sol.type})</strong><hr style="border-color:rgba(255,255,255,0.4); margin: 15px 0;">${answerText}`;
        document.body.appendChild(banner);
        
        // 点击消失，或者 8 秒后自动消失
        banner.onclick = () => banner.remove();
        setTimeout(() => { if(document.body.contains(banner)) banner.remove(); }, 8000);
        
    } else {
        alert("未能提取到 currentChallenge 数据。");
    }
})();