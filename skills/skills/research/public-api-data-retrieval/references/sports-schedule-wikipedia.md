# Sports / Event Schedule Retrieval via Wikipedia API (with timezone conversion)

Pattern that worked for "what match is on at Beijing-time X" — e.g. World Cup
quarter-finals. The Wikipedia `action=parse` API with `prop=wikitext` is far
more reliable than scraping search engines (DuckDuckGo HTML returned empty for
this). Prefer the API path over the browser (browser nav to wikipedia.org timed
out at 120s in testing).

## Why not search engines
- DuckDuckGo HTML (`html.duckduckgo.com/html`) returned empty result snippets in
  this environment — grep on `result__a` / `result__snippet` yielded nothing.
- Direct scraping needs JS/CAPTCHA handling. Wikipedia's `api.php` is clean
  structured JSON.

## Step-by-step (Python via terminal / execute_code)
1. Find the right page + section indices:
   ```python
   params={"action":"parse","page":"2026 FIFA World Cup","prop":"sections",
           "format":"json","formatversion":"2"}
   # look for "Knockout stage" / "Quarterfinals" / "Final" section indices
   ```
2. Fetch the section wikitext (knockout bracket often lives on a dedicated
   "knockout stage" page, pulled in via `{{#lst:...|QF1}}` transclusion):
   ```python
   params={"action":"parse","page":"2026 FIFA World Cup knockout stage",
           "prop":"wikitext","format":"json","formatversion":"2"}
   ```
3. Extract per-match facts with regex on the `football box` template:
   - date: `Start date\|(\d+)\|(\d+)\|(\d+)` -> (Y,M,D)
   - time: `\|time=([^|\n]+)` (e.g. `12:00&nbsp;p.m. [[UTC−07:00|UTC−7]]`)
   - tz:   `UTC[−-]\d+` (venue local offset; US hosts use −4 to −7 in summer)
   - teams/stadium: `team1=`, `team2=`, `stadium=`
   - To anchor on a specific match, search the wikitext for its FIFA
     match-centre ID (e.g. `400021538`) and read `±800` chars around it.
4. Convert local kickoff -> Beijing (UTC+8):
   - Parse the local time + venue UTC offset, then shift to UTC+8.
   - US summer offsets: EDT=UTC−4, CDT=UTC−5, MDT=UTC−6, PDT=UTC−7.
   - Beijing is UTC+8, so add **+12 (EDT) to +15 (PDT)** hours.
   - Example: Foxborough 7/9 16:00 EDT (UTC−4) -> +12h -> Beijing **7/10 04:00**.
   - Example: Inglewood 7/10 12:00 PDT (UTC−7) -> +15h -> Beijing 7/11 03:00.

## Pitfalls
- Bracket tables are split: the summary bracket (with dates) is on the
  "knockout stage" subpage; individual `football box` match details are
  transcluded via `#lst`. Fetch BOTH pages — the parent page only has
  `{{#lst:...|QF2}}` placeholders.
- `time=` fields contain HTML entities (`&nbsp;`, `&p.m.`); strip them before
  parsing. Some QF entries omit `time=` in the bracket but include it in the
  transcluded football box — search the football box, not the bracket.
- Scores are blank pre-kickoff (`|score=` empty) — don't infer results from the
  template.
- Don't hardcode "the match"; locate by FIFA match ID or by team pair to stay
  robust across editions.

## Reusable probe
For a future "what's on at Beijing-time T" sports question, reuse this shape:
find page -> parse sections -> get wikitext -> regex date/time/tz -> convert to
UTC+8. Works for World Cup, Euros, Olympics schedules on Wikipedia.
