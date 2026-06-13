# ⚽ World Cup 2026 WebCal

> English version: [README.en.md](README.en.md)

Lịch **FIFA World Cup 2026** dạng **WebCal / ICS** tối ưu cho người dùng Việt Nam.

Repo này xuất bản lịch công khai qua **GitHub Pages** để có thể:
- subscribe trên **iPhone / Apple Calendar**
- thêm vào **Google Calendar**
- dùng với **Outlook** và các ứng dụng lịch hỗ trợ `.ics`

---

## 1) Public links

### Landing page

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/
```

### ICS calendar

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

### WebCal subscribe URL

```text
webcal://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

---

## 2) Có gì trong lịch

Calendar hiện hỗ trợ:
- **104 trận** World Cup 2026
- múi giờ **Asia/Ho_Chi_Minh**
- tiêu đề có số trận và bảng đấu, ví dụ:
  - `Trận 1 [A] Mexico 2-0 Nam Phi`
- mô tả sự kiện rõ ràng, có emoji:
  - `📌 Vòng:`
  - `⏱ Trạng thái:`
  - `🏟 Sân:`
  - `⚽ Tỷ số:`
  - `⚽ Cầu thủ ghi bàn:`
  - `📺 Kênh xem:`
- nhắc lịch trước trận bằng `VALARM`
- cập nhật kết quả **FT / Finished**
- cập nhật **cầu thủ ghi bàn** cho các trận đã kết thúc khi nguồn dữ liệu có sẵn

---

## 3) Cấu trúc repo

```text
.
├── README.md
├── index.html            # landing page GitHub Pages
├── matches.json          # dữ liệu nguồn từng trận
├── generate_ics.py       # script sinh file .ics
└── worldcup2026.ics      # file lịch public
```

---

## 4) Cách cập nhật dữ liệu

Chỉnh dữ liệu trong `matches.json`, sau đó chạy:

```bash
python3 generate_ics.py
```

Script sẽ:
- kiểm tra dữ liệu đầu vào
- sinh lại `worldcup2026.ics`
- giữ định dạng iCalendar phù hợp cho calendar clients

Sau đó commit và push:

```bash
git add matches.json worldcup2026.ics README.md index.html generate_ics.py
git commit -m "chore: update World Cup calendar"
git push
```

---

## 5) Tự động cập nhật kết quả

Repo này đang dùng cron ngoài repo để:
- lấy các trận **FT / Finished**
- cập nhật tỷ số
- cập nhật cầu thủ ghi bàn
- sinh lại `worldcup2026.ics`
- push lên GitHub

Lịch công khai sẽ tự phản ánh dữ liệu mới sau khi GitHub Pages refresh.

---

## 6) Dùng với iPhone / Apple Calendar

Mở link sau trên iPhone:

```text
webcal://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

Sau đó chọn **Subscribe / Add Calendar**.

---

## 7) Dùng với Google Calendar

1. Mở Google Calendar trên web.
2. Ở mục **Other calendars** chọn `+`.
3. Chọn **From URL**.
4. Dán link:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/worldcup2026.ics
```

---

## 8) Dùng với Outlook

1. Mở **Add calendar**.
2. Chọn **Subscribe from web**.
3. Dán link ICS public.

---

## 9) Ghi chú kỹ thuật

- File `.ics` dùng chuẩn iCalendar.
- Dòng dài được fold để tương thích tốt hơn với calendar clients.
- UID từng trận ổn định theo `id`, giúp client cập nhật đúng event cũ thay vì tạo trùng.
- Nội dung trong `worldcup2026.ics` được sinh từ `matches.json`; không nên sửa tay file `.ics` nếu muốn thay đổi bền vững.

---

## 10) Mục tiêu của repo

Repo này ưu tiên:
- **dễ subscribe**
- **đẹp khi hiển thị trên điện thoại**
- **dễ cập nhật dữ liệu**
- **ổn định khi public cho nhiều người dùng**

Nếu bạn chỉ cần dùng lịch, hãy mở landing page:

```text
https://bidikid77-hub.github.io/worldcup2026-webcal/
```

và bấm nút subscribe phù hợp.