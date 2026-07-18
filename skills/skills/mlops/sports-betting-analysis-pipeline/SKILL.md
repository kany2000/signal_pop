---
name: sports-betting-analysis-pipeline
description: Multi-source sports betting analysis pipeline — quota-aware API orchestration, daily data collection, historical baselines, real-time odds, news signals, and weighted prediction generation.
category: mlops
tags: [sports-betting, odds-api, data-pipeline, prediction, world-cup]
---

# Sports Betting Analysis Pipeline

## Overview
Reusable pattern for tournament-level betting analysis (World Cup, Euros, etc.) combining:
- **Multiple odds APIs** with quota tracking (The Odds API, RapidAPI providers)
- **Daily news collection** via RSS feeds (BBC, Guardian, Sky Sports)
- **Historical baseline** from comprehensive pre-tournament analysis
- **Real-time match odds** for specific fixtures
- **Weighted prediction model** (baseline + market + news signals)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Odds APIs  │     │  RSS Feeds  │     │  Baseline   │
│  (quota-mgr)│     │  (daily)    │     │  (static)   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
              ┌─────────────────────────┐
              │   odds_latest.json      │
              │   daily_collection/     │
              │   FINAL_COMPREHENSIVE_  │
              │   ANALYSIS.md           │
              └───────────┬─────────────┘
                          ▼
              ┌─────────────────────────┐
              │  final_predict.py       │
              │  (weighted scoring)     │
              └───────────┬─────────────┘
                          ▼
              ┌─────────────────────────┐
              │  Champion / Runner-up   │
              │  Top 4 / Dark Horse     │
              │  Match-specific odds    │
              └─────────────────────────┘
```

## Key Scripts (in project `scripts/`)

| Script | Purpose | Schedule |
|--------|---------|----------|
| `scrape_all.py` | Fetch all odds sources → `odds_latest.json` | Manual / pre-match |
| `collect_daily.py` | RSS news → `daily_collection/report_YYYY-MM-DD.txt` | Cron daily 08:30 |
| `final_predict.py` | Combine all sources → prediction | Manual / pre-match |

## API Quota Management

**The Odds API** (primary for outright winner + match odds)
- **Free tier: 500 requests/month — BUT NO ODDS DATA** — only `/events` (schedule/fixtures) endpoint works
- Paid tier required for `/odds` endpoints (outright winner + match odds) — ~$30/month
- Endpoint: `soccer_fifa_world_cup_winner` + `soccer_fifa_world_cup`
- Check quota via response headers or dashboard
- **Pitfall**: Returns `match_odds` as **list** (not dict) — iterate directly
- **⚠️ Verified June 2026**: Free key returns `INVALID_KEY` on `/odds` calls; `/events` works fine

**RapidAPI: free-api-live-football-data** (backup for qualifiers)
- Free tier: monthly quota, often exhausted early
- Returns 429 when quota exceeded
- Use only for qualifier match odds (not outright winner)

## Data Structures

### `odds_latest.json` (output of `scrape_all.py`)
```json
{
  "timestamp": "2026-06-10 10:12:25",
  "free_api": null,
  "odds_api": {
    "source": "The Odds API",
    "winner_odds": { "eu": [...], "uk": [...], ... },
    "match_odds": [                    // ← LIST, not dict
      {
        "home_team": "Mexico",
        "away_team": "South Africa",
        "commence_time": "2026-06-11T19:00:00Z",
        "bookmakers": [...]
      },
      ...
    ]
  }
}
```

### `daily_collection/report_YYYY-MM-DD.txt`
Structured RSS report with:
- Injury / Squad / Coaching / Odds / Match classifications
- Team mention frequency (signal strength)
- Key signal flags (⚠️ injury, 🔄 coaching change)

### `FINAL_COMPREHENSIVE_ANALYSIS.md`
Pre-tournament baseline with probability table:
```
| 排名 | 球队 | 概率 |
|------|------|------|
| 1    | 法国 | 22%  |
| 2    | 阿根廷 | 17% |
...
```

## Prediction Model (final_predict.py)

**Weighted scoring**:
```
combined = baseline * 0.4 + market_implied * 0.3 + news_signals * 0.3
```
- Baseline: from comprehensive analysis (static, pre-tournament)
- Market implied: from `odds_latest.json` consensus odds
- News signals: team mention count in daily reports (capped)

**Output**:
- 🥇 Champion, 🥈 Runner-up, 🥉 Top 4, 🌟 Dark Horse
- Risk flags (⚠️ injury signals)
- Detailed scoreboard with component breakdown

### Common Operations

### Refresh odds (pre-match)
```bash
cd ~/worldcup-analysis
python3 scripts/scrape_all.py
python3 scripts/final_predict.py
## Free Historical Odds with xG (football-data.co.uk)

### Download World Cup Excel (contains bet365, Betfair, Max, Avg odds + xG for all matches)
```bash
# Download World Cup Excel (contains bet365, Betfair, Max, Avg odds + xG for all matches)
curl -s "https://www.football-data.co.uk/WorldCup2026.xlsx" -o data/WorldCup2026.xlsx

# Parse with Python - extract team stats & upcoming matches with odds
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('data/WorldCup2026.xlsx')
ws = wb['WorldCup2026']
for row in ws.iter_rows(min_row=2, values_only=True):
    finished = row[15] if len(row) > 15 else None
    if finished != '90 minutes' and finished != 'Penalties' and finished != 'Extra time':
        home, away = row[1], row[2]
        b365_h, b365_d, b365_a = row[28], row[29], row[30]
        bf_h, bf_d, bf_a = row[31], row[32], row[33]
        h_max, d_max, a_max = row[34], row[35], row[36]
        h_avg, d_avg, a_avg = row[37], row[38], row[39]
        print(f'{home} vs {away} | bet365: {b365_h}/{b365_d}/{b365_a} | Betfair: {bf_h}/{bf_d}/{bf_a} | Max: {h_max}/{d_max}/{a_max} | Avg: {h_avg}/{d_avg}/{a_avg}')
"
```

### Build Poisson + Dixon-Coles model from historical data (xG-weighted)
```python
# Quick model: team attack/defense strength from WorldCup2022/2018/2014 + Qualifiers sheets
# See scripts/pipeline_health_check.py for health checks, adapt for model training
```

### Query specific match odds
```python
import json
with open('odds_data/odds_latest.json') as f:
    data = json.load(f)
for match in data['odds_api']['match_odds']:
    if 'mexico' in match['home_team'].lower() and 'south africa' in match['away_team'].lower():
        for bm in match['bookmakers']:
            for market in bm['markets']:
                if market['key'] == 'h2h':
                    for o in market['outcomes']:
                        print(f"{o['name']}: {o['price']}")
```

### Check API quota status
```bash
# The Odds API: check dashboard or response headers
# RapidAPI: run scrape_odds.py → 429 = quota exhausted
```

## Pitfalls & Gotchas

1. **`match_odds` is a list** — not a dict keyed by region. Iterate directly.
2. **RapidAPI free tier dies fast** — don't rely on it for daily updates. The Odds API is more reliable.
3. **Odds update frequency** — match odds can change multiple times/day. Refresh `scrape_all.py` on match day morning.
4. **Timezones** — `commence_time` is UTC. Convert for local display (e.g., +8 for Beijing).
5. **Missing match odds** — not all fixtures have odds early. Check `match_odds` length vs expected fixtures.
6. **News signal noise** — RSS picks up generic mentions. Filter keywords carefully (`WC_KEYWORDS` in `collect_daily.py`).

## Extending for Other Tournaments

Replace sport keys:
- World Cup: `soccer_fifa_world_cup_winner` + `soccer_fifa_world_cup`
- Euros: `soccer_uefa_euro_winner` + `soccer_uefa_euro`
- Champions League: `soccer_uefa_champs_league_winner` + `soccer_uefa_champs_league`

Update `TEAMS` list in `collect_daily.py` and `final_predict.py` for tournament participants.

---

## Subsection: Tournament Winner Prediction Methodology (from sports-tournament-prediction)

### Multi-Factor Weighted Scoring

```
夺冠概率 =
    阵容实力(25%) × 阵容评分 +
    球员状态(20%) × 球员评分 +
    教练能力(15%) × 教练评分 +
    赛程难度(15%) × 路线评分 +
    历史数据(10%) × 历史评分 +
    博彩共识(10%) × 赔率评分 +
    外部因素(5%) × 外部评分
```

Each sub-score: 0-100 scale. Multiply by weight → weighted contribution.
Sum across factors → raw score. Normalize to probability distribution (all teams sum to ~100%).

### Factor Detail

| Factor | Weight | Key Metrics |
|--------|--------|-------------|
| 阵容实力 | 25% | Depth rating (S/A/B/C), injury tolerance, positional strength, age profile |
| 球员状态 | 20% | Key players, recent club form, injury risk, fatigue (>55 matches = high risk) |
| 教练能力 | 15% | Tournament experience, tactical adaptability, man management, set piece strategy |
| 赛程难度 | 15% | Group difficulty, knockout bracket half, travel distance, rest days |
| 历史数据 | 10% | Past 4 editions weighted, H2H vs bracket opponents, defending champion curse, penalties |
| 博彩共识 | 10% | Cross-bookmaker comparison, divergence signals, odds movement trends |
| 外部因素 | 5% | Host advantage (+10-15%), geopolitical, weather, political unrest |

### Odds Anomaly Detection

Compare 5+ bookmakers for the same market. Teams with max(implied) - min(implied) ≥ 5pp divergence = **anomaly signals** — investigate for information asymmetry.

### Daily Intelligence Collection Pipeline

For tournaments running over weeks, set up automated daily collection:

1. **Build collection script** (Python + RSS/API) fetching from BBC Sport, Guardian, Sky Sports
2. **Filter by tournament keywords**, classify: INJURY / SQUAD / COACHING / ODDS / MATCH / GENERAL
3. **Schedule via cron** — daily at fixed time, `deliver: "local"` to save files
4. **Final compilation job** — one-shot ISO timestamp, `deliver: "origin"`

### Graceful Degradation (Pipeline Must Not Crash)

When any external source fails, pipeline MUST produce output. Wrap each fetch in try/except, load most recent local cache, annotate output with data freshness.

### Multi-Source Weighted Prediction Formula

```
score = baseline_prob × 0.4 + market_odds_implied_prob × 0.3 + news_mention_count × 0.3
```

Rationale: 40% baseline (widest coverage), 30% market (directionally accurate but noisy), 30% news (catches late-breaking signals).

---

## Subsection: Tournament Motivation Analysis (from tournament-motivation-analysis)

### The Motivation Matrix (Group Stage Finals)

| Scenario (Strong Team → Opponent) | Expected Behavior | Probability Trend |
|-----------------------------------|-------------------|-------------------|
| **Locked #1 → Opponent Out (0 pts)** | Low intensity, minimal risk | High Draw Probability |
| **Locked #1 → Opponent Fighting (1-3 pts)** | High volatility; opponent high intensity vs strong team low | Win or Loss (Low Draw) |
| **Fighting for #1 → Fighting for #1** | Maximum intensity both sides | Normal Strength-based Analysis |
| **Locked #1 → Opponent Stable (4+ pts)** | Controlled match, minimal risk | Strong Team Favor (Low Risk) |

### Workflow

1. **Compute Standings**: Points, GF/GA after penultimate matchday
2. **Determine Qualification Status**: Is favorite mathematically qualified? Fighting for top seed?
3. **Analyze Opponent's Incentive**: Need specific result? Already eliminated?
4. **Adjust Prediction**: Apply Motivation Matrix to override/modify baseline

### Pitfalls

- **Reserve Strength Fallacy**: Top team reserves often superior to bottom-tier starters
- **Bracket Manipulation**: Strategic throwing to avoid powerhouse in knockout
- **Home Advantage**: Host motivation usually higher even if qualified

### References

- `references/worldcup-motivation-baseline.md`: Historical baseline from 2014-2022 World Cups.

## References
- `references/odds-api-structure.md` — The Odds API response format details
- `references/rapidapi-quotas.md` — RapidAPI provider limits and fallback logic
- `references/prediction-weights.md` — Weight tuning rationale and backtesting notes
- `references/free-historical-odds.md` — football-data.co.uk Excel, football-data.org API, The Odds API free tier limits comparison