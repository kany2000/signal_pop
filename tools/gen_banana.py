import os
import sys
import json
import base64
import httpx

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PROXY = os.environ.get("SOCKS_PROXY", "socks5://127.0.0.1:10808")

def generate_image(prompt: str, output_path: str, model: str = "models/gemini-3.1-flash-image", aspect_ratio: str = "16:9"):
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Generate an image: {prompt} --ar {aspect_ratio}"}
                ]
            }
        ]
    }
    
    print(f"[*] Calling Google {model} with prompt: {prompt[:60]}...")
    try:
        with httpx.Client(proxy=PROXY, timeout=120.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                print(f"[-] HTTP Error {resp.status_code}: {resp.text}")
                return False
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                print("[-] No candidates in response:", data)
                return False
            
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    b64_str = part["inlineData"].get("data")
                    if b64_str:
                        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(b64_str))
                        print(f"[+] SUCCESS! Nano Banana image saved to: {output_path}")
                        return True
                elif "text" in part:
                    print("[-] Model returned text instead of image:", part["text"][:200])
            return False
    except Exception as e:
        print(f"[-] Error: {e}")
        return False

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "A cute little red panda eating bamboo on a mossy green tree branch, warm golden sunlight, cinematic 8k, photorealistic, highly detailed, no text"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "E:/projects/signal_pop/generated-images/nano_banana_red_panda.png"
    generate_image(prompt, out_file)
