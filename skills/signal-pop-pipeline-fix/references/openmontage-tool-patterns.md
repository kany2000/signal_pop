# OpenMontage 工具库实测模式 (2026-06-26)

## 核心工具调用模式

### 1. 素材搜索/下载 - DirectClipSearch
```python
from tools.video.direct_clip_search import DirectClipSearch

tool = DirectClipSearch()
result = tool.execute({
    'operation': 'search',
    'queries': [
        {'query': 'rain city night streets', 'clips_per_query': 2},
        {'query': 'neon lights wet pavement', 'clips_per_query': 2}
    ],
    'sources': ['archive_org', 'wikimedia', 'nasa', 'mixkit', 'dareful'],
    'output_dir': '/path/to/clips'
})
# 返回: {'success': True, 'data': {'total_clips': N, 'clips': [...]}}
```

### 2. 视频合成 - VideoCompose
```python
from tools.video.video_compose import VideoCompose

tool = VideoCompose()
result = tool.execute({
    'operation': 'compose',
    'edit_decisions': {
        'render_runtime': 'ffmpeg',
        'cuts': [
            {'source': '/path/clip1.mp4', 'in_seconds': 0, 'out_seconds': 10, 'transition': 'none'},
            {'source': '/path2.webm', 'in_seconds': 0, 'out_seconds': 10, 'transition': 'crossfade'}
        ],
        'audio': {
            'source': '/path/narration.wav',
            'mix_level': 1.0,
            'duck_music': False  # 音频混音由 audio_mixer 单独处理
        },
        'output': {'resolution': '1920x1080', 'fps': 30, 'codec': 'libx264', 'crf': 23}
    },
    'output_path': '/path/output.mp4'
})
```

### 3. 音频混音 - AudioMixer
```python
from tools.audio.audio_mixer import AudioMixer

tool = AudioMixer()

# 简单混音 (旁白 + 背景音乐)
result = tool.execute({
    'operation': 'mix',
    'tracks': [
        {'path': '/path/narration.wav', 'role': 'speech', 'volume': 1.0},
        {'path': '/path/music.wav', 'role': 'music', 'volume': 0.3, 'fade_in_seconds': 2}
    ],
    'output_path': '/path/mixed.wav',
    'normalize': True  # loudnorm -16 LUFS
})

# Ducking (语音时压低音乐) - 推荐用 full_mix
result = tool.execute({
    'operation': 'full_mix',
    'tracks': [
        {'path': '/path/narration.wav', 'role': 'speech', 'start_seconds': 0},
        {'path': '/path/music.wav', 'role': 'music', 'volume': 0.3}
    ],
    'ducking': {'enabled': True, 'music_volume_during_speech': 0.15, 'attack_ms': 200, 'release_ms': 500},
    'normalize': True,
    'output_path': '/path/mixed_ducked.wav'
})
```

### 4. 字幕烧录 - FFmpeg 直接调用
```bash
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontSize=48,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Shadow=1,MarginV=80'" output.mp4
```

## Signal Pop 管道架构映射

### RPA层 (自动化执行)
```
fetch_news → filter_news → generate_brief
    ↓
direct_clip_search (queries → clips)
    ↓
piper_tts / mimo_tts (script → narration.wav)
    ↓
audio_mixer (narration + music → mixed.wav)
    ↓
video_compose (clips + audio → video.mp4)
    ↓
burn_subtitles (video + srt → video_subs.mp4)
    ↓
hyperframes_render (end_card + philosophy_quote)
```

### Workflow层 (编排/决策)
```
documentary-montage skill (fast path):
  ├─ idea-director      → brief + scene_plan
  ├─ asset-director     → clip selection + relevance scoring
  ├─ edit-director      → edit_decisions (timeline, transitions, music)
  └─ compose-director   → video_compose + audio_mixer + subtitles
```

### Agent层 (策略/质量)
```
内容策略: 选题角度、观点注入、风格一致性
质量把关: 时长控制 (8-12min)、节奏把控、版权合规
预算控制: 免费素材优先、TTS 本地化、GPU 按需
```

## 关键参数速查

| 工具 | 关键参数 | 推荐值 | 说明 |
|------|----------|--------|------|
| video_compose | crf | 23 | 质量/大小平衡 |
| video_compose | preset | medium | 平衡速度/质量 |
| audio_mixer | target_lufs | -16 | 广播标准响度 |
| audio_mixer | duck_level | 0.15 | 语音时音乐音量 |
| direct_clip_search | clips_per_query | 2-3 | 避免过量下载 |
| 字幕 | FontSize | 48 | 1080p 适中 |
| 字幕 | MarginV | 80 | 底部安全区 |

## 常见问题

1. **audio_mixer tracks 格式**: 必须用 `tracks` 数组，`role` 必须为 `speech`/`music`/`sfx`/`primary`/`secondary`
2. **video_compose audio.duck_music**: 设为 False，由 audio_mixer 全权处理混音
3. **素材格式**: 输入可混用 mp4/webm/mov，输出统一 mp4 (libx264)
4. **分辨率**: 强制 1920x1080，短边缩放 + 黑边填充 (video_compose 内部处理)
5. **字幕编码**: SRT 必须 UTF-8，中文无需转码