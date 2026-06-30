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
# Cron window requested by user: continue from 13:15 15/06/2026 Asia/Saigon through 20/07/2026.
# Do not re-scan matches before this cutoff; early FT results are already filled.
CUTOFF_UTC = datetime(2026, 6, 14, 17, 0, tzinfo=timezone.utc)  # 00:00 15/06 Asia/Saigon; do not scan previous dates
END_UTC = datetime(2026, 7, 20, 16, 59, 59, tzinfo=timezone.utc)  # end of 20/07 Asia/Saigon

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
    "Austria": "Áo",
    "Jordan": "Jordan",
    "Portugal": "Bồ Đào Nha",
    "Congo DR": "Congo DR",
    "England": "Anh",
    "Croatia": "Croatia",
    "Uzbekistan": "Uzbekistan",
    "Colombia": "Colombia",
}

def norm(name: str) -> str:
    return ALIASES.get(name, name)

def run(cmd):
    return subprocess.run(cmd, cwd=BASE, text=True, capture_output=True, check=False)

def fetch_url(url):
    last = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=12) as r:
                return json.load(r)
        except Exception as e:
            last = e
    raise RuntimeError(f"failed to fetch {url}: {last}")

def event_dt(ev):
    try:
        return datetime.fromisoformat(ev.get("date", "").replace("Z", "+00:00"))
    except Exception:
        return None

def in_window(ev):
    dt = event_dt(ev)
    now = datetime.now(timezone.utc)
    return bool(dt and CUTOFF_UTC <= dt <= min(now, END_UTC))

def fetch():
    """Fetch only matches from cutoff forward, not earlier filled results."""
    now = datetime.now(timezone.utc)
    if now > END_UTC:
        return {"events": []}
    end = min(now, END_UTC)
    events = []
    seen = set()
    day = CUTOFF_UTC
    while day.date() <= end.date():
        data = fetch_url(ESPN_DATED_URL.format(date=day.strftime("%Y%m%d")))
        for ev in data.get("events", []):
            eid = ev.get("id")
            if eid and eid not in seen and in_window(ev):
                seen.add(eid)
                events.append(ev)
        day += timedelta(days=1)
    # include rolling window too, filtered by same cutoff/end window
    data = fetch_url(ESPN_URL)
    for ev in data.get("events", []):
        eid = ev.get("id")
        if eid and eid not in seen and in_window(ev):
            seen.add(eid)
            events.append(ev)
    return {"events": events}

def fetch_summary(event_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={event_id}"
    return fetch_url(url)

def summary_result(data):
    try:
        comp = data["header"]["competitions"][0]
        comps = comp.get("competitors", [])
        home = next((c for c in comps if c.get("homeAway") == "home"), None)
        away = next((c for c in comps if c.get("homeAway") == "away"), None)
        st = comp.get("status", {}).get("type", {})
        if not home or not away:
            return None
        return {
            "home": norm(home["team"].get("displayName", "")),
            "away": norm(away["team"].get("displayName", "")),
            "score": f"{home.get('score', '0')}-{away.get('score', '0')}",
            "completed": bool(st.get("completed")) or not comp.get("liveAvailable", True),
            "status": st.get("detail") or "FT",
        }
    except Exception:
        return None

def extract_scorers(event_id, data=None):
    try:
        data = data or fetch_summary(event_id)
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
        names = {
            (m.get("home"), m.get("away")),
            (m.get("away"), m.get("home")),
            (norm(m.get("home", "")), norm(m.get("away", ""))),
            (norm(m.get("away", "")), norm(m.get("home", ""))),
        }
        for key in names:
            by_key[key] = m

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
        state = status_type.get("state")
        completed = bool(status_type.get("completed"))
        desc = status_type.get("description") or status_type.get("shortDetail") or ""
        event_id = ev.get("id")
        summary = fetch_summary(event_id) if event_id else None
        sres = summary_result(summary) if summary else None
        if completed:
            hscore = str(home.get("score", ""))
            ascore = str(away.get("score", ""))
            new_status = "FT"
        elif sres and sres.get("completed") and sres.get("home") == hname and sres.get("away") == aname:
            hscore, ascore = (sres.get("score") or "-").split("-", 1)
            new_status = "FT"
        elif state == "in":
            hscore = str(home.get("score", ""))
            ascore = str(away.get("score", ""))
            new_status = status_type.get("detail") or desc or "Live"
        else:
            continue
        if hscore == "" or ascore == "":
            continue
        if norm(m.get("home", "")) == hname and norm(m.get("away", "")) == aname:
            score = f"{hscore}-{ascore}"
        elif norm(m.get("home", "")) == aname and norm(m.get("away", "")) == hname:
            # ESPN may present teams opposite to local canonical calendar order.
            # Store score in matches.json home-away order.
            score = f"{ascore}-{hscore}"
        else:
            continue
        scorers = extract_scorers(event_id, summary) if event_id else []
        old = (m.get("score", ""), m.get("status", ""), m.get("scorers") or [])
        new = (score, new_status, scorers)
        if old != new:
            m["score"] = score
            m["status"] = new_status
            if scorers:
                m["scorers"] = scorers
            else:
                m.pop("scorers", None)
            changes.append(f"{m['home']} {score} {m['away']} ({new_status})")

    for m in matches:
        status = str(m.get("status", "") or "").strip().lower()
        if status in {"scheduled", "postponed", "canceled", "cancelled"}:
            dirty = False
            if m.get("score"):
                m["score"] = ""
                dirty = True
            if m.get("scorers"):
                m.pop("scorers", None)
                dirty = True
            if dirty:
                changes.append(f"Sanitized future match: {m['home']} vs {m['away']}")

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
