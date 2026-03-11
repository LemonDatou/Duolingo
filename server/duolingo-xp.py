from curl_cffi import requests
import json
import sys
import argparse
import os

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

def auto_farm_xp(jwt_token, target_amount=1000):
    print(f"🚀 Requesting {target_amount} XP from proxy server...")

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
        # Make a streaming request
        response = requests.post(
            url, 
            json=payload, 
            headers=headers, 
            impersonate="chrome120", 
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Server request failed with status code: {response.status_code}")
            return

        print("📡 Firewall pierced! Server is processing...")

        buffer = ""
        open_braces = 0
        
        # Read the raw byte chunks
        for chunk_bytes in response.iter_content():
            if not chunk_bytes: 
                continue
            
            # Manually decode bytes to string, ignoring errors
            chunk_str = chunk_bytes.decode('utf-8', errors='ignore')
            
            # Process char by char to find JSON objects
            for ch in chunk_str:
                buffer += ch
                
                if ch == '{':
                    if open_braces == 0: 
                        buffer = '{'  # Filter out potential leading garbage
                    open_braces += 1
                elif ch == '}':
                    open_braces -= 1
                    
                    # If braces are balanced, we have a complete JSON object
                    if open_braces == 0:
                        try:
                            data = json.loads(buffer)
                            status = data.get("status")
                            
                            if status == "completed":
                                msg = data.get("notification", {}).get("body", "XP granted")
                                print(f"\n✅ XP farming complete! 🎉 Notification: {msg}")
                                is_finished = True
                                break
                            elif status in ["failed", "rejected"] or "max_amount" in data:
                                print(f"\n⚠️ Request rejected: {data}")
                                is_finished = True
                                break
                            elif "percentage" in data:
                                sys.stdout.write(f"\r⏳ Current progress: {data['percentage']}%")
                                sys.stdout.flush()
                                
                        except json.JSONDecodeError:
                            pass # Incomplete JSON, ignore
                        
                        buffer = "" # Clear buffer
            
            # If finished, break out of the outer loop
            if is_finished:
                break
                    
        print("\n🏁 Task finished successfully.")

    except Exception as e:
        if not is_finished:
            error_msg = repr(e) if repr(e) else "Connection was forcibly closed by the server"
            print(f"\n❌ Network error occurred: {error_msg}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Duolingo XP Farmer")
    parser.add_argument("-t", "--target", type=int, default=2000, help="Target XP")
    args = parser.parse_args()
    
    # Read JWT safely from a file in the same directory
    jwt_file_path = os.path.join(script_dir, "duolingo_jwt.txt")
    
    try:
        with open(jwt_file_path, "r", encoding="utf-8") as f:
            # Use strip() to remove potential newlines or spaces
            MY_JWT_TOKEN = f.read().strip()
            
        if not MY_JWT_TOKEN:
            print(f"❌ Fatal Error: {jwt_file_path} is empty! Please check if the previous script extracted it successfully.")
            sys.exit(1)
            
        print(f"🔑 Successfully loaded JWT from file (length: {len(MY_JWT_TOKEN)})")
        
    except FileNotFoundError:
        print(f"❌ Fatal Error: JWT file not found at '{jwt_file_path}'!")
        print("💡 Please run the Playwright lesson script first to generate this file.")
        sys.exit(1)

    # Start the XP farming task
    auto_farm_xp(MY_JWT_TOKEN, target_amount=args.target)