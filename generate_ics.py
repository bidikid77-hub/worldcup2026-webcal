#!/usr/bin/env python3
import json, hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
BASE = Path(__file__).resolve().parent
MATCHES = BASE / 'matches.json'
OUT = BASE / 'worldcup2026.ics'
CAL_NAME = 'World Cup 2026 - Nguyen'
DEFAULT_DURATION_MINUTES = 120

def esc(s):
    s = '' if s is None else str(s)
    return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')

def fold(line):
    b = line.encode('utf-8')
    out = []
    while len(b) > 75:
        cut = 75
        while cut > 0 and (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode('utf-8'))
        b = b' ' + b[cut:]
    out.append(b.decode('utf-8'))
    return '\r\n'.join(out)

def dt_local(date, time, tz):
    return datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo(tz))

def fmt_dt(dt):
    return dt.strftime('%Y%m%dT%H%M%S')

def summary(m):
    h = m.get('home', 'TBD')
    a = m.get('away', 'TBD')
    score = str(m.get('score', '') or '').strip()
    status = str(m.get('status', '') or '').strip().lower()
    raw_id = str(m.get('id') or '')
    num = ''
    if raw_id.startswith('wc2026-m'):
        try:
            num = str(int(raw_id.split('m', 1)[1]))
        except Exception:
            num = ''
    stage = str(m.get('stage') or '')
    group = ''
    if 'Bảng ' in stage:
        group = stage.split('Bảng ', 1)[1].split(' ', 1)[0].strip()
    prefix = f'Trận {num} ' if num else ''
    group_text = f'[{group}] ' if group else ''

    def bold_winner(home, away):
        try:
            n = int(num)
        except Exception:
            return home, away
        if not (1 <= n <= 87):
            return home, away
        winner = str(m.get('winner') or '').strip()
        if winner:
            if winner == home:
                return f'**{home}**', away
            if winner == away:
                return home, f'**{away}**'
        try:
            hs, as_ = [int(x) for x in score.split('-', 1)]
        except Exception:
            return home, away
        if hs > as_:
            return f'**{home}**', away
        if as_ > hs:
            return home, f'**{away}**'
        return home, away

    if score and status in {'ft', 'aet', 'pen'}:
        bh, ba = bold_winner(h, a)
        if status == 'pen' and m.get('winner') and m.get('penalty_score'):
            return f'{prefix}{group_text}{bh} {score} {ba} · **{m["winner"]}** thắng pen {m["penalty_score"]}'
        return f'{prefix}{group_text}{bh} {score} {ba}'
    return f'{prefix}{group_text}{h} vs {a}'

def description(m):
    parts = []
    if m.get('stage'):
        parts.append(f'📌 Vòng: {m["stage"]}')
    if m.get('status'):
        parts.append(f'⏱ Trạng thái: {m["status"]}')
    if m.get('stadium'):
        parts.append(f'🏟 Sân: {m["stadium"]}')
    if m.get('score'):
        parts.append(f'⚽ Tỷ số: {m["score"]}')
    if m.get('penalty_score'):
        parts.append(f'🎯 Luân lưu: {m["penalty_score"]}')
    if m.get('winner'):
        parts.append(f'🏆 Đội thắng: {m["winner"]}')
    scorers = m.get('scorers') or []
    if scorers:
        parts.append('⚽ Cầu thủ ghi bàn:')
        for s in scorers:
            if isinstance(s, dict):
                assist = s.get("assist", "")
                suffix = f' (kiến tạo: {assist})' if assist else ''
                parts.append(f'- {s.get("team", "")}: {s.get("player", "")} {s.get("minute", "")}{suffix}')
            else:
                parts.append(f'- {s}')
    if m.get('notes'):
        parts.append(f'📝 Ghi chú: {m["notes"]}')
    if m.get('tv_channel'):
        parts.append(f'📺 Kênh xem: {m["tv_channel"]}')
    return '\n'.join(parts)

def uid(m):
    raw = m.get('id') or '|'.join([m.get('date',''), m.get('time',''), m.get('home',''), m.get('away',''), m.get('stadium','')])
    return hashlib.sha1(raw.encode()).hexdigest() + '@worldcup2026-nguyen'

def main():
    matches = json.loads(MATCHES.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = [
        'BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Nguyen//World Cup 2026 WebCal//VI',
        'CALSCALE:GREGORIAN','METHOD:PUBLISH',f'X-WR-CALNAME:{esc(CAL_NAME)}','X-WR-TIMEZONE:UTC',
        'REFRESH-INTERVAL;VALUE=DURATION:PT1H','X-PUBLISHED-TTL:PT1H'
    ]
    for m in matches:
        tz = m.get('timezone') or 'UTC'
        start = dt_local(m['date'], m['time'], tz)
        end = start + timedelta(minutes=int(m.get('duration_minutes') or DEFAULT_DURATION_MINUTES))
        loc = ' - '.join(x for x in [m.get('stadium',''), m.get('city','')] if x)
        lines += [
            'BEGIN:VEVENT', f'UID:{uid(m)}', f'DTSTAMP:{now}',
            f'DTSTART;TZID={tz}:{fmt_dt(start)}', f'DTEND;TZID={tz}:{fmt_dt(end)}',
            f'SUMMARY:{esc(summary(m))}', f'LOCATION:{esc(loc)}', f'DESCRIPTION:{esc(description(m))}',
            'STATUS:CONFIRMED', 'END:VEVENT'
        ]
    lines.append('END:VCALENDAR')
    OUT.write_text('\r\n'.join(fold(x) for x in lines) + '\r\n', encoding='utf-8')
    print(f'Wrote {OUT} with {len(matches)} matches')

if __name__ == '__main__':
    main()
