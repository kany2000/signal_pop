# RapidAPI Provider Quotas & Fallback Logic

## Providers Used

| Provider | Host | Free Tier | Status |
|----------|------|-----------|--------|
| **free-api-live-football-data** | `free-api-live-football-data.p.rapidapi.com` | ~100-500 req/mo | ❌ Often exhausted early |
| **api-football** | `api-football-v1.p.rapidapi.com` | 100 req/day | Alternative |
| **sportapi7** | `sportapi7.p.rapidapi.com` | Unknown | Tested, limited |

## free-api-live-football-data (Primary Backup)

**Endpoints used**:
- `/football-get-all-leagues` — find WC leagues
- `/football-get-all-matches-by-league` — qualifier matches (league 10195)
- `/football-event-odds` — match odds (1X2)

**Quota behavior**:
- Monthly reset (1st of month)
- 429 response: `{"message":"You have exceeded the MONTHLY quota for Requests on your current plan, BASIC"}`
- No per-day limit, pure monthly
- **Typical exhaustion**: ~June 5-10 for World Cup period (high usage)

**Response format**:
```json
{
  "response": {
    "leagues": [{"id": 10195, "name": "World Cup Qualifiers UEFA", "ccode": "EU"}],
    "matches": [{"id": 12345, "home": {"name": "France"}, "away": {"name": "Netherlands"}}],
    "odds": {
      "odds": {
        "resolvedOddsMarket": {
          "selections": [
            {"name": "1", "oddsDecimal": "1.85"},
            {"name": "X", "oddsDecimal": "3.40"},
            {"name": "2", "oddsDecimal": "4.20"}
          ]
        }
      }
    }
  }
}
```

**Limitations**:
- No outright winner market
- Only qualifier matches (not final tournament)
- Odds from limited bookmakers (mostly UK)

## Fallback Priority Order

```
1. The Odds API (primary) → winner + match odds, reliable quota
2. free-api-live-football-data (backup) → qualifier match odds only
3. api-football (tertiary) → broader coverage, daily limit
4. Manual/scraped → last resort
```

## Quota Checking in Code

```python
def check_quota_rapidapi(key):
    """Test call to verify quota"""
    import requests
    url = "https://free-api-live-football-data.p.rapidapi.com/football-get-all-leagues"
    headers = {"x-rapidapi-key": key, "x-rapidapi-host": "free-api-live-football-data.p.rapidapi.com"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 429:
        return False, "QUOTA_EXHAUSTED"
    return True, r.headers.get("x-ratelimit-remaining", "unknown")
```

## Monitoring Strategy

- Run `scrape_odds.py` weekly to detect 429 early
- Log quota remaining in `odds_data/quota_log.json`
- Alert when `< 50` requests remaining
- Switch to The Odds API exclusively when RapidAPI exhausted

## Cost Considerations

| Provider | Free Tier | Paid Upgrade | Worth It? |
|----------|-----------|--------------|-----------|
| The Odds API | 500/mo | $30/mo (10k) | ✅ Yes — reliable, outright + match |
| RapidAPI free | ~100-500/mo | $10-50/mo | ❌ No — unreliable, limited markets |
| api-football | 100/day | $10/mo | Maybe — if need live scores |

**Recommendation**: Budget $30/mo for The Odds API Starter during tournament. Covers all needs.