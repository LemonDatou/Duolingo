(function displayAnswerOnScreen() {
    // 1. Find React node
    let typeMarker = document.querySelector('[data-test="challenge-type"]');
    let curr = typeMarker ? typeMarker : document.querySelector('._3yE3H');
    
    if (!curr) {
        alert("Could not find challenge node. Please make sure you are in a lesson.");
        return;
    }

    while(curr && !Object.keys(curr).some(k => k.startsWith("__reactFiber$"))) {
        curr = curr.parentElement;
    }
    
    let key = Object.keys(curr).find(k => k.startsWith("__reactFiber$"));
    if(!key) {
        alert("Could not find React fiber node.");
        return;
    }
    
    let fiber = curr[key];
    let sol = null;

    // Traverse up 5 levels to find currentChallenge
    for (let i = 0; i < 5; i++) {
        if (fiber?.memoizedProps?.currentChallenge) { sol = fiber.memoizedProps.currentChallenge; break; }
        if (fiber?.pendingProps?.currentChallenge) { sol = fiber.pendingProps.currentChallenge; break; }
        if (fiber?.return) fiber = fiber.return;
    }

    if (sol) {
        let answerText = "";
        
        // --- Core Answer Parsing Module ---
        
        // 1. Translation / Fill in the blank (Translate / Form)
        if (sol.correctSolutions && sol.correctSolutions.length > 0) {
            answerText = sol.correctSolutions.join("<br><span style='font-size:16px;opacity:0.8'>or</span><br>");
        } 
        // 2. Word selection (tapComplete, etc., find words in choices via correctIndices)
        else if (sol.correctIndices && sol.choices) {
            let ansArray = sol.correctIndices.map(idx => {
                let choice = sol.choices[idx];
                return choice.text || choice.phrase || choice.val || choice;
            });
            answerText = ansArray.join(" "); // Join to form a complete sentence
        }
        // 3. Another word selection type (given correctTokens directly)
        else if (sol.correctTokens && sol.correctTokens.length > 0) {
            answerText = sol.correctTokens.join(" ");
        } 
        // 4. Multiple Choice
        else if (sol.correctIndex !== undefined && sol.choices) {
            let choice = sol.choices[sol.correctIndex];
            answerText = choice.text || choice.phrase || ("Option " + (sol.correctIndex + 1));
        } 
        // 5. Matching question (Match)
        else if (sol.pairs) {
            answerText = sol.pairs.map(p => `${p.character || p.learningToken}  ➡️  ${p.transliteration || p.fromToken}`).join("<br>");
        }
        // 6. Fill in the missing letters (Type Cloze)
        else if (sol.displayTokens) {
            let blanks = sol.displayTokens.filter(t => t.isBlank || t.damageStart !== undefined);
            if (blanks.length > 0) {
                answerText = blanks.map(t => t.text).join(" | ");
            }
        }

        // 7. Fallback strategy: If no match above, force extract key fields and display as text
        if (!answerText) {
            let rawData = {
                choices: sol.choices?.map(c => c.text || c),
                answer: sol.correctSolutions || sol.correctTokens || sol.correctIndex || sol.correctIndices
            };
            answerText = "<span style='font-size:16px; color:#ffeb3b;'>Parsing failed, showing raw data:</span><br><div style='font-size:14px; text-align:left; background:rgba(0,0,0,0.3); padding:10px; margin-top:10px; border-radius:8px; word-break:break-all;'>" + 
                         JSON.stringify(rawData).substring(0, 300) + "</div>";
        }

        // --- UI Display Module ---
        
        // Remove old banner (if clicked multiple times)
        let oldBanner = document.getElementById('dlp-answer-banner');
        if (oldBanner) oldBanner.remove();

        // Inject a new banner in the center of the screen
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
        // Display challenge type and the extracted answer
        banner.innerHTML = `🕵️‍♂️ <strong>Answer Intercepted (Type: ${sol.type})</strong><hr style="border-color:rgba(255,255,255,0.4); margin: 15px 0;">${answerText}`;
        document.body.appendChild(banner);
        
        // Click to dismiss, or auto-dismiss after 8 seconds
        banner.onclick = () => banner.remove();
        setTimeout(() => { if(document.body.contains(banner)) banner.remove(); }, 8000);
        
    } else {
        alert("Failed to extract currentChallenge data.");
    }
})();