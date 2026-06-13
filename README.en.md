# ⚽ World Cup 2026 WebCal

A public **WebCal / ICS calendar** for the **FIFA World Cup 2026**, optimized for viewers in Vietnam.

This repository publishes a calendar through **GitHub Pages**, so users can:

- subscribe on **iPhone / Apple Calendar**
- add it to **Google Calendar**
- use it with **Outlook** and other calendar apps that support `.ics` files

---

## 1) Public links

### Landing page

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/
```

### ICS calendar file

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

### WebCal subscription URL

```text
webcal://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

---

## 2) What the calendar includes

The calendar currently supports:

- **104 World Cup 2026 matches**
- timezone: **Asia/Ho_Chi_Minh**
- match number and group label in the event title, for example:
  - `Trận 1 [A] Mexico 2-0 Nam Phi`
- clean event descriptions with emoji labels:
  - `📌 Vòng:` — round / group stage
  - `⏱ Trạng thái:` — match status
  - `🏟 Sân:` — stadium
  - `⚽ Tỷ số:` — score
  - `⚽ Cầu thủ ghi bàn:` — goal scorers
  - `📺 Kênh xem:` — TV channel
- pre-match reminders through `VALARM`
- automatic updates for **FT / Finished** matches
- goal scorer updates when available from the data source

---

## 3) Repository structure

```text
.
├── README.md             # Vietnamese README
├── README.en.md          # English README
├── index.html            # GitHub Pages landing page
├── matches.json          # source match data
├── generate_ics.py       # ICS generator
└── worldcup2026.ics      # public calendar file
```

---

## 4) Updating the calendar data

Edit `matches.json`, then regenerate the ICS file:

```bash
python3 generate_ics.py
```

The generator will:

- validate the source data
- regenerate `worldcup2026.ics`
- keep the iCalendar output compatible with common calendar clients

Then commit and push:

```bash
git add matches.json worldcup2026.ics README.md README.en.md index.html generate_ics.py
git commit -m "chore: update World Cup calendar"
git push
```

---

## 5) Automatic result updates

This repository is updated by an external cron job that:

- fetches **FT / Finished** matches
- updates scores
- updates goal scorers when available
- regenerates `worldcup2026.ics`
- pushes the latest calendar to GitHub

The public calendar reflects new data after GitHub Pages refreshes.

---

## 6) Use with iPhone / Apple Calendar

Open this link on iPhone:

```text
webcal://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

Then choose **Subscribe** or **Add Calendar**.

---

## 7) Use with Google Calendar

1. Open Google Calendar on the web.
2. Under **Other calendars**, click `+`.
3. Choose **From URL**.
4. Paste this link:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

---

## 8) Use with Outlook

1. Open **Add calendar**.
2. Choose **Subscribe from web**.
3. Paste the public ICS link.

---

## 9) Technical notes

- The `.ics` file follows the iCalendar format.
- Long lines are folded for better compatibility with calendar clients.
- Each match has a stable UID based on its `id`, so clients update existing events instead of creating duplicates.
- `worldcup2026.ics` is generated from `matches.json`; avoid editing the `.ics` file manually if you want persistent changes.

---

## 10) Project goals

This project prioritizes:

- easy subscription
- clean display on mobile calendar apps
- reliable data updates
- stable public hosting through GitHub Pages

If you only want to use the calendar, open the landing page:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/
```

and choose the subscription option that fits your calendar app.
