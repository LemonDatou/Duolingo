from curl_cffi import requests
import json
import sys

def auto_farm_xp(jwt_token, target_amount=1000):
    print(f"🚀 开始向代理服务器请求刷取 {target_amount} XP...")

    url = "https://api.duolingopro.net/request"
    
    payload = {
        "type": "xp",               
        "amount": target_amount,    
        "version": "3.1BETA.04.3",  
        "lang": "en"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}",
        "Origin": "https://www.duolingo.com",
        "Referer": "https://www.duolingo.com/",
        "Accept": "*/*"
    }

    is_finished = False

    try:
        # 发起流式请求
        response = requests.post(
            url, 
            json=payload, 
            headers=headers, 
            impersonate="chrome120", 
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ 服务器请求失败，状态码: {response.status_code}")
            return

        print("📡 防火墙穿透成功！服务器正在处理...")

        buffer = ""
        open_braces = 0
        
        # 【核心修复】：去掉不支持的参数，按原始字节块读取
        for chunk_bytes in response.iter_content():
            if not chunk_bytes: 
                continue
            
            # 手动将字节解码为字符串，忽略无法解析的杂质
            chunk_str = chunk_bytes.decode('utf-8', errors='ignore')
            
            # 逐字处理，寻找 JSON 的大括号
            for ch in chunk_str:
                buffer += ch
                
                if ch == '{':
                    if open_braces == 0: 
                        buffer = '{'  # 过滤掉开头可能存在的多余字符
                    open_braces += 1
                elif ch == '}':
                    open_braces -= 1
                    
                    # 括号完全闭合，说明截获了一个完整的 JSON
                    if open_braces == 0:
                        try:
                            data = json.loads(buffer)
                            status = data.get("status")
                            
                            if status == "completed":
                                msg = data.get("notification", {}).get("body", "XP 已到账")
                                print(f"\n✅ 刷分完成！🎉 提示: {msg}")
                                is_finished = True
                                break
                            elif status in ["failed", "rejected"] or "max_amount" in data:
                                print(f"\n⚠️ 请求被拒绝: {data}")
                                is_finished = True
                                break
                            elif "percentage" in data:
                                sys.stdout.write(f"\r⏳ 当前进度: {data['percentage']}%")
                                sys.stdout.flush()
                                
                        except json.JSONDecodeError:
                            pass # JSON不完整，直接忽略
                        
                        buffer = "" # 清空缓冲区
            
            # 如果已经完成，提前跳出外层网络读取循环
            if is_finished:
                break
                    
        print("\n🏁 任务圆满结束。")

    except Exception as e:
        if not is_finished:
            error_msg = repr(e) if repr(e) else "连接被服务器强制重置"
            print(f"\n❌ 网络异常中断: {error_msg}")

if __name__ == "__main__":
    # 替换为你刚才从浏览器控制台 (document.cookie) 提取到的长字符串
    MY_JWT_TOKEN = "" 
    # check_token(MY_JWT_TOKEN)
    auto_farm_xp(MY_JWT_TOKEN, target_amount=100)