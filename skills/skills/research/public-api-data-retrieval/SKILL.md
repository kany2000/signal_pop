---
name: public-api-data-retrieval
description: 从公共API获取数据（天气、历史事件等）的策略和技巧，包括多源备选和HTML解析
tags: [api, curl, weather, historical-events, fallback-strategies]
---

# Public API Data Retrieval with Fallback Strategies

## Overview
When retrieving factual data (weather, historical events, etc.), use multiple public APIs with fallback strategies, as some services may be unreliable or return data in difficult-to-parse formats.

## Weather Data
**Primary method**: Use `wttr.in` service via curl

```bash
# Current weather (simple format)
curl -s "https://wttr.in/{city}?format=%C+%t"

# 3-day forecast with detailed breakdown
curl -s "https://wttr.in/{city}?format=v2"
curl -s "https://wttr.in/{city}?3"
```

The `wttr.in` service provides:
- Current conditions: `%C` (weather condition), `%t` (temperature), `%h` (humidity), `%w` (wind)
- ASCII art visualizations for easy parsing
- Unicode weather symbols (☀️ ☁️ ☂️)
- Timezone-aware output

## Historical Events
**Primary method**: Use Wikipedia API with HTML content parsing

```bash
# Get JSON with full HTML content
curl -s "https://zh.wikipedia.org/w/api.php?action=parse&page={date}&prop=text&format=json&redirects=1"
```

**Parsing strategy**:
1. Parse JSON response to extract `parse.text['*']` (HTML content)
2. Use regex to find list items containing years: `<li>.*?(\d{4})[^<]*</li>`
3. Search for specific known events with string matching (e.g., "莎士比亚", "世界读书日")
4. Have a backup list of well-known events for common dates

## Fallback Chain
Always implement a cascade approach:

1. **Try primary source** (Wikipedia API for historical events, wttr.in for weather)
2. **If JSON/HTML parsing fails**, try alternative endpoints or simpler formats
3. **If all automated methods fail**, fall back to static known facts for common dates
4. **If still uncertain**, output minimal verified information only

## Error Handling
- Check JSON parsing errors and provide defaults
- Verify extracted data contains expected patterns (e.g., 4-digit years)
- Use try-except blocks with fallback values
- When extracting specific events, have at least 2-3 backup candidates

## Common Pitfalls
- Wikipedia API returns HTML, not plain text - need to use regex on HTML or a proper parser
- Some services (Baidu) trigger captchas on automated requests - avoid or use proper headers
- Direct HTML scraping of websites often fails due to JS/CAPTCHAs - prefer official APIs
- Weather emojis may not render in all terminals - document what `%C` symbols mean (☀️ = Clear, ☁️ = Cloudy, ⛅ = Partly Cloudy, 🌦 = Light Rain)

## Verification
- Cross-check dates against multiple sources when possible
- Confirm historical events include the actual date in question (e.g., "April 23")
- Validate temperature ranges are reasonable for the location
- For historical events, prefer well-documented facts (Shakespeare's death, World Book Day, etc.)

## Example Workflow
For "historical events on April 23":
1. Query Wikipedia API for "4月23日"
2. Parse HTML, look for `<li>` items with year patterns
3. Extract event descriptions with associated years
4. Match against known important events for validation
5. If extraction fails, use pre-known: Shakespeare's death (1616), World Book Day (1995), Cervantes death (1616)

For weather in Guangzhou:
1. Use `https://wttr.in/Guangzhou?format=v2` for detailed 3-day
2. Parse ASCII art and text for temperatures (format: `+23(25)°C` shows range)
3. Extract weather symbols and translate: ☀️ = Sunny, ☁️ = Cloudy, ⛅ = Partly Cloudy, 🌦 = Light Rain
4. Include humidity, wind, pressure for completeness

## Skill Triggers
- User asks for weather forecast for any city
- User asks for "historical events today" or specific date
- Need to retrieve factual data from public sources
- One API fails and need to implement fallback strategy
- User asks to research a Chinese A-share stock (e.g. "帮我关注某只股票")
- Need financial data, shareholder structure, or company profile for Chinese listed stocks
- User asks "what match/game is on at Beijing-time T" or any sports/event
  schedule question — use Wikipedia `action=parse` + `prop=wikitext`
  (see references/sports-schedule-wikipedia.md); do NOT rely on search-engine
  scraping, which returns empty in this environment.

## Related Resources
- `references/china-stock-research-eastmoney-apis.md` — 东方财富A股数据API实战参考
- `references/agnes-ai-api.md` — Agnes AI (apihub.agnes-ai.com) OpenAI兼容API实测记录，含模型列表、认证方式、可用/不可用端点 — 东方财富A股数据API实战参考，含行情/财务/F10/股东结构接口及踩坑记录
- `references/sports-schedule-wikipedia.md` — 体育/赛事赛程抓取实战：Wikipedia action=parse wikitext + 时区换算到北京时间（世界杯等）