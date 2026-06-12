# World Cup 2026 WebCal

Lịch FIFA World Cup 2026 dạng WebCal/ICS, tối ưu cho người xem ở Việt Nam.

- Link subscribe Apple Calendar/iPhone:

```text
webcal://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

- Link HTTPS cho Google Calendar/Outlook:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

## Tính năng

- 104 trận World Cup 2026 theo giờ Việt Nam (`Asia/Ho_Chi_Minh`).
- Tỷ số nổi bật bằng số Unicode đậm, ví dụ `Mexico 𝟐-𝟎 Nam Phi`.
- Cập nhật trạng thái trận đấu: `Scheduled`, `Live`, `Finished`, `Cancelled`.
- Thêm cầu thủ ghi bàn trong phần mô tả sự kiện.
- Nhắc trước trận 4 tiếng bằng `VALARM`.
- Có landing page trên GitHub Pages để người dùng subscribe dễ hơn.

## Cách cập nhật lịch

Sửa dữ liệu trong `matches.json`, sau đó chạy:

```bash
python3 generate_ics.py
```

Script sẽ:

1. kiểm tra `matches.json` có đúng cấu trúc không;
2. kiểm tra ngày, giờ, timezone, ID trùng;
3. sinh lại `worldcup2026.ics`;
4. thêm các trường đồng bộ như `DTSTAMP`, `LAST-MODIFIED`, `X-PUBLISHED-TTL`.

Sau đó commit và push:

```bash
git add matches.json worldcup2026.ics
git commit -m "chore: update World Cup results"
git push
```

## Cấu trúc dữ liệu

Mỗi trận trong `matches.json` có dạng:

```json
{
  "id": "wc2026-m001",
  "date": "2026-06-12",
  "time": "02:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "home": "Mexico",
  "away": "Nam Phi",
  "stage": "Bảng A - Lượt 1",
  "stadium": "Mexico City",
  "city": "Mexico City",
  "score": "2-0",
  "status": "Finished",
  "scorers": [
    "Mexico: Julián Quiñones 9'",
    "Mexico: Raúl Jiménez 67'"
  ],
  "notes": ""
}
```

## Deploy GitHub Pages

Vào repository trên GitHub:

1. mở `Settings`;
2. chọn `Pages`;
3. mục `Build and deployment` chọn `Deploy from a branch`;
4. chọn branch `main`, folder `/root`;
5. bấm `Save`.

Sau khi GitHub Pages chạy xong, trang public sẽ là:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/
```

## Dùng với ứng dụng lịch

### iPhone / Apple Calendar

Mở link:

```text
webcal://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

Sau đó chọn `Subscribe` hoặc `Add Calendar`.

### Google Calendar

1. Mở Google Calendar trên web.
2. `Other calendars` → `+` → `From URL`.
3. Dán link HTTPS:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

### Outlook

1. `Add calendar`.
2. `Subscribe from web`.
3. Dán link HTTPS của file `.ics`.

## Ghi chú kỹ thuật

- File `.ics` dùng CRLF theo chuẩn iCalendar.
- Dòng dài được fold để tránh lỗi import trên calendar client.
- UID của mỗi trận ổn định theo `id`, giúp calendar client cập nhật sự kiện cũ thay vì tạo trùng.
- Calendar không hỗ trợ in đậm HTML/Markdown trong tiêu đề, nên tỷ số dùng chữ số Unicode đậm.
