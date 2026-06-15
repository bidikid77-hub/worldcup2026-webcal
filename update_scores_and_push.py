#!/usr/bin/env python3
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
MATCHES = BASE / "matches.json"
GEN = BASE / "generate_ics.py"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?limit=100"

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

def fetch():
    with urllib.request.urlopen(ESPN_URL, timeout=30) as r:
        return json.load(r)

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
        old = (m.get("score", ""), m.get("status", ""))
        new = (score, new_status)
        if old != new:
            m["score"] = score
            m["status"] = new_status
            changes.append(f"{m['home']} {score} {m['away']} ({new_status})")

    if not changes:
        print("No score changes.")
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
