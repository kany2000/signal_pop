#!/usr/bin/env python3
"""Generate scene images for Signal Pop daily news via Pollinations"""
import os, urllib.request, urllib.parse, time, sys

DATE = sys.argv[1] if len(sys.argv) > 1 else "20260629"
IMG_DIR = f"/home/kan/signal_pop/daily/images/{DATE}"
os.makedirs(IMG_DIR, exist_ok=True)

prompts = {
    1: "Aerial view of semiconductor factory clean room, modern chip fabrication plant, blue lighting, telephoto lens, flat perspective, sharp focus, industrial photography",
    2: "Apple Store minimalist glass entrance, white interior with wooden tables, product display, telephoto lens, flat perspective, architectural photography",
    3: "Beijing CBD skyline at dawn, China Zun building, modern skyscrapers, misty morning, telephoto lens 200mm, flat perspective",
    4: "Buckingham Palace exterior, London, royal architecture, formal gardens, overcast day, telephoto lens, flat perspective, architectural photography",
    5: "Gaming consoles lineup on shelf, Xbox Series X Nintendo Switch PlayStation, electronic store, telephoto lens, flat perspective, retail photography",
    6: "Digital download screen on laptop, video game store interface, keyboard mouse desk setup, blue ambient light, telephoto lens, flat perspective",
    7: "American diner restaurant interior, check bill on table, coins, warm lighting, empty booth seats, telephoto lens, flat perspective, documentary style",
    8: "Times Square New York, giant LED screens, crowded street, World Cup banners, night scene, telephoto lens, flat perspective, city photography",
    9: "Football stadium aerial view, soccer field, diverse international flags, green grass, sunny day, telephoto lens, flat perspective, sports photography",
    10: "Cargo port aerial view, shipping containers stacked, logistics hub, container ship docked, cranes, telephoto lens, flat perspective, industrial photography"
}

def gen_image(prompt, out_path, seed):
    url = f"https://image.pollinations.ai/v1/images?prompt={urllib.parse.quote(prompt)}&width=1920&height=1080&model=flux&n=1&seed={seed}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) > 5000:
        with open(out_path, "wb") as f: f.write(data)
        return len(data)
    raise ValueError(f"Image too small: {len(data)}B")

for i in sorted(prompts.keys()):
    out = os.path.join(IMG_DIR, f"{i}.jpg")
    if os.path.exists(out) and os.path.getsize(out) > 5000:
        sz = os.path.getsize(out)
        print(f"[{i}/10] SKIP {sz//1024}KB")
        continue
    
    print(f"[{i}/10] {prompts[i][:50]}...", flush=True)
    try:
        sz = gen_image(prompts[i], out, i*100+42)
        print(f"  OK {sz//1024}KB")
    except Exception as e:
        print(f"  FAIL {e}")
    
    time.sleep(5)

# anchor_bg
abg = os.path.join(IMG_DIR, "anchor_bg.jpg")
if not os.path.exists(abg) or os.path.getsize(abg) < 5000:
    print("[anchor] studio background...", flush=True)
    try:
        sz = gen_image("Professional TV news studio, minimalist futuristic set, blue white ambient lighting, glass panels, blurred depth, broadcast quality, telephoto lens, flat perspective", abg, 0)
        print(f"  OK {sz//1024}KB")
    except Exception as e:
        print(f"  FAIL {e}")

print("\nDone.")
import subprocess
r = subprocess.run(["ls","-lh",IMG_DIR], capture_output=True, text=True)
for line in r.stdout.split("\n"):
    if ".jpg" in line:
        print(line)
