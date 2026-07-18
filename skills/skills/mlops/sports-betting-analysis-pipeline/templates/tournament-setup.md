# Tournament Setup Template

Copy this directory structure for a new tournament (Euros, Copa America, etc.):

```
<tournament>-analysis/
├── .odds_config.json          # API keys (The Odds API + RapidAPI)
├── odds_data/                 # Created by scrape_all.py
│   └── odds_latest.json
├── daily_collection/          # Created by collect_daily.py (cron)
│   ├── report_YYYY-MM-DD.txt
│   └── raw_YYYY-MM-DD.json
├── reports/
│   └── FINAL_COMPREHENSIVE_ANALYSIS.md  # Manual pre-tournament analysis
└── scripts/
    ├── scrape_all.py          # Adapted from template
    ├── collect_daily.py       # Adapted from template
    ├── final_predict.py       # Adapted from template
    └── pipeline_health_check.py
```

## Adaptation Checklist

### 1. `.odds_config.json`
```json
{
  "odds_api_key": "YOUR_ODDS_API_KEY",
  "rapidapi_key": "YOUR_RAPIDAPI_KEY"
}
```

### 2. `scrape_all.py` — Update sport keys
```python
# World Cup
WINNER_SPORT = "soccer_fifa_world_cup_winner"
MATCH_SPORT = "soccer_fifa_world_cup"

# Euros
WINNER_SPORT = "soccer_uefa_euro_winner"
MATCH_SPORT = "soccer_uefa_euro"

# Copa America
WINNER_SPORT = "soccer_conmebol_copa_america_winner"
MATCH_SPORT = "soccer_conmebol_copa_america"

# Champions League
WINNER_SPORT = "soccer_uefa_champs_league_winner"
MATCH_SPORT = "soccer_uefa_champs_league"
```

### 3. `collect_daily.py` — Update TEAMS and WC_KEYWORDS
```python
TEAMS = [
    "France", "Spain", "Germany", "England", "Italy", "Portugal",
    "Netherlands", "Belgium", "Croatia", "Denmark", "Switzerland",
    # ... tournament participants
]

WC_KEYWORDS = [
    "euro 2024", "european championship", "uefa euro",
    # ... team names, keywords
]
```

### 4. `final_predict.py` — Update TEAMS list and normalize_team mapping
```python
teams_list = [
    "France", "Spain", "Germany", "England", "Italy", "Portugal",
    # ... same as TEAMS above
]

# Add Chinese name mapping if baseline uses Chinese
mapping = {
    "法国": "France", "西班牙": "Spain", "德国": "Germany",
    # ...
}
```

### 5. `FINAL_COMPREHENSIVE_ANALYSIS.md` — Create baseline
Use the same table format:
```markdown
| 排名 | 球队 | 概率 |
|------|------|------|
| 1    | France | 25% |
| 2    | Spain | 20% |
| 3    | Germany | 15% |
...
```

### 6. Cron job for daily collection
```bash
# Add to crontab (runs daily 08:30)
30 8 * * * cd ~/euro2024-analysis && python3 scripts/collect_daily.py
```

## Quick Start Commands

```bash
# 1. Create project dir
mkdir -p ~/euro2024-analysis/{odds_data,daily_collection,reports,scripts}

# 2. Copy scripts from worldcup-analysis and adapt
cp ~/worldcup-analysis/scripts/*.py ~/euro2024-analysis/scripts/

# 3. Edit sport keys in scrape_all.py and team lists in collect_daily.py, final_predict.py

# 4. Add API keys
echo '{"odds_api_key": "xxx", "rapidapi_key": "yyy"}' > ~/euro2024-analysis/.odds_config.json

# 5. Create baseline analysis
vim ~/euro2024-analysis/reports/FINAL_COMPREHENSIVE_ANALYSIS.md

# 6. Test pipeline
cd ~/euro2024-analysis
python3 scripts/scrape_all.py
python3 scripts/collect_daily.py
python3 scripts/final_predict.py

# 7. Add cron for daily collection
crontab -e  # add: 30 8 * * * cd ~/euro2024-analysis && python3 scripts/collect_daily.py
```

## Verification

Run health check before first prediction:
```bash
python3 scripts/pipeline_health_check.py
```