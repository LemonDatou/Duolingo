(async function triggerBackendXP() {
    // 1. 设置你想刷的 XP 数量 (原作者服务器可能会对单次/单日数量有限制)
    const targetAmount = 1000; 
    
    console.log(`🚀 开始向代理服务器请求刷取 ${targetAmount} XP...`);

    // 2. 提取当前账号的 JWT Token
    let jwtToken = null;
    try {
        jwtToken = document.cookie.split('; ').find(row => row.startsWith('jwt_token=')).split('=')[1];
    } catch (e) {
        console.error("❌ 无法获取 jwt_token，请确保你已经登录了 Duolingo！");
        return;
    }

    // 3. 组装发给原作者服务器的数据包 (伪装成原版脚本)
    const payload = {
        type: "xp",               // 也可以改成 "gem" (宝石), "streak" (连胜) 等
        amount: targetAmount,
        version: "3.1BETA.04.3",  // 必须带上正确的版本号，否则作者服务器会拒绝(返回Outdated)
        lang: "en"
    };

    try {
        // 4. 发起 POST 请求
        const response = await fetch("https://api.duolingopro.net/request", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            console.error(`❌ 服务器请求失败，状态码: ${response.status}`);
            return;
        }

        console.log("📡 服务器已接收请求，正在处理 (监听数据流)...");

        // 5. 原作者的服务器使用了流式传输 (Stream) 来返回进度，我们需要用流的方式读取
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let buffer = '';

        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            buffer += decoder.decode(value, { stream: true });

            // 简易 JSON 分块解析
            let openBraces = 0;
            let start = 0;
            for (let i = 0; i < buffer.length; i++) {
                const ch = buffer[i];
                if (ch === '{') openBraces++;
                else if (ch === '}') {
                    openBraces--;
                    if (openBraces === 0) {
                        const jsonStr = buffer.substring(start, i + 1).trim();
                        try {
                            const data = JSON.parse(jsonStr);
                            
                            // 打印服务器返回的状态
                            if (data.status === 'completed') {
                                console.log(`✅ 刷分完成！\n🎉 提示: ${data.notification?.body || 'XP已到账'}`);
                            } else if (data.status === 'failed' || data.status === 'rejected' || data.max_amount) {
                                console.warn(`⚠️ 请求被拒绝或失败 (可能达到了服务器的限制):`, data);
                            } else if (data.percentage) {
                                console.log(`⏳ 当前进度: ${data.percentage}%`);
                            }
                            
                            // 截断已处理的 buffer
                            buffer = buffer.substring(i + 1);
                            i = -1;
                            start = 0;
                            openBraces = 0;
                        } catch (e) { /* JSON 解析不完整，继续等数据 */ }
                    }
                } else if (openBraces === 0 && buffer[i].trim() !== '') {
                    start = i;
                }
            }
        }
        
        console.log("🏁 与服务器的连接已关闭，请刷新页面查看最新的 XP！");

    } catch (error) {
        console.error("❌ 网络连接错误，可能是原作者的服务器宕机了:", error);
    }
})();