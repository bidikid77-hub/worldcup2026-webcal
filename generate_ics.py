#!/usr/bin/env python3
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MATCHES_FILE = Path("matches.json")
ICS_FILE = Path("worldcup2026.ics")

CAL_NAME = "⚽ World Cup 2026 – Giờ Việt Nam"
CAL_DESC = "Lịch FIFA World Cup 2026 tự cập nhật: lịch thi đấu, kết quả, cầu thủ ghi bàn."
DEFAULT_TZ = "Asia/Ho_Chi_Minh"
UID_DOMAIN = "bidikid77-worldcup2026"
FINISHED_STATUSES = {"finished", "ended", "fulltime", "ft", "kết thúc"}
LIVE_STATUSES = {"live", "đang đá"}
CANCELLED_STATUSES = {"cancelled", "canceled", "hủy"}


def esc(s):
    s = "" if s is None else str(s)
    return (
        s.replace("\\", "\\\\")
         .replace(";", "\\;")
         .replace(",", "\\,")
         .replace("\n", "\\n")
    )


def fold_line(line):
    """Fold an iCalendar line at <= 73 UTF-8 bytes to stay under RFC 5545's 75-octet limit."""
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
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def now_utc():
    return datetime.now(timezone.utc)


def to_bold_digits(text):
    table = str.maketrans({
        "0": "𝟎",
        "1": "𝟏",
        "2": "𝟐",
        "3": "𝟑",
        "4": "𝟒",
        "5": "𝟓",
        "6": "𝟔",
        "7": "𝟕",
        "8": "𝟖",
        "9": "𝟗",
    })
    return str(text).translate(table)


def match_number(match_id):
    m = re.match(r"^wc2026-m(\d+)$", str(match_id or ""))
    return str(int(m.group(1))) if m else ""


def group_label(stage):
    if "Bảng " not in (stage or ""):
        return ""
    group = stage.split("Bảng ", 1)[1].split(" ", 1)[0]
    return f" [{group}]"


def event_summary(m):
    home = m.get("home") or "TBD"
    away = m.get("away") or "TBD"
    score = (m.get("score") or "").strip()
    status = (m.get("status") or "Scheduled").strip().lower()
    number = match_number(m.get("id"))
    prefix = f"Trận {number} ⚽{group_label(m.get('stage'))} " if number else "⚽ "

    if score:
        title = f"{prefix}{home} {to_bold_digits(score)} {away}"
    else:
        title = f"{prefix}{home} vs {away}"

    if status in FINISHED_STATUSES:
        title += " ✅"
    elif status in LIVE_STATUSES:
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

    parts.append("Nguồn lịch: https://bidikid77-hub.github.io/worldcup2026-webcal/")
    return "\n".join(parts)


def parse_start(m):
    tzname = m.get("timezone") or DEFAULT_TZ
    try:
        tz = ZoneInfo(tzname)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid timezone for {m.get('id')}: {tzname}") from exc

    try:
        return datetime.strptime(f"{m['date']} {m['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except KeyError as exc:
        raise ValueError(f"Missing required field {exc} in match {m.get('id')}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid date/time in match {m.get('id')}: {m.get('date')} {m.get('time')}") from exc


def validate_matches(matches):
    if not isinstance(matches, list):
        raise ValueError("matches.json must contain a JSON array")

    seen_ids = set()
    errors = []
    for idx, m in enumerate(matches, start=1):
        if not isinstance(m, dict):
            errors.append(f"Match #{idx} is not an object")
            continue

        mid = m.get("id") or f"wc2026-{idx:03d}"
        if mid in seen_ids:
            errors.append(f"Duplicate id: {mid}")
        seen_ids.add(mid)

        for field in ["date", "time", "home", "away"]:
            if not m.get(field):
                errors.append(f"{mid}: missing {field}")

        try:
            parse_start(m)
        except ValueError as exc:
            errors.append(str(exc))

        if m.get("scorers") is not None and not isinstance(m.get("scorers"), list):
            errors.append(f"{mid}: scorers must be a list")

    if errors:
        raise ValueError("Invalid matches.json:\n- " + "\n- ".join(errors))


def load_matches():
    matches = json.loads(MATCHES_FILE.read_text(encoding="utf-8"))
    validate_matches(matches)
    return matches


def build_calendar(matches):
    generated_at = now_utc()
    generated_at_str = fmt_dt(generated_at)
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
        "X-PUBLISHED-TTL:PT24H",
    ]

    for idx, m in enumerate(matches, start=1):
        start = parse_start(m)
        duration = int(m.get("duration_minutes") or 120)
        end = start + timedelta(minutes=duration)
        uid = m.get("id") or f"wc2026-{idx:03d}"
        location = m.get("stadium") or m.get("city") or ""
        status = (m.get("status") or "Scheduled").lower()

        lines.append("BEGIN:VEVENT")
        add(lines, "UID", f"{uid}@{UID_DOMAIN}")
        lines.append(f"DTSTAMP:{generated_at_str}")
        lines.append(f"LAST-MODIFIED:{generated_at_str}")
        add(lines, "SUMMARY", event_summary(m))
        lines.append(f"DTSTART:{fmt_dt(start)}")
        lines.append(f"DTEND:{fmt_dt(end)}")
        if location:
            add(lines, "LOCATION", location)
        add(lines, "DESCRIPTION", event_description(m))
        lines.append("STATUS:CANCELLED" if status in CANCELLED_STATUSES else "STATUS:CONFIRMED")
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
    return "\r\n".join(lines) + "\r\n"


def main():
    matches = load_matches()
    ICS_FILE.write_text(build_calendar(matches), encoding="utf-8")
    print(f"Generated {ICS_FILE} with {len(matches)} matches")


if __name__ == "__main__":
    main()
