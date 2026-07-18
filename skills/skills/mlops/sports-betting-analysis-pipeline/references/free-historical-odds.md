# Free Historical Odds Sources (Verified June 2026)

## football-data.co.uk — World Cup Excel

**URL**: `https://www.football-data.co.uk/WorldCup2026.xlsx`

**Contents**:
- Sheet `WorldCup2026`: 2026 World Cup matches (friendlies/qualifiers played in 2025-2026)
  - Columns: Competition, Home, Away, Date, Time, FT scores, HT scores, Shots, Fouls, Corners, Cards, xG
  - **Odds columns (28-40)**: bet365 H/D/A, Betfair H/D/A, Max H/D/A, Avg H/D/A
- Sheet `WorldCup2026Qualifiers`: Qualifier matches with odds (Max, Avg) + stats
- Sheets `WorldCup2022`, `WorldCup2018`, `WorldCup2014`: Historical tournaments with odds

**Status**: ✅ Free, no API key, no rate limit (direct download)

**Limitation**: **Only finished matches have odds available** — all 2026 World Cup sheet matches show `Finished: 90 minutes`. No upcoming match odds.

**Use case**: Historical backtesting, model training, odds calibration, baseline analysis

---

## football-data.org — Live API (requires registration)

**Registration**: `https://www.football-data.org/client/register` (free, 1 min)

**Free tier**: 10 requests/minute, 1000 requests/day

**Endpoint**: `https://api.football-data.org/v4/competitions/WC/matches` (WC = World Cup)

**Headers**: `X-Auth-Token: <your-token>`

**Odds**: Available in match detail responses for upcoming fixtures

**Status**: ✅ Free registration, has live odds for upcoming matches

**Use case**: Real-time odds for prediction pipeline

---

## The Odds API — Free Tier Limitation

**Verified**: June 2026

| Endpoint | Free Tier | Paid Tier |
|----------|-----------|-----------|
| `/v4/sports/*/events` (schedule) | ✅ 500 req/mo | ✅ |
| `/v4/sports/*/odds` (odds) | ❌ `INVALID_KEY` | ✅ ~$30/mo |

**Bottom line**: Free tier is **schedule only**. For odds, need paid plan or alternative source.

### ⚠️ Additional Critical Limitation: Friendlies vs Tournament Matches

Even if you had paid access to odds endpoints, the `soccer_fifa_world_cup` sport key **mixes friendlies and tournament matches** under the same endpoint. The free tier friendlies (June 11-28 warm-ups) are **not** the real World Cup group stage matches.

| Data | Free Tier | Paid Tier | Notes |
|------|-----------|-----------|-------|
| Winner outright odds | ✅ Works | ✅ | Tournament winner market |
| Tournament match odds | ❌ Returns friendlies | ✅ Real matches | Same sport key, different data |
| Qualifier match odds | ❌ | ✅ | Different sport key |
| Schedule/fixtures | ✅ | ✅ | Use to get match IDs |

**Practical Impact**: You cannot use The Odds API free tier for ANY match-level analysis during the tournament. The match odds returned are for meaningless friendlies with rotated lineups.

---

## Comparison Table

| Source | Cost | Registration | Upcoming Odds | Historical Odds | Rate Limit |
|--------|------|--------------|---------------|-----------------|------------|
| The Odds API | Free tier (schedule only) | Yes | ❌ Free / ✅ Paid | ❌ | 500/mo |
| football-data.org | Free tier | Yes | ✅ | ✅ (paid?) | 1000/day |
| football-data.co.uk | Free | No | ❌ | ✅ Excel | None |
| API-Football (RapidAPI) | Free tier | Yes | ✅ | ✅ | 100/day |
| Oddsble | Free tier | Yes | ✅ Claimed | ? | 500/mo |

---

## Recommendation for Free Pipeline

1. **Historical training**: Download `WorldCup2026.xlsx` + prior World Cup sheets → build baseline model
2. **Live odds (pre-match)**: Register football-data.org token → daily odds collection
3. **Backup**: The Odds API paid if budget allows; otherwise manual odds entry from bookmaker sites