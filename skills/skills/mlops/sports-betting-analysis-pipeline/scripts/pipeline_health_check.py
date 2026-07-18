#!/usr/bin/env python3
"""
Pipeline Health Check — Run before match day or prediction generation.
Checks: API quota, data freshness, file integrity, prediction readiness.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path.home() / "worldcup-analysis"
ODDS_FILE = BASE / "odds_data" / "odds_latest.json"
DAILY_DIR = BASE / "daily_collection"
ANALYSIS_FILE = BASE / "reports" / "FINAL_COMPREHENSIVE_ANALYSIS.md"

def check_odds_freshness(max_age_hours=24):
    if not ODDS_FILE.exists():
        return False, "odds_latest.json missing"
    try:
        data = json.loads(ODDS_FILE.read_text())
        ts_str = data.get("timestamp", "")
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        age = datetime.now() - ts
        if age > timedelta(hours=max_age_hours):
            return False, f"odds stale: {age} old (max {max_age_hours}h)"
        match_count = len(data.get("odds_api", {}).get("match_odds", []))
        winner_count = len(data.get("odds_api", {}).get("winner_odds", {}).get("eu", [{}])[0].get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", []))
        return True, f"OK: {match_count} matches, {winner_count} teams with outright odds, age {age}"
    except Exception as e:
        return False, f"odds parse error: {e}"

def check_daily_reports(min_days=3):
    reports = list(DAILY_DIR.glob("report_*.txt"))
    if len(reports) < min_days:
        return False, f"only {len(reports)} daily reports (need {min_days})"
    # Check latest is today or yesterday
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    latest_date = latest.stem.replace("report_", "")
    try:
        latest_dt = datetime.strptime(latest_date, "%Y-%m-%d")
        if (datetime.now().date() - latest_dt.date()).days > 2:
            return False, f"latest report {latest_date} > 2 days old"
    except:
        pass
    return True, f"OK: {len(reports)} reports, latest {latest_date}"

def check_baseline():
    if not ANALYSIS_FILE.exists():
        return False, "FINAL_COMPREHENSIVE_ANALYSIS.md missing"
    content = ANALYSIS_FILE.read_text()
    if "排名" not in content or "概率" not in content:
        return False, "baseline missing probability table"
    return True, "OK: baseline has probability table"

def check_api_quota():
    # Quick test call to The Odds API
    import os, requests
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        cfg = BASE / ".odds_config.json"
        if cfg.exists():
            key = json.loads(cfg.read_text()).get("odds_api_key", "")
    if not key:
        return False, "no API key configured"
    try:
        r = requests.get(
            "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup_winner/odds",
            params={"apiKey": key, "regions": "eu", "markets": "outrights"},
            timeout=10
        )
        if r.status_code == 429:
            return False, "The Odds API: QUOTA EXHAUSTED (429)"
        if r.status_code != 200:
            return False, f"The Odds API: HTTP {r.status_code}"
        remaining = r.headers.get("x-requests-remaining", "unknown")
        return True, f"The Odds API: {remaining} requests remaining"
    except Exception as e:
        return False, f"The Odds API: {e}"

def main():
    checks = [
        ("Odds freshness", check_odds_freshness),
        ("Daily reports", check_daily_reports),
        ("Baseline analysis", check_baseline),
        ("API quota", check_api_quota),
    ]
    
    print("=" * 55)
    print("  World Cup Analysis Pipeline — Health Check")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)
    
    all_ok = True
    for name, fn in checks:
        ok, msg = fn()
        status = "✅" if ok else "❌"
        print(f"  {status} {name}: {msg}")
        if not ok:
            all_ok = False
    
    print("=" * 55)
    if all_ok:
        print("  🎯 Pipeline READY for prediction")
        print("  Run: python3 scripts/final_predict.py")
    else:
        print("  ⚠️  Pipeline ISSUES detected — fix before predicting")
    print("=" * 55)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())