#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MATCHES_FILE = Path("matches.json")
ICS_FILE = Path("worldcup2026.ics")

CAL_NAME = "⚽ World Cup 2026 – Giờ Việt Nam"
CAL_DESC = "FIFA World Cup 2026 – lịch tự cập nhật bởi anh Nguyên."
DEFAULT_TZ = "Asia/Ho_Chi_Minh"

def esc(s):
    s = "" if s is None else str(s)
    return (
        s.replace("\\", "\\\\")
         .replace(";", "\\;")
         .replace(",", "\\,")
         .replace("\n", "\\n")
    )

def fold_line(line):
    out = []
    while len(line.encode("utf-8")) > 73:
        cut = 73
        while cut > 1 and len(line[:cut].encode("utf-8")) > 73:
            cut -= 1
        out.append(line[:cut])
        line = " " + line[cut:]
    out.append(line)
    return "\r\n".join(out)

def add(lines, key, value):
    lines.append(fold_line(f"{key}:{esc(value)}"))

def fmt_dt(dt):
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")

def event_summary(m):
    home = m.get("home") or "TBD"
    away = m.get("away") or "TBD"
    score = (m.get("score") or "").strip()
    status = (m.get("status") or "Scheduled").strip().lower()
    stage = m.get("stage") or ""
    mid = m.get("id") or ""

    match_no = ""
    if mid.startswith("wc2026-m"):
        match_no = str(int(mid.replace("wc2026-m", "")))

    group = ""
    if "Bảng " in stage:
        group = stage.split("Bảng ", 1)[1].split(" ", 1)[0]
        group = f" [{group}]"

    prefix = f"Trận {match_no} ⚽{group} " if match_no else "⚽ "

    if score:
        title = f"{prefix}{home} {score} {away}"
    else:
        title = f"{prefix}{home} vs {away}"

    if status in ["finished", "ended", "fulltime", "ft", "kết thúc"]:
        title += " ✅"
    elif status in ["live", "đang đá"]:
        title += " 🔴 LIVE"

    return title

def event_description(m):
    parts = []

    if m.get("stage"):
        parts.append(f"Vòng/bảng: {m['stage']}")

    if m.get("score"):
        parts.append(f"Tỷ số: {m['score']}")

    if m.get("status"):
        parts.append(f"Trạng thái: {m['status']}")

    scorers = m.get("scorers") or []
    if scorers:
        parts.append("Cầu thủ ghi bàn:")
        for scorer in scorers:
            parts.append(f"- {scorer}")

    if m.get("stadium"):
        parts.append(f"Sân: {m['stadium']}")

    if m.get("city"):
        parts.append(f"Thành phố: {m['city']}")

    if m.get("notes"):
        parts.append(f"Ghi chú: {m['notes']}")

    return "\n".join(parts)

def main():
    matches = json.loads(MATCHES_FILE.read_text(encoding="utf-8"))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Nguyen World Cup 2026//VI",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        fold_line(f"X-WR-CALNAME:{esc(CAL_NAME)}"),
        f"X-WR-TIMEZONE:{DEFAULT_TZ}",
        fold_line(f"X-WR-CALDESC:{esc(CAL_DESC)}"),
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
    ]

    for idx, m in enumerate(matches, start=1):
        tzname = m.get("timezone") or DEFAULT_TZ
        tz = ZoneInfo(tzname)

        start = datetime.strptime(
            f"{m['date']} {m['time']}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=tz)

        duration = int(m.get("duration_minutes") or 120)
        end = start + timedelta(minutes=duration)

        uid = m.get("id") or f"wc2026-{idx:03d}"
        location = m.get("stadium") or m.get("city") or ""

        lines.append("BEGIN:VEVENT")
        add(lines, "UID", f"{uid}@bidikid77-worldcup2026")
        add(lines, "SUMMARY", event_summary(m))
        lines.append(f"DTSTART:{fmt_dt(start)}")
        lines.append(f"DTEND:{fmt_dt(end)}")

        if location:
            add(lines, "LOCATION", location)

        add(lines, "DESCRIPTION", event_description(m))

        status = (m.get("status") or "Scheduled").lower()
        if status in ["cancelled", "canceled", "hủy"]:
            lines.append("STATUS:CANCELLED")
        else:
            lines.append("STATUS:CONFIRMED")

        lines.append("TRANSP:TRANSPARENT")

        lines.extend([
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:World Cup 2026 - trận đấu bắt đầu sau 4 tiếng",
            "TRIGGER:-PT4H",
            "END:VALARM",
        ])

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    ICS_FILE.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"Generated {ICS_FILE} with {len(matches)} matches")

if __name__ == "__main__":
    main()
