# 🎬 AI Video Dubbing Studio (Python)

Dự án tự động **lồng tiếng video đa ngôn ngữ bằng AI** viết bằng ngôn ngữ **Python**.

Hệ thống tự động thực hiện quy trình khép kín:
1. **Trích xuất âm thanh** từ video gốc (`MoviePy` / `FFmpeg`).
2. **Nhận diện giọng nói & gán mốc thời gian** từng câu (`faster-whisper` ASR).
3. **Dịch phụ đề** sang ngôn ngữ đích (`deep-translator` / Google Translate, hỗ trợ Anh, Việt, Nhật, Hàn, Trung...).
4. **Tạo giọng đọc AI tự nhiên** (`edge-tts` với giọng Hoài My, Nam Minh, Jenny...).
5. **Đồng bộ thời gian & khớp khẩu hình** (`AudioSynchronizer` tự động tăng/giảm tốc độ để khít thời lượng câu thoại gốc).
6. **Hòa âm (Audio Ducking) & Ghép video hoàn thiện**: Giữ lại 15% nhạc nền gốc và xuất video kèm file phụ đề `.srt`.

---

## 📁 Cấu trúc thư mục dự án

```text
studiovdt/
├── config.py                 # Cấu hình tham số, danh sách giọng đọc và ngôn ngữ
├── requirements.txt          # Danh sách thư viện Python cần thiết
├── main.py                   # Giao diện dòng lệnh CLI tiện lợi
├── app.py                    # Giao diện Web UI hiện đại (Streamlit)
├── .gitignore                # Bỏ qua các file rác và video tạm
├── video_dubber/             # Module cốt lõi
│   ├── __init__.py
│   ├── extractor.py          # Trích xuất âm thanh từ video sang WAV mono 16kHz
│   ├── transcriber.py        # Nhận diện giọng nói bằng Whisper
│   ├── translator.py         # Dịch thuật câu thoại
│   ├── tts.py                # Sinh giọng nói bằng Edge-TTS (miễn phí, chất lượng cao)
│   ├── synchronizer.py       # Tinh chỉnh tốc độ, ghép audio khớp mốc thời gian
│   ├── merger.py             # Hòa âm nền và ghép audio mới vào video
│   └── pipeline.py           # Quản lý luồng xử lý toàn bộ quy trình
└── README.md
```

---

## 🛠️ Hướng dẫn cài đặt

### Bước 1: Cài đặt Python & FFmpeg (Dành cho Windows)

Nếu máy tính chưa có Python hoặc FFmpeg, bạn có thể cài nhanh bằng lệnh PowerShell sau:

```powershell
# Cài đặt Python 3.11 hoặc 3.12 qua winget
winget install Python.Python.3.11

# Cài đặt FFmpeg
winget install Gyan.FFmpeg
```

> **Lưu ý**: Sau khi cài xong, hãy khởi động lại terminal hoặc VSCode để nhận lệnh `python` và `ffmpeg`.

### Bước 2: Tạo môi trường ảo và cài đặt thư viện

Mở PowerShell tại thư mục dự án:

```powershell
# Tạo môi trường ảo (khuyến nghị)
python -m venv venv

# Kích hoạt môi trường ảo trên Windows
.\venv\Scripts\activate

# Nâng cấp pip và cài đặt các thư viện
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Tính năng chính

### 1. 🎬 Lồng tiếng Video tự động (Video Dubbing)
- Tự động tách âm thanh từ video.
- Nhận diện lời thoại & tách mốc thời gian bằng **Faster-Whisper**.
- Dịch câu thoại sang ngôn ngữ đích.
- Tự động điều chỉnh tốc độ đọc (time-stretching) để vừa khít khẩu hình và mốc thời gian video gốc.
- Hòa âm nền (Audio Ducking) giữ lại tiếng động và nhạc nền gốc.
- Xuất video hoàn thiện kèm phụ đề `.srt`.

### 2. 🎙️ Chuyển Văn bản sang Âm thanh (Text-to-Speech Studio - Đa giọng đọc)
- Nhập văn bản tùy ý hoặc tải file `.txt`.
- Kho giọng đọc AI Neural đa dạng: Tiếng Việt (Hoài My, Nam Minh), Tiếng Anh (Mỹ, Anh, Úc), Tiếng Trung (Bắc Kinh, Đài Loan, Quảng Đông), Tiếng Nhật, Tiếng Hàn, Pháp, Đức, Thái...
- **Chế độ 1 giọng đọc**: Tinh chỉnh linh hoạt Tốc độ (Speed), Cao độ (Pitch) và Âm lượng (Volume).
- **Chế độ Đa giọng đọc (Multi-Voice Comparison)**: Tạo cùng một đoạn văn bản với nhiều giọng khác nhau để nghe so sánh cạnh nhau và chọn ra giọng ưng ý nhất.
- Nghe trực tiếp trên trình phát tích hợp và tải file `.mp3` về máy.

### Cách 1: Sử dụng giao diện Web trực quan (Streamlit)

Khởi chạy ứng dụng Web trên trình duyệt:

```powershell
streamlit run app.py
```

- Kéo thả video cần lồng tiếng vào khung Upload.
- Chọn ngôn ngữ đích (Ví dụ: Tiếng Việt, Tiếng Anh...).
- Chọn giọng đọc (Nam / Nữ).
- Nhấn **"Bắt đầu lồng tiếng Video"** và xem trực tiếp kết quả.

---

### Cách 2: Sử dụng dòng lệnh CLI

Lồng tiếng một video tiếng Anh sang tiếng Việt với giọng đọc Hoài My:

```powershell
python main.py --input "duong_dan_video.mp4" --target-lang vi --voice vi-VN-HoaiMyNeural
```

Các tùy chọn tham số nâng cao:

```text
Tùy chọn:
  -i, --input PATH            Đường dẫn file video cần lồng tiếng (bắt buộc)
  -t, --target-lang TEXT      Ngôn ngữ đích (mặc định: 'vi')
  -s, --source-lang TEXT      Ngôn ngữ video gốc ('auto' để tự động phát hiện)
  -v, --voice TEXT            Tên giọng đọc TTS (VD: vi-VN-HoaiMyNeural, vi-VN-NamMinhNeural)
  -m, --whisper-model CHOICE  Kích thước model: [tiny|base|small|medium|large-v3]
  --bg-volume FLOAT           Âm lượng nhạc nền gốc (mặc định: 0.15 = 15%)
  -o, --output PATH           Đường dẫn lưu file video kết quả
```

Ví dụ lồng tiếng video tiếng Trung sang tiếng Việt với giọng Nam:

```powershell
python main.py -i "video_tieng_trung.mp4" -s zh -t vi -v vi-VN-NamMinhNeural -o "output/ket_qua.mp4"
```

---

## 🎙️ Danh sách giọng đọc nổi bật

### Giọng Tiếng Việt AI (VieNeu-TTS & Edge-TTS):
| Tên giọng | Động cơ (Engine) | Phong cách |
| :--- | :--- | :--- |
| **🔥 Adam bựa** | **VieNeu Turbo** | **Nam · Bắc · Giọng Review phim hài hước, châm biếm, meme TikTok** |
| **🔥 Adam** | **VieNeu Turbo** | **Nam · Nam · Giọng Tốp Tốp tự nhiên, trầm ấm, cuốn hút** |
| **Trúc Ly** | VieNeu Turbo | Nữ · Bắc tự nhiên, trẻ trung, dí dỏm |
| **Thiện Minh** | VieNeu Turbo | Nam · Bắc kể chuyện, truyền cảm |
| **Mai Anh** | VieNeu Turbo | Nữ · Bắc tin tức, thời sự chuyên nghiệp |
| **Hải Đăng** | VieNeu Turbo | Nam · Bắc tự nhiên, năng động |
| **Thùy Dung** | VieNeu Turbo | Nữ · Nam phát thanh viên |
| **Thiền Tâm Đức** | VieNeu Turbo | Nam · Bắc đọc kinh, triết lý, thiền định |
| **Mỹ Duyên** | VieNeu Turbo | Nữ · Nam đọc truyện ngôn tình diễn cảm |
| **Đức Trí** | VieNeu Turbo | Nam · Nam đọc truyện trinh thám, rùng rợn |
| **Hoài My** | Edge-TTS | Nữ truyền cảm, tin tức |
| **Nam Minh** | Edge-TTS | Nam chuẩn phát thanh viên |
| **Tiếng Anh (Mỹ)** | Nữ | `en-US-JennyNeural` |
| **Tiếng Anh (Mỹ)** | Nam | `en-US-GuyNeural` |
| **Tiếng Nhật** | Nữ | `ja-JP-NanamiNeural` |
| **Tiếng Hàn** | Nữ | `ko-KR-SunHiNeural` |
| **Tiếng Trung** | Nữ | `zh-CN-XiaoxiaoNeural` |

---

## ⚡ Ưu điểm nổi bật của dự án

1. **Hoàn toàn miễn phí**: Sử dụng `faster-whisper`, `deep-translator` và `edge-tts`, không yêu cầu thẻ tín dụng hay API Key trả phí đắt đỏ.
2. **Khớp khẩu hình & thời gian tự động**: Không bị tình trạng audio lồng tiếng nói lấn sang câu sau nhờ thuật toán time-stretching thích ứng.
3. **Giữ lại âm thanh môi trường (Audio Ducking)**: Không cắt cụt video thành khoảng lặng mà vẫn giữ tiếng động cơ, tiếng vỗ tay, tiếng cười hoặc nhạc nền gốc ở mức 15%.
4. **Tự động xuất phụ đề**: Luôn xuất kèm file `.srt` chuẩn mốc thời gian để người dùng có thể nhúng vào video hoặc đăng lên TikTok, YouTube, Facebook Reels.
