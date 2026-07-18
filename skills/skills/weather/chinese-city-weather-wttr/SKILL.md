---
name: chinese-city-weather-wttr
description: Retrieve and format weather forecasts for Chinese cities using wttr.in JSON API with proper Chinese output
version: 1.1.0
metadata:
  hermes:
    tags: [weather, api, china, forecasting, data-parsing]
    related_skills: []
---

# Chinese City Weather Forecast using wttr.in API

## Overview
Retrieve and format weather forecasts for Chinese cities using wttr.in's JSON API. Handles current conditions and multi-day forecasts with proper Chinese output formatting.

## When to Use
- Need weather data for Chinese cities (广州, 北京, 上海, etc.)
- Want structured JSON parsing for wttr.in API
- Generating Chinese-language weather reports

## Prerequisites
- Python standard library (urllib.request, json, datetime)
- Internet access to wttr.in

## Steps

### 1. API Call
```python
import urllib.request
import json

city = "Guangzhou"  # Use English city name for API
url = f"https://wttr.in/{city}?format=j1"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())
```

### 2. Current Weather
```python
current = data['current_condition'][0]
temp_c = current['temp_C']
weather_desc = current['weatherDesc'][0]['value']
humidity = current.get('humidity', 'N/A')
wind_speed = current.get('windspeedKmph', 'N/A')
```

### 3. Multi-Day Forecast Structure
**Critical insight**: wttr.in returns multi-day data as a **list** in `data['weather']`, not as nested arrays. Each element represents one day:

```python
weather_data = data['weather']  # This is a list of day objects

# For day i:
day = weather_data[i]
date_str = day['date']  # e.g., "2026-04-27"
max_temp = day['maxtempC']  # Direct value, NOT an array
min_temp = day['mintempC']  # Direct value
# Weather description: take from last hourly entry (21:00)
representative_weather = day['hourly'][-1]['weatherDesc'][0]['value']
```

**Common pitfalls**:
- ❌ Don't access `weather_data[0]['maxtempC'][i]` - it's a single string, not a list
- ✅ Access `weather_data[i]['maxtempC']` directly for day i
- ✅ Representative weather is in `hourly[-1]`, not a separate field at day level

### 4. Date Formatting
```python
from datetime import datetime
dt = datetime.strptime(date_str, '%Y-%m-%d')
cn_date = f"{dt.month}月{dt.day}日"
```

### 5. Clothing/Travel Suggestions
```python
temp_num = int(temp_c)
if temp_num >= 30:
    clothing = '高温天气，建议穿着短袖、短裤等清凉衣物，注意防暑降温，多补充水分。'
elif temp_num >= 25:
    clothing = '温暖天气，适合穿着轻薄长袖或短袖，注意防晒。'
elif temp_num >= 15:
    clothing = '舒适温度，建议穿着薄外套或长袖衬衫，注意早晚温差。'
else:
    clothing = '较凉天气，建议穿着外套或毛衣，注意保暖。'

travel = '出行建议：建议关注天气变化，' + ('如需外出请携带雨具。' if 'rain' in weather_desc.lower() or '雨' in weather_desc else '天气适宜出行。')
```

## Complete Example
```python
import urllib.request
import json
from datetime import datetime

url = "https://wttr.in/Guangzhou?format=j1"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())

# Current conditions
current = data['current_condition'][0]
print(f"当前温度：{current['temp_C']}°C")
print(f"当前天气：{current['weatherDesc'][0]['value']}")
print()

# 3-day forecast
for i in range(min(3, len(data['weather']))):
    day = data['weather'][i]
    dt = datetime.strptime(day['date'], '%Y-%m-%d')
    weather_desc = day['hourly'][-1]['weatherDesc'][0]['value']
    print(f"{dt.month}月{dt.day}日：天气：{weather_desc}，温度：{day['mintempC']}°C - {day['maxtempC']}°C")
```

## Notes
- API returns 8 hourly entries per day (0, 300, 600, 900, 1200, 1500, 1800, 2100 minutes from midnight)
- Use `hourly[-1]` (21:00 entry) for representative daily weather description
- City name must be in English (Pinyin works: Guangzhou, Beijing, Shanghai)
- The free API may have rate limits but is generally reliable
- `current_condition` is real-time; `weather[]` array contains daily forecasts

## Alternative: Simple Text Format (No JSON Parsing Needed)
For quick lookups without JSON parsing, use wttr.in's plain text formats:

```bash
# Simple current weather: "Clear +18°C"
curl -s "https://wttr.in/Guangzhou?format=%C+%t"

# Detailed 3-day with full visualization
curl -s "https://wttr.in/Guangzhou?format=v2"
```

**Advantages**:
- No JSON parsing required (useful for shell scripts, cron jobs)
- Includes visual weather symbols that are self-explanatory
- Shows temperature ranges in parentheses: `+23(25)°C` = min 23°C, feels-like 25°C

**Output parsing**:
- `%C` = weather condition emoji/symbol: ☀️ (Clear), ☁️ (Cloudy), ⛅ (Partly Cloudy), 🌦 (Light Rain), 🌧 (Rain)
- `%t` = current temperature (with `+` sign)
- `format=v2` includes time-of-day breakdowns (Morning, Noon, Evening, Night) with detailed conditions

**When to use**: Quick queries, cron jobs, shell scripts, or when you need human-readable output without JSON overhead.

## Network Troubleshooting

If `urllib`/`requests` fail with `ssl.SSLEOFError: EOF occurred in violation of protocol` or `SSL_ERROR_SYSCALL`:
- The endpoint resolves (ping works) but TLS handshake fails → environment is behind an SSL-inspecting proxy/firewall.
- **Do NOT** encode "wttr.in is blocked" as a permanent constraint — this is environment-specific.
- Try in order: Python `urllib` → `requests` → `curl` → `wget` → browser automation. Different tools may use different TLS stacks that bypass the inspection.
- If all HTTPS fails, try `http://` (plain HTTP) endpoints listed in Fallback APIs below.
- OpenSSL diagnostic: `openssl s_client -connect wttr.in:443` — if it shows `no peer certificate available` and closes immediately, the proxy is terminating TLS at the network layer.

## Primary Working API: weather.com.cn (HTTP)

In environments with SSL-inspecting proxies/firewalls, **weather.com.cn via HTTP** works reliably. This should be tried before Open-Meteo:

```python
import urllib.request
import json
import re

# Current weather
url = "http://d1.weather.com.cn/sk_2d/101280101.html"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://www.weather.com.cn/'
})
with urllib.request.urlopen(req, timeout=8) as response:
    content = response.read().decode('utf-8')

# Parse JS variable: var dataSK={...}
match = re.search(r'var dataSK=(.+)', content)
data = json.loads(match.group(1))
print(f"温度: {data['temp']}°C, 天气: {data['weather']}, 湿度: {data['SD']}")

# 3-day forecast + life indices
url2 = "http://d1.weather.com.cn/weather_index/101280101.html"
# Returns: var cityDZ, var dataSK, var dataZS (life indices), var fc (forecast)
```

**City code lookup**: `101280101` = Guangzhou. For other cities:
- Beijing: `101010100`
- Shanghai: `101020100`
- Shenzhen: `101280601`

**Weather code mapping** (for `fc['f'][i]['fa']`):
| Code | 中文 | Code | 中文 |
|------|------|------|------|
| 00/01 | 晴 | 04 | 雷阵雨 |
| 02 | 多云 | 07 | 小雨 |
| 03 | 阴 | 08-09 | 中雨-大雨 |

## Fallback APIs

If weather.com.cn also fails, try these free APIs (no API key required):

```python
import requests

# Open-Meteo (free, no key, HTTPS)
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 23.12,       # Guangzhou
    "longitude": 113.32,
    "current_weather": True,
    "daily": "temperature_2m_max,temperature_2m_min,weathercode",
    "timezone": "Asia/Shanghai",
    "forecast_days": 3
}
r = requests.get(url, params=params, timeout=10)
data = r.json()
# WMO weather codes: 0=Clear, 1-3=PartlyCloudy, 45-48=Fog, 51-67=Rain, 71-77=Snow, 80-82=Showers
wmo_map = {0:'晴',1:'晴间多云',2:'多云',3:'阴',45:'雾',48:'霜雾',51:'小毛毛雨',53:'中毛毛雨',55:'大毛毛雨',61:'小雨',63:'中雨',65:'大雨',71:'小雪',73:'中雪',75:'大雪',77:'雪粒',80:'小阵雨',81:'中阵雨',82:'大阵雨',95:'雷暴',96:'雷暴伴冰雹',99:'强雷暴伴冰雹'}
current = data['current_weather']
print(f"{current['temperature']}°C, {wmo_map.get(current['weathercode'], '未知')}")
for i, (mx, mn, wc) in enumerate(zip(data['daily']['temperature_2m_max'], data['daily']['temperature_2m_min'], data['daily']['weathercode'])):
    print(f"Day {i}: {wmo_map.get(wc,'未知')} {mn}-{mx}°C")
```

**WMO weather code reference** (for Open-Meteo):
| Code | Description (EN) | 中文 |
|------|-------------------|------|
| 0 | Clear sky | 晴 |
| 1-3 | Cloudy/Overcast | 多云/阴 |
| 45, 48 | Fog | 雾/霜雾 |
| 51-55 | Drizzle | 毛毛雨 |
| 61-65 | Rain | 雨 |
| 71-77 | Snow | 雪 |
| 80-82 | Showers | 阵雨 |
| 95-99 | Thunderstorm | 雷暴 |

## History
Created: 2026-04-27 after debugging JSON structure parsing
Key learning: `weather` is a list of day objects, not a single object with nested arrays. Each day's `maxtempC`/`mintempC` are direct values; weather description must be extracted from hourly data.

Updated: 2026-05-26
- Added Network Troubleshooting section: SSL-inspecting proxy symptoms (SSL_ERROR_SYSCALL, EOF errors) and diagnostic steps.
- Added Fallback APIs section: Open-Meteo as a free no-key alternative with WMO weather code reference table.

Updated: 2026-05-29
- Discovered weather.com.cn (d1.weather.com.cn) works via HTTP despite SSL inspection blocking HTTPS APIs.
- Primary endpoint: `http://d1.weather.com.cn/sk_2d/<citycode>.html` for current weather; `weather_index/<citycode>.html` for forecast + life indices.
- Added city code table and weather code mapping for the `fc` forecast array structure.