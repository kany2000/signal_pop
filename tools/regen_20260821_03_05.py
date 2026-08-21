#!/usr/bin/env python3
"""重新生成 03 固态电池 / 05 谦合益邦芯片（按真实概念）"""
import os, sys
sys.path.insert(0, os.path.join("E:/projects/signal_pop", "scripts"))
from win_pipeline_images import download_image

OUT_DIR = "E:/projects/signal_pop/output/weekly/20260821/images"

PROMPTS = {
    # 固态电池：全固态电解质分层结构（正极/固态电解质/负极），无液态电解液
    3: "all-solid-state battery cell structure concept, thin layered cross-section of cathode solid electrolyte and anode stacked as clean geometric layers, futuristic energy storage technology, glowing blue energy particles between layers, minimal dark tech background, premium product visualization, no text, no words, no letters, no numbers, no people, no hands",
    # 谦合益邦 4+1：底层逻辑芯片 + 上层垂直堆叠 4 层 DRAM（高楼式 3D 集成，非水平排列）
    5: "vertical 3D chip stacking structure like a mini skyscraper, four identical DRAM layers stacked one on top of another above a wider logic base chip, 4+1 high-rise 3D IC integration concept, cross-section view showing compute and memory fused in vertical space, silicon texture with blue and gold lighting, macro photography, deep tech aesthetic, no text, no words, no letters, no numbers, no people, no hands",
}

for num, prompt in PROMPTS.items():
    fname = f"{num:02d}.jpg"
    print(f"[{fname}] 重新生成...")
    download_image(prompt, seed=num * 100 + 7, out_path=os.path.join(OUT_DIR, fname))
print("✅ 完成")
