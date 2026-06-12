# World Cup 2026 WebCal

Public GitHub Pages calendar for iPhone/Apple Calendar.

Subscribe URL after GitHub Pages is enabled:

```text
webcal://<github-username>.github.io/worldcup2026-webcal/worldcup2026.ics
```

Edit `matches.json`, then run:

```bash
python3 generate_ics.py
```

Commit and push. Calendar clients will refresh from `worldcup2026.ics`.
