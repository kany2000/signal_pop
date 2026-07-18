# Piper TTS 本地部署方案 (2026-06-26)

## 为什么选 Piper
- ✅ 完全离线，无 API 限制
- ✅ 支持任意长度文本 (分句合成自动拼接)
- ✅ 中文模型质量高 (zh_CN-huayan-medium)
- ✅ 模型小 (~50MB)，启动快
- ✅ Python 包 `piper-tts` 直接可用
- ✅ 输出标准 WAV，兼容现有 audio_mixer

## 安装
```bash
pip install piper-tts
# 或从源码: https://github.com/rhasspy/piper
```

## 模型下载
```bash
# 中文女声 (推荐，自然度高)
mkdir -p /home/kan/models/piper
cd /home/kan/models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json

# 备选男声
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/low/zh_CN-huayan-low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/low/zh_CN-huayan-low.onnx.json
```

## 使用方式

### 命令行
```bash
echo "这是隔天信号弹的测试视频。城市雨夜，霓虹倒映。" | \
  piper --model /home/kan/models/piper/zh_CN-huayan-medium.onnx \
        --output_file /path/narration.wav
```

### Python API (推荐，集成到 tts_piper.py)
```python
# src/tts_piper.py
from piper import PiperVoice
import wave

class PiperTTS:
    def __init__(self, model_path="/home/kan/models/piper/zh_CN-huayan-medium.onnx"):
        self.voice = PiperVoice.load(model_path)
    
    def synthesize(self, text, output_path):
        """合成长文本，自动分句"""
        # Piper 内部按标点分句，流式写入 WAV
        with wave.open(output_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.voice.config.sample_rate)
            
            for audio_bytes in self.voice.synthesize_stream_raw(text):
                wav_file.writeframes(audio_bytes)
        
        return output_path

# 用法
tts = PiperTTS()
tts.synthesize("长文本...", "/path/narration.wav")
```

### 分段合成 + SRT 生成 (兼容现有流程)
```python
def synthesize_with_srt(text, output_wav, output_srt, voice="female"):
    """按 '第X条' 分段合成，生成 SRT 时间轴"""
    import re
    
    # 分段逻辑同 tts_mimo.py
    segments = split_by_markers(text)  # 复用现有分段函数
    
    tts = PiperTTS(model_path=MODEL_MAP[voice])
    
    with wave.open(output_wav, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(tts.voice.config.sample_rate)
        
        srt_entries = []
        current_time = 0.0
        
        for i, (seg_text, marker) in enumerate(segments):
            seg_start = current_time
            seg_audio = b""
            
            for chunk in tts.voice.synthesize_stream_raw(seg_text):
                seg_audio += chunk
                wav_file.writeframes(chunk)
            
            # 计算时长
            seg_duration = len(seg_audio) / (2 * tts.voice.config.sample_rate)  # bytes / (channels * sample_rate * 2)
            seg_end = current_time + seg_duration
            
            srt_entries.append(f"{i+1}\n{format_srt_time(seg_start)} --> {format_srt_time(seg_end)}\n{seg_text}\n")
            current_time = seg_end
    
    with open(output_srt, "w") as f:
        f.write("\n".join(srt_entries))
    
    return output_wav, output_srt

MODEL_MAP = {
    "female": "/home/kan/models/piper/zh_CN-huayan-medium.onnx",
    "male": "/home/kan/models/piper/zh_CN-huayan-low.onnx"
}
```

## 集成到现有流水线

### 修改 `scripts/generate_audio_only.sh`
```bash
# 替换 tts_mimo.py 调用为 tts_piper.py
python3 src/tts_piper.py "$SCRIPT_CONTENT" --voice female \
  --output output/daily/signal_pop_daily_YYYYMMDD_female.wav \
  --srt output/daily/signal_pop_daily_YYYYMMDD_female.srt

# 转 MP3 (供发布)
ffmpeg -i output/daily/signal_pop_daily_YYYYMMDD_female.wav \
       -codec:a libmp3lame -q:a 2 \
       output/daily/signal_pop_daily_YYYYMMDD_female.mp3
```

### 保留 MiMo 作为备选
```bash
# 环境变量控制 TTS 引擎
TTS_ENGINE=${TTS_ENGINE:-piper}  # piper | mimo

if [ "$TTS_ENGINE" = "piper" ]; then
    python3 src/tts_piper.py ...
else
    python3 src/tts_mimo.py ...
fi
```

## 预期效果对比

| 指标 | MiMo API | Piper 本地 |
|------|----------|------------|
| 最大时长 | ~1.1s | 无限制 |
| 10条新闻合成 | 失败/需分段拼接 | 单次 ~10-15s |
| 音质 | 优秀 (商业级) | 良好 (开源 SOTA) |
| 部署复杂度 | 低 (API Key) | 中 (模型下载) |
| 运行成本 | 按量付费 | 免费 |
| 网络依赖 | 是 | 无 |

## 迁移清单
- [ ] 下载中文模型到 `/home/kan/models/piper/`
- [ ] 创建 `src/tts_piper.py` (复用分段/SRT 逻辑)
- [ ] 修改 `scripts/generate_audio_only.sh` 支持双引擎
- [ ] 测试 Daily 全流程 (目标 < 2分钟)
- [ ] 验证 Weekly 视频合成音频同步
- [ ] 更新 cron 环境变量 `TTS_ENGINE=piper`