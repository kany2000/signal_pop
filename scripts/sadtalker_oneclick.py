#!/usr/bin/env python3
"""Signal Pop AI主播 — 一键脚本，上传到Colab运行"""
import os, sys, subprocess, shutil, site, urllib.request, urllib.parse, json, glob, time

def run(cmd, **kw):
    print(f"$ {cmd[:120]}")
    subprocess.run(cmd, shell=True, check=False, **kw)

AUDIO_FILE = "tts.wav"  # 上传到Colab的TTS音频文件名

# ===== 1. 安装系统依赖 =====
print("="*60)
print("1/6 安装系统依赖")
print("="*60)
run("apt-get -qq install ffmpeg 2>/dev/null")

# ===== 2. 克隆 SadTalker =====
print("="*60)
print("2/6 克隆 SadTalker")
print("="*60)
if os.path.exists("/content/SadTalker"):
    shutil.rmtree("/content/SadTalker")
run("git clone https://github.com/OpenTalker/SadTalker.git")
os.chdir("/content/SadTalker")

# ===== 3. 安装Python依赖 =====
print("="*60)
print("3/6 安装Python依赖")
print("="*60)
run("pip install --quiet numpy==1.23.5 opencv-python-headless imageio scipy scikit-image 2>/dev/null")
run("pip install --quiet tqdm tensorboard 2>/dev/null")
run("pip install --quiet dlib-bin 2>/dev/null")
run("pip install --quiet face-alignment 2>/dev/null")
run("pip install --quiet kornia ninja einops omegaconf yacs numexpr 2>/dev/null")
run("pip install --quiet basicsr==1.4.2 2>/dev/null")
run("pip install --quiet gfpgan==1.3.8 2>/dev/null")

# ===== 4. 修复兼容性问题 =====
print("="*60)
print("4/6 修复兼容性")
print("="*60)
# 修复 numpy
run("sed -i 's/np.VisibleDeprecationWarning/DeprecationWarning/g' src/face3d/util/preprocess.py 2>/dev/null")
# 修复 basicsr 的 functional_tensor 引用 — 直接替换源文件
run("sed -i 's/from torchvision.transforms.functional_tensor import/from torchvision.transforms.functional import/g' /usr/local/lib/python3.12/dist-packages/basicsr/data/degradations.py 2>/dev/null")

# 写入 sitecustomize.py 确保所有子进程都生效
import site as _site
try:
    _sp = _site.getsitepackages()[0]
except:
    _sp = "/usr/local/lib/python3.12/dist-packages"
with open(os.path.join(_sp, "sitecustomize.py"), "w") as f:
    f.write('''
import sys, torchvision.transforms.functional as F
from types import ModuleType
_m = ModuleType("torchvision.transforms.functional_tensor")
_m.rgb_to_grayscale = F.rgb_to_grayscale
sys.modules["torchvision.transforms.functional_tensor"] = _m
''')

# ===== 5. 下载模型 =====
print("="*60)
print("5/6 下载模型文件")
print("="*60)
os.makedirs("checkpoints", exist_ok=True)
urls = [
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.1/SadTalker_V0.0.1.pth", "checkpoints/SadTalker_V0.0.1.pth"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.1/mapping_00109-model_dict-general_wi.pth", "checkpoints/mapping_00109-model_dict-general_wi.pth"),
    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.1/mapping_00229-model_dict-general_wi.pth", "checkpoints/mapping_00229-model_dict-general_wi.pth"),
]
for url, out in urls:
    if not os.path.exists(out):
        print(f"  Downloading {os.path.basename(out)}...")
        urllib.request.urlretrieve(url, out)
        print(f"  Done ({os.path.getsize(out)//1024//1024}MB)")
    else:
        print(f"  {os.path.basename(out)} exists, skip")

# ===== 6. 生成主播照片 =====
print("="*60)
print("生成主播照片 (Pollinations)")
print("="*60)
seed = int(time.time()) % 99999
prompt = ("professional Chinese female news anchor, head and shoulders portrait, "
          "natural realistic body proportions, neutral studio background, "
          "professional broadcast look, soft lighting, no text, no distortion")
q = urllib.parse.quote(prompt)
url = f"https://image.pollinations.ai/prompt/{q}?width=768&height=768&nologo=true&seed={seed}"
print(f"  seed={seed}, downloading...")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=120) as r:
    with open("anchor.jpg", "wb") as f:
        f.write(r.read())
print(f"  anchor.jpg ({os.path.getsize('anchor.jpg')//1024}KB)")

# ===== 7. 检查音频文件 =====
print("="*60)
print("检查音频文件")
print("="*60)
if not os.path.exists(AUDIO_FILE):
    print(f"  ERROR: 请上传 {AUDIO_FILE} 到Colab当前目录")
    print("  从Colab左侧文件面板拖入即可")
    sys.exit(1)
print(f"  {AUDIO_FILE} ({os.path.getsize(AUDIO_FILE)//1024//1024}MB)")

# ===== 8. 运行推理 =====
print("="*60)
print("8/8 生成AI主播口型视频 (约5-10分钟)")
print("="*60)
os.makedirs("output", exist_ok=True)
cmd = (
    f"python inference.py "
    f"--driven_audio \"{AUDIO_FILE}\" "
    f"--source_image \"anchor.jpg\" "
    f"--result_dir \"./output\" "
    f"--preprocess crop "
    f"--still "
    f"--enhancer gfpgan"
)
run(cmd)

# ===== 9. 输出结果 =====
print("="*60)
print("生成完成！")
print("="*60)
output_videos = glob.glob("output/*.mp4")
for v in output_videos:
    size = os.path.getsize(v) / 1024 / 1024
    print(f"  {v} ({size:.1f}MB)")
    # 下载到本地
    from google.colab import files
    files.download(v)

print("Done!")