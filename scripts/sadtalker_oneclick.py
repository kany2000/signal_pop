#!/usr/bin/env python3
"""Signal Pop AI主播 — 一键脚本，Colab运行"""
import os, sys, subprocess, shutil, urllib.request, urllib.parse, glob, time

AUDIO_FILE = "tts.wav"
os.chdir("/content")

def run(cmd):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True)
    if r.returncode != 0:
        print(f"  ⚠️ exit code {r.returncode}")
    return r

# ===== 1. 系统依赖 =====
print("="*60 + "\n1/6 系统依赖\n" + "="*60)
run("apt-get -qq install ffmpeg 2>&1 | tail -1")

# ===== 2. 克隆 =====
print("="*60 + "\n2/6 克隆 SadTalker\n" + "="*60)
if os.path.exists("SadTalker"):
    shutil.rmtree("SadTalker")
run("git clone https://github.com/OpenTalker/SadTalker.git")
os.chdir("SadTalker")

# ===== 3. 依赖 =====
print("="*60 + "\n3/6 安装依赖\n" + "="*60)
run("pip install -q numpy==1.23.5 opencv-python-headless imageio scipy scikit-image 2>&1 | tail -1")
run("pip install -q torch torchvision --index-url https://download.pytorch.org/whl/cu118 2>&1 | tail -1")
run("pip install -q tqdm tensorboard kornia ninja einops omegaconf yacs numexpr 2>&1 | tail -1")
run("pip install -q dlib-bin face-alignment 2>&1 | tail -1")
run("pip install -q basicsr==1.4.2 gfpgan==1.3.8 2>&1 | tail -1")

# ===== 4. 修复 =====
print("="*60 + "\n4/6 修复兼容性\n" + "="*60)
run("sed -i 's/np.VisibleDeprecationWarning/DeprecationWarning/g' src/face3d/util/preprocess.py")
run("sed -i 's/from torchvision.transforms.functional_tensor import/from torchvision.transforms.functional import/g' /usr/local/lib/python3.12/dist-packages/basicsr/data/degradations.py")
import site
with open(os.path.join(site.getsitepackages()[0], "sitecustomize.py"), "w") as f:
    f.write("import sys,torchvision.transforms.functional as F;from types import ModuleType\n_m=ModuleType('torchvision.transforms.functional_tensor')\n_m.rgb_to_grayscale=F.rgb_to_grayscale\nsys.modules['torchvision.transforms.functional_tensor']=_m\n")

# ===== 5. 模型 =====
print("="*60 + "\n5/6 下载模型 (用 SadTalker 自带脚本)\n" + "="*60)
run("python scripts/download_models.py 2>&1")

# 检查
os.makedirs("checkpoints", exist_ok=True)
for f in sorted(os.listdir("checkpoints")):
    sz = os.path.getsize(f"checkpoints/{f}") / 1048576
    print(f"  {f}: {sz:.1f}MB")

# ===== 6. 主播照片 =====
print("="*60 + "\n生成主播照片\n" + "="*60)
seed = int(time.time()) % 99999
q = urllib.parse.quote("professional Chinese male news anchor, head and shoulders portrait, natural realistic body proportions, neutral studio background, professional broadcast look, soft lighting, no text, no distortion")
url = f"https://image.pollinations.ai/prompt/{q}?width=768&height=768&nologo=true&seed={seed}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=120) as r:
    with open("anchor.jpg", "wb") as f:
        f.write(r.read())
print(f"  anchor.jpg ({os.path.getsize('anchor.jpg')//1024}KB)")

# ===== 7. 音频 =====
print("="*60 + "\n检查音频\n" + "="*60)
if not os.path.exists(f"/content/{AUDIO_FILE}"):
    print(f"⚠️ 请上传 {AUDIO_FILE} 到 Colab 左侧文件面板")
    print("   上传后重新运行此脚本")
    sys.exit(1)
shutil.copy(f"/content/{AUDIO_FILE}", AUDIO_FILE)
print(f"  {AUDIO_FILE} ({os.path.getsize(AUDIO_FILE)//1048576}MB)")

# ===== 8. 推理 =====
print("="*60 + "\n6/6 生成AI主播口型视频 (~5-10分钟)\n" + "="*60)
os.makedirs("output", exist_ok=True)
run(f"python inference.py --driven_audio {AUDIO_FILE} --source_image anchor.jpg --result_dir output --preprocess crop --still --enhancer gfpgan 2>&1")

# ===== 9. 结果 =====
print("="*60 + "\n完成！\n" + "="*60)
for v in sorted(glob.glob("output/*.mp4")):
    print(f"  {v} ({os.path.getsize(v)//1048576}MB)")
    from google.colab import files
    files.download(v)