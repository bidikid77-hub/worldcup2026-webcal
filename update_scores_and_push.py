#!/usr/bin/env python3
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path.cwd()
if not (BASE / "matches.json").exists():
    BASE = Path(__file__).resolve().parent
MATCHES = BASE / "matches.json"
GEN = BASE / "generate_ics.py"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?limit=100"
ESPN_DATED_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date}&limit=100"
START_DATE = datetime(2026, 6, 11, tzinfo=timezone.utc)  # 12/6 Asia/Saigon includes 11/6 UTC evening

ALIASES = {
    "Australia": "Australia",
    "Türkiye": "Thổ Nhĩ Kỳ",
    "Turkey": "Thổ Nhĩ Kỳ",
    "Germany": "Đức",
    "Curaçao": "Curaçao",
    "Curacao": "Curaçao",
    "Netherlands": "Hà Lan",
    "Japan": "Nhật Bản",
    "Ivory Coast": "Bờ Biển Ngà",
    "Côte d'Ivoire": "Bờ Biển Ngà",
    "Cote d'Ivoire": "Bờ Biển Ngà",
    "Ecuador": "Ecuador",
    "Tunisia": "Tunisia",
    "Sweden": "Thụy Điển",
    "Spain": "Tây Ban Nha",
    "Cape Verde": "Cape Verde",
    "Belgium": "Bỉ",
    "Egypt": "Ai Cập",
    "Saudi Arabia": "Saudi Arabia",
    "Uruguay": "Uruguay",
    "Iran": "Iran",
    "New Zealand": "New Zealand",
    "France": "Pháp",
    "Senegal": "Senegal",
    "Norway": "Na Uy",
    "Iraq": "Iraq",
    "Argentina": "Argentina",
    "Algeria": "Algeria",
    "Mexico": "Mexico",
    "South Africa": "Nam Phi",
    "Korea Republic": "Hàn Quốc",
    "South Korea": "Hàn Quốc",
    "Czechia": "Czechia",
    "Canada": "Canada",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Bosnia-Herzegovina": "Bosnia-Herzegovina",
    "United States": "USA",
    "USA": "USA",
    "Paraguay": "Paraguay",
    "Qatar": "Qatar",
    "Switzerland": "Thụy Sĩ",
    "Brazil": "Brazil",
    "Morocco": "Morocco",
    "Haiti": "Haiti",
    "Scotland": "Scotland",
}

def norm(name: str) -> str:
    return ALIASES.get(name, name)

def run(cmd):
    return subprocess.run(cmd, cwd=BASE, text=True, capture_output=True, check=False)

def fetch_url(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def fetch():
    """Fetch scoreboard events from 12/6 VN time through current date.

    ESPN default scoreboard is a rolling window and misses earlier FT matches,
    so cron uses dated scoreboards and de-dupes event IDs.
    """
    now = datetime.now(timezone.utc)
    events = []
    seen = set()
    day = START_DATE
    while day.date() <= now.date():
        data = fetch_url(ESPN_DATED_URL.format(date=day.strftime("%Y%m%d")))
        for ev in data.get("events", []):
            eid = ev.get("id")
            if eid and eid not in seen:
                seen.add(eid)
                events.append(ev)
        day += timedelta(days=1)
    # include rolling window too, in case ESPN exposes live edge differently
    data = fetch_url(ESPN_URL)
    for ev in data.get("events", []):
        eid = ev.get("id")
        if eid and eid not in seen:
            seen.add(eid)
            events.append(ev)
    return {"events": events}

def fetch_summary(event_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={event_id}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def extract_scorers(event_id):
    try:
        data = fetch_summary(event_id)
    except Exception:
        return []
    out = []
    seen = set()
    for ev in data.get("keyEvents", []):
        if not ev.get("scoringPlay"):
            continue
        team = norm((ev.get("team") or {}).get("displayName", ""))
        minute = ((ev.get("clock") or {}).get("displayValue") or "").strip()
        participants = ev.get("participants") or []
        player = ""
        if participants:
            player = ((participants[0].get("athlete") or {}).get("displayName") or "").strip()
        if not player:
            short = ev.get("shortText") or ""
            player = short.replace(" Goal - Header", "").replace(" Goal - Volley", "").replace(" Penalty - Scored", "").replace(" Goal", "").strip()
        assist = ""
        if len(participants) > 1:
            assist = ((participants[1].get("athlete") or {}).get("displayName") or "").strip()
        row = {"team": team, "player": player, "minute": minute}
        if assist:
            row["assist"] = assist
        key = (team, player, minute)
        if player and key not in seen:
            seen.add(key)
            out.append(row)
    return out

def main():
    # Keep repo current; continue if pull fails due local changes? cron owns repo, so fail loud.
    pull = run(["git", "pull", "--ff-only"])
    if pull.returncode != 0:
        print("git pull failed", pull.stdout, pull.stderr, file=sys.stderr)
        return 2

    matches = json.loads(MATCHES.read_text(encoding="utf-8"))
    by_key = {}
    for m in matches:
        by_key[(m.get("home"), m.get("away"))] = m
        by_key[(m.get("away"), m.get("home"))] = m

    data = fetch()
    changes = []
    for ev in data.get("events", []):
        comp = ev.get("competitions", [{}])[0]
        status_type = comp.get("status", {}).get("type", {})
        comps = comp.get("competitors", [])
        home = next((c for c in comps if c.get("homeAway") == "home"), None)
        away = next((c for c in comps if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        hname = norm(home["team"].get("displayName", ""))
        aname = norm(away["team"].get("displayName", ""))
        m = by_key.get((hname, aname))
        if not m:
            continue
        hscore = str(home.get("score", "0"))
        ascore = str(away.get("score", "0"))
        score = f"{hscore}-{ascore}"
        state = status_type.get("state")
        completed = bool(status_type.get("completed"))
        desc = status_type.get("description") or status_type.get("shortDetail") or ""
        if completed:
            new_status = "FT"
        elif state == "in":
            new_status = status_type.get("detail") or desc or "Live"
        else:
            continue
        event_id = ev.get("id")
        scorers = extract_scorers(event_id) if event_id else []
        old = (m.get("score", ""), m.get("status", ""), m.get("scorers") or [])
        new = (score, new_status, scorers)
        if old != new:
            m["score"] = score
            m["status"] = new_status
            if scorers:
                m["scorers"] = scorers
            changes.append(f"{m['home']} {score} {m['away']} ({new_status})")

    if not changes:
        return 0

    MATCHES.write_text(json.dumps(matches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gen = run(["python3", str(GEN)])
    if gen.returncode != 0:
        print(gen.stdout, gen.stderr, file=sys.stderr)
        return gen.returncode

    status = run(["git", "status", "--porcelain"])
    if not status.stdout.strip():
        print("No git changes after regeneration.")
        return 0

    run(["git", "add", "matches.json", "worldcup2026.ics"])
    msg = "chore: update World Cup results " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = run(["git", "commit", "-m", msg])
    if commit.returncode != 0:
        print(commit.stdout, commit.stderr, file=sys.stderr)
        return commit.returncode
    push = run(["git", "push", "origin", "main"])
    if push.returncode != 0:
        print(push.stdout, push.stderr, file=sys.stderr)
        return push.returncode

    print("Updated and pushed:")
    for c in changes:
        print("- " + c)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
