# VoxCPM 本地部署说明（Signal Pop 离线灾备 TTS）

> 调研与落地记录：2026-10-22
> 上游项目：https://github.com/OpenBMB/VoxCPM（Apache-2.0，权重与代码均可商用）
> 技术报告：arXiv 2606.06928（VoxCPM2） / 2509.24650（VoxCPM）

---

## 一、结论速览

| 路线 | 状态 | 说明 |
|---|---|---|
| **VoxCPM1.5 + PyTorch CPU** | ✅ **已跑通并接入管线** | 0.6B / 44.1kHz / 权重 1.95GB，本机可用 |
| VoxCPM2 + PyTorch CPU | ⚠️ 需扩容页面文件后重启 | 2B / 48kHz / 权重 4.96GB，本机内存吃紧 |
| llama.cpp-omni（GGUF Q8_0） | 🔲 未验证 | 需 CMake + MSVC 工具链（本机缺） |

**定位**：与 Kokoro 并列为「纯本地离线灾备引擎」，**不替代** Gemini 3.8 Flash TTS / 豆包 / Qwen-TTS 主产线。

---

## 二、本机硬件与硬约束

| 项 | 值 | 影响 |
|---|---|---|
| GPU | NVIDIA GTX 1050，**4GB 显存** | 官方要 ~8GB（VoxCPM2）/ ~6GB（1.5），**跑不了 GPU 推理** |
| CPU | Intel i7-8750H，6 核 12 线程 @2.2GHz | 无 AVX512，bf16 走软件模拟 |
| 内存 | 24GB（可用 ~17GB） | fp32 建模 2B 参数会撑爆提交限制 |
| **页面文件** | 原固定 **2424MB**（`AutomaticManagedPagefile=False`） | **这是最初 access violation 的真凶** |

### 崩溃根因（已确诊）

第一次加载 VoxCPM2 直接段错误（exit 139），`faulthandler` 栈定位在：

```
torch/nn/modules/linear.py:109 in __init__   ← torch.empty()
minicpm4/model.py:231 → 244 → 344 (listcomp) ← 逐层建 MiniCPMDecoderLayer
```

插桩监控 `GlobalMemoryStatusEx` 后真相大白：

```
[Linear#40 ] availPhys=15.27GB  availCommit=10.42GB
...
[Linear#320] availPhys= 8.05GB  availCommit= 0.01GB   ← 提交内存耗尽
Windows fatal exception: access violation
```

**不是** torch bug、**不是** 显存问题、**不是** 单段 Linear 太大 —— 而是
Windows 提交限制（RAM 24GB + 页面文件 2.4GB ≈ 28GB 上限）在建模阶段被耗尽，
分配器拿不到地址空间就报 access violation，而不是干净的 `MemoryError`。

### 三项修复

1. **页面文件改系统托管**（根本解法）
   ```powershell
   $cs = Get-CimInstance Win32_ComputerSystem
   $cs | Set-CimInstance -Property @{AutomaticManagedPagefile = $true}
   ```
   > 已在本机执行，**需重启后生效**，届时提交上限会显著提升。

2. **bfloat16 建模**（把建模内存减半）
   ```python
   torch.set_default_dtype(torch.bfloat16)   # 必须在建模之前
   ```
   fp32 下建模推进到 Linear#320 就耗尽提交内存；切 bf16 后顺利建到 Linear#420+
   并完成权重加载。

3. **降级 torch 到官方锁定版本**
   上游 `uv.lock` 锁定 `torch==2.10.0`，本机 pip 默认装到了 2.14.1，已对齐：
   ```
   pip install "torch==2.10.0" "torchaudio==2.10.0" --index-url https://download.pytorch.org/whl/cpu
   ```

---

## 三、目录结构

```
external/voxcpm/
├── .venv/                      独立虚拟环境（Python 3.11.9 + torch 2.10.0+cpu）
├── src_repo/                   上游源码（git clone --depth 1）
├── models/
│   ├── VoxCPM1.5/              ✅ 1.95GB（audiovae.pth 346MB + model.safetensors 1.60GB）
│   └── VoxCPM2/                4.96GB（已下好，需扩容页面文件后重启才能加载）
└── _worker.py                  合成 worker（在该 venv 内运行）
```

主解释器**不装 torch**，通过子进程调用 `.venv/Scripts/python.exe _worker.py`，避免依赖冲突。

---

## 四、使用方式

### 4.1 管线内（推荐）

```bash
# 周末版双主播
SIGNAL_POP_TTS_BACKEND=voxcpm python tools/gen_dual_tts.py 20261016

# 平日版
SIGNAL_POP_TTS_BACKEND=voxcpm python tools/gen_cloud_tts.py 20261016
```

音色走「声音设计」（Voice Design）自然语言描述，无需参考音频：

| 角色 | 音色描述 |
|---|---|
| 阿信（男） | `A mature man, calm and steady voice, standard Mandarin` |
| 小蓝（女） | `A young woman, lively and cheerful voice, standard Mandarin` |
| 平日女声 | `A young woman, bright and friendly voice, standard Mandarin` |

### 4.2 独立调用

```bash
cd external/voxcpm
./.venv/Scripts/python.exe _worker.py \
  --text "(A mature man, calm and steady voice)大家好，这是信号弹。" \
  --out test.wav
```

---

## 五、实测性能（本机 i7-8750H / GTX 1050 / CPU 推理）

| 测试 | 音频时长 | 耗时 | RTF | 采样率 |
|---|---|---|---|---|
| 中文新闻句 | 5.60s | 217.7s | **38.87** | 44.1kHz |
| 中文比分句 | 4.80s | 189.4s | **39.47** | 44.1kHz |
| 英文句 | 5.92s | 209.1s | **35.33** | 44.1kHz |

- 模型加载：36.8s
- 官方 RTX 4090 参考 RTF：VoxCPM2 ≈ 0.30、1.5 ≈ 0.15 → 本机约 **200~260 倍**差距
- **RTF 35~40 意味着：生成 12 分钟成片音频需 7~8 小时**，只适合应急补条，
  不适合整期批量生产

### 音频质量自检（客观指标）

| 文件 | 时长 | 峰值 | RMS | 语音占比 | 前导静音 |
|---|---|---|---|---|---|
| 01_zh_news.wav | 5.60s | 0.969 | 0.218 | 82.4% | 0.02s |
| 02_zh_score.wav | 4.80s | 0.530 | 0.054 | 89.1% | 0.00s |
| 03_en.wav | 5.92s | 0.969 | 0.198 | 90.2% | 0.00s |

无削波（peak<1.0）、无异常静音、中英文均可正常输出。

---

## 六、已知限制与后续

1. **比分发音**：VoxCPM 对 `7-5` 仍可能读成「减」，管线在 `voxcpm_synthesize()`
   里用 `re.sub(r"(\d+)-(\d+)", r"\1比\2", text)` 兜底（与 Kokoro 后端同一策略）。
2. **内存**：跑 VoxCPM2 前建议先重启让页面文件扩容生效，否则仍会 access violation。
3. **速度**：CPU RTF 35~40 是硬伤。若要提速，优先级建议：
   - 换 llama.cpp-omni + GGUF Q8_0（需装 CMake + MSVC，Windows 有预编译安装包）
   - 或升级到 12GB+ 显存的显卡，走 GPU 推理（RTF 可到 0.3，接近实时）
4. **声音克隆**：VoxCPM 支持 3~10s 参考音频克隆，若要用固定主播声线，
   可用已有阿信/小蓝 TTS 成品作为 `prompt_wav_path` + `prompt_text` 做 Ultimate Cloning。

---

## 七、上游能力备忘（VoxCPM2，暂未在本机跑通）

- 30 种语言 + 9 种中文方言（粤语、四川话、东北话…）—— **对广州受众有潜在价值**
- Voice Design：纯文字描述生成新音色，无需参考音频
- Controllable Cloning：克隆音色同时用自然语言调节情绪/语速
- Ultimate Cloning：参考音频 + 转写，保真度最高
- 原生 48kHz 输出（AudioVAE V2 非对称编解码 + 内置超分）
- 推理服务：Nano-vLLM（RTF ≈0.13）、vLLM-Omni（OpenAI 兼容 API）
