# The Odds API Response Structure (v4)

## Winner Odds (outrights)
Endpoint: `sports/soccer_fifa_world_cup_winner/odds`

```json
{
  "data": [
    {
      "id": "event_id",
      "sport_key": "soccer_fifa_world_cup_winner",
      "sport_title": "FIFA World Cup Winner",
      "commence_time": "2026-07-19T19:00:00Z",
      "home_team": null,
      "away_team": null,
      "bookmakers": [
        {
          "key": "betfair_ex_eu",
          "title": "Betfair",
          "last_update": "2026-06-10T02:11:07Z",
          "markets": [
            {
              "key": "outrights",
              "last_update": "2026-06-10T02:11:07Z",
              "outcomes": [
                {"name": "Spain", "price": 5.8},
                {"name": "France", "price": 6.2},
                ...
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Key fields**:
- `commence_time`: tournament final date (UTC)
- `bookmakers[].markets[].key`: always `"outrights"` for winner
- `outcomes[].price`: decimal odds (European format)
- Multiple regions: `eu`, `uk`, `us`, `au` — each returns separate bookmaker sets

## Match Odds (1X2)
Endpoint: `sports/soccer_fifa_world_cup/odds`

```json
{
  "data": [
    {
      "id": "match_id",
      "sport_key": "soccer_fifa_world_cup",
      "sport_title": "FIFA World Cup 2026",
      "commence_time": "2026-06-11T19:00:00Z",
      "home_team": "Mexico",
      "away_team": "South Africa",
      "bookmakers": [
        {
          "key": "pinnacle",
          "title": "Pinnacle",
          "last_update": "2026-06-10T02:11:07Z",
          "markets": [
            {
              "key": "h2h",
              "last_update": "2026-06-10T02:11:07Z",
              "outcomes": [
                {"name": "Mexico", "price": 1.41},
                {"name": "Draw", "price": 4.62},
                {"name": "South Africa", "price": 8.77}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**Key fields**:
- `home_team` / `away_team`: team names (exact strings for matching)
- `commence_time`: match kickoff (UTC)
- `markets[].key`: `"h2h"` = 1X2 (home/draw/away)
- `outcomes[].name`: "Home Team", "Draw", "Away Team" — match against `home_team`/`away_team`

## Implied Probability Calculation

```python
def implied_prob(odds_list):
    """odds_list = [1.41, 4.62, 8.77] for 1X2"""
    inv = [1/o for o in odds_list]
    total = sum(inv)
    return [round(i/total*100, 1) for i in inv]

# Pinnacle example: [71.0%, 21.6%, 11.4%] (sum ≈ 103.9% → overround 3.9%)
```

## Consensus Across Bookmakers

```python
def consensus_odds(bookmakers, market_key='h2h'):
    outcomes = {}
    for bm in bookmakers:
        for m in bm['markets']:
            if m['key'] == market_key:
                for o in m['outcomes']:
                    outcomes.setdefault(o['name'], []).append(o['price'])
    return {name: sum(prices)/len(prices) for name, prices in outcomes.items()}

# Returns: {"Mexico": 1.41, "Draw": 4.45, "South Africa": 8.62}
```

## Rate Limits & Quota

| Tier | Requests/Month | Price |
|------|----------------|-------|
| Free | 500 | $0 |
| Starter | 10,000 | $30/mo |
| Pro | 100,000 | $100/mo |

- Check `x-requests-remaining` header in response
- Free tier resets 1st of each month
- Each region (`eu`, `uk`, `us`, `au`) = 1 request
- Winner + match odds = 2 requests per region = 8 requests per full scrape

## Error Responses

```json
// 429 Quota Exceeded
{
  "message": "You have exceeded the monthly quota for Requests on your current plan, FREE. Upgrade at..."
}

// 401 Invalid Key
{
  "message": "Invalid API Key"
}
```

## ⚠️ CRITICAL PITFALL: Free Tier Returns Friendlies, Not Tournament Matches

**Verified June 2026**: The `soccer_fifa_world_cup` endpoint on **free tier** returns **pre-tournament friendlies/warm-up matches only**, NOT the actual World Cup group stage matches.

| What API Returns (Free Tier) | What You Actually Need |
|------------------------------|------------------------|
| Mexico vs South Africa (friendly) | Mexico vs France (WC Group A Matchday 1) |
| Germany vs Curaçao (friendly) | Germany vs Spain (WC Group E Matchday 2) |
| Brazil vs Morocco (friendly) | Brazil vs Serbia (WC Group G Matchday 1) |
| All matches: June 11-28, 2026 | Real WC: June 11 - July 19, 2026 |

**Why this happens**: The API uses the same sport key (`soccer_fifa_world_cup`) for both friendlies and tournament matches, but free tier only has access to the friendlies feed. Paid tier unlocks the actual tournament match odds.

**Impact on Analysis**:
- ❌ Cannot backtest "Matchday 3 water release" pattern with free tier data
- ❌ Match odds are for meaningless friendlies (lineups rotated, no stakes)
- ✅ Winner outright odds (`soccer_fifa_world_cup_winner`) WORK on free tier
- ✅ Schedule/events endpoint works for fixture list

**Workarounds**:
1. **Pay $30/mo** for Starter tier → unlocks real tournament match odds
2. **Use football-data.co.uk** historical Excel (free) for backtesting past tournaments
3. **Use football-data.org** free API (1000 req/day) for live tournament odds
4. **Manual entry** from bookmaker sites for specific matches

**Detection Code**:
```python
def is_real_tournament_match(match, tournament_start="2026-06-11"):
    \"\"\"Filter out friendlies masquerading as tournament matches\"\"\"
    commence = match['commence_time'][:10]
    # Friendlies cluster before tournament start
    if commence < tournament_start:
        return False
    # Check if both teams are in final 48
    wc_teams = set([...])  # load from official squad lists
    return match['home_team'] in wc_teams and match['away_team'] in wc_teams
```