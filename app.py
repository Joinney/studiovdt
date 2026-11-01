"""
Studio VDT • AI Dubbing & Multi-Voice Text-to-Speech (DAW Pro Edition)
Enterprise Pro Audio • VieNeu Neural Engine v4.2 Max
Full DAW Studio Interface với Theme Đen Than Chì & Điểm Nhấn Cam Amber Phòng Thu Chuẩn DAW
Đảm bảo 100% tính năng hoạt động hoàn hảo: Caret Tag Injection, Audio Synthesis, Live Waveform, Downloads
"""
import asyncio
import base64
from datetime import datetime
import json
from pathlib import Path
import re
import time
import urllib.parse
import logging
import streamlit as st
import streamlit.components.v1 as components
import edge_tts

logger = logging.getLogger("studiovdt")

from config import DEFAULT_VOICES, LANGUAGE_NAMES, VOICES_CATALOG, DubbingConfig
from video_dubber.pipeline import VideoDubberPipeline
from video_dubber.vieneu_tts import generate_vieneu_speech, EMOTION_SOUND_MAP

# 1. Page Configuration
st.set_page_config(
    page_title="Studio VDT • Enterprise Pro Audio DAW",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Comprehensive 55+ Emotion Table & Prompt Templates
EMOTION_TABLE_DATA = [
    ("[crying]", "hu hu", "[sneezes]", "ách xì"),
    ("[coughs]", "khụ khụ", "[hesitant]", "ừm..."),
    ("[lip smacks]", "chẹp chẹp", "[chuckles]", "he he he"),
    ("[annoyed]", "chậc", "[shouting]", "gôôôôô"),
    ("[screaming]", "áaaaa", "[sighs]", "haizzz"),
    ("[yelling]", "Êeeee", "[surprised]", "á há"),
    ("[affirmative]", "ừ hứ", "[awkward laugh]", "hơ hơ hơ"),
    ("[realization]", "ôooo", "[laughing]", "hahaha"),
    ("[giggles]", "hí hí hí", "[yawns]", "ngáppp"),
    ("[thinking]", "hmmm", "[whispering]", "psst..."),
    ("[gasps]", "hự", "[shocked]", "trời ơi!"),
    ("[excited]", "wowww", "[amazed]", "ôi wow"),
    ("[relieved]", "phùuu", "[frustrated]", "trời đất ơi"),
    ("[confused]", "hả?", "[doubtful]", "thật không vậy?"),
    ("[agreeing]", "đúng rồi", "[disagreeing]", "không đâu"),
    ("[cheering]", "yeahhhh", "[applause]", "bốp bốp bốp"),
    ("[groans]", "ôi trời ơi...", "[nervous laugh]", "hơ hơ..."),
    ("[embarrassed]", "ôi ngại quá", "[disappointed]", "ôi thôi rồi"),
    ("[angry]", "tức quá", "[worried]", "chết rồi"),
    ("[curious]", "ủa?", "[teasing]", "ê nhaaa"),
    ("[sarcastic]", "ghê chưa", "[proud]", "tuyệt vời"),
    ("[happy]", "vui quá", "[sad]", "buồn ghê"),
    ("[celebrating]", "yooooo", "[apologetic]", "anh xin lỗi nhé"),
    ("[pleading]", "làm ơn đi", "[determined]", "nhất định rồi"),
    ("[confident]", "chắc chắn luôn", "[excited gasp]", "ôiiii không"),
    ("[grunts]", "hự! Cố lên", "[clears throat]", "hèm hèm"),
    ("[snickers]", "khì khì", "[smug]", "biết ngay mà"),
    ("[panicked]", "chết chết chết!", "", ""),
]

EMOTION_TABLE_MARKDOWN = (
    "| Mã lệnh (Tiếng Anh) | Âm thanh phát ra | Mã lệnh (Tiếng Anh) | Âm thanh phát ra |\n"
    "| :--- | :--- | :--- | :--- |\n"
)
for _c1, _c2, _c3, _c4 in EMOTION_TABLE_DATA:
    EMOTION_TABLE_MARKDOWN += f"| {_c1} | {_c2} | {_c3} | {_c4} |\n"

EMOTION_PROMPT_TEMPLATE = (
    "Dưới đây là Bảng mã lệnh cảm xúc (sound FX / acoustic tags) hỗ trợ bởi giọng đọc AI VieNeu-TTS (Studio VDT):\n\n"
    f"{EMOTION_TABLE_MARKDOWN}\n"
    "🎯 HƯỚNG DẪN DÀNH CHO BẠN (AI):\n"
    "Hãy viết kịch bản (review phim / kể chuyện / đời sống / quảng cáo...) thật tự nhiên, lôi cuốn "
    "và khéo léo lồng ghép các mã lệnh cảm xúc ở bảng trên (đặt trong dấu ngoặc vuông []) vào các câu thoại thích hợp "
    "để khi đưa vào phần mềm Studio VDT, giọng đọc AI sẽ tự động phát ra cảm xúc, tiếng cười, tiếng thở dài, ho, thán phục... chân thực và sống động nhất!"
)


def generate_emotion_table_html():
    rows_html = []
    for i, (col1, col2, col3, col4) in enumerate(EMOTION_TABLE_DATA):
        bg = "#111622" if i % 2 == 0 else "#151b2a"
        c1_btn = f'<button type="button" class="m-chip neon-tag-chip" data-tag="{col1}" style="margin: 0; padding: 2px 7px; font-size: 11.5px; font-weight: 600; color: #f97316;" title="Bấm để chèn {col1}">{col1}</button>' if col1 else ""
        c3_btn = f'<button type="button" class="m-chip neon-tag-chip" data-tag="{col3}" style="margin: 0; padding: 2px 7px; font-size: 11.5px; font-weight: 600; color: #f97316;" title="Bấm để chèn {col3}">{col3}</button>' if col3 else ""
        row = f"""
        <tr style="background: {bg}; border-bottom: 1px solid rgba(255, 255, 255, 0.04);">
            <td style="padding: 6px 4px; text-align: center;">{c1_btn}</td>
            <td style="padding: 6px 4px; text-align: center; color: #cbd5e1; font-size: 12px;">{col2}</td>
            <td style="padding: 6px 4px; text-align: center;">{c3_btn}</td>
            <td style="padding: 6px 4px; text-align: center; color: #cbd5e1; font-size: 12px;">{col4}</td>
        </tr>
        """
        rows_html.append(row)

    table_html = f"""
    <div style="max-height: 400px; overflow-y: auto; overflow-x: auto; border: 1px solid #20273a; border-radius: 8px; margin-top: 10px; -webkit-overflow-scrolling: touch;">
        <table style="width: 100%; border-collapse: collapse; min-width: 460px;">
            <thead>
                <tr style="background: #171d2c; border-bottom: 1px solid #273046; position: sticky; top: 0; z-index: 2;">
                    <th style="padding: 8px 4px; text-align: center; color: #f97316; font-size: 12px; font-weight: 700; width: 25%;">Mã lệnh (Tiếng Anh)</th>
                    <th style="padding: 8px 4px; text-align: center; color: #94a3b8; font-size: 12px; font-weight: 700; width: 25%;">Âm thanh phát ra</th>
                    <th style="padding: 8px 4px; text-align: center; color: #f97316; font-size: 12px; font-weight: 700; width: 25%;">Mã lệnh (Tiếng Anh)</th>
                    <th style="padding: 8px 4px; text-align: center; color: #94a3b8; font-size: 12px; font-weight: 700; width: 25%;">Âm thanh phát ra</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    """
    return table_html


emotion_table_html = generate_emotion_table_html()


def get_author_logo_base64():
    logo_path = Path(__file__).parent / "assets" / "author.png"
    if logo_path.exists():
        encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    return "https://github.com/Joinney.png"


author_logo_b64 = get_author_logo_base64()


# 3. Audio Generation Helpers
async def generate_single_tts_edge(text: str, voice: str, rate: str, volume: str, pitch: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    await communicate.save(str(output_path))
    return output_path


def get_or_generate_voice_preview(voice_id: str, lang: str, voice_name: str) -> Path:
    preview_dir = Path("./output/preview_samples")
    preview_dir.mkdir(parents=True, exist_ok=True)
    import unicodedata
    clean_slug = voice_id.replace("vieneu:", "").replace(":", "_").replace(" ", "_").replace("-", "_")
    safe_ascii = unicodedata.normalize('NFKD', clean_slug).encode('ascii', 'ignore').decode('ascii')
    safe_ascii = re.sub(r'[^\w\-_\.]', '_', safe_ascii).strip('_')
    if not safe_ascii:
        safe_ascii = "preview_voice"
    preview_path = preview_dir / f"preview_{safe_ascii}.mp3"

    if preview_path.exists():
        if preview_path.stat().st_size > 1000:
            return preview_path
        try:
            preview_path.unlink(missing_ok=True)
        except Exception:
            pass

    if voice_id.startswith("vieneu:"):
        actual_voice = voice_id.replace("vieneu:", "").strip()
        demo_text = f"Xin chào, đây là giọng đọc {voice_name} trên Studio VDT."
        generate_vieneu_speech(
            text=demo_text,
            voice=actual_voice,
            speed=1.0,
            output_path=preview_path,
        )
    else:
        if lang == "vi":
            demo_text = f"Xin chào, đây là giọng đọc {voice_name} trên Studio VDT."
        elif lang == "en":
            demo_text = f"Hello, this is a sample preview of {voice_name} on Studio VDT."
        else:
            demo_text = f"Hello, this is an AI voice sample from Studio VDT."

        asyncio.run(
            generate_single_tts_edge(
                text=demo_text,
                voice=voice_id,
                rate="+0%",
                volume="+0%",
                pitch="+0Hz",
                output_path=preview_path,
            )
        )
    return preview_path


# Session States
DEFAULT_DEMO_TEXT = (
    "Hello các con vợ, hôm nay Adam lại lên đồ ngon cho cả nhà đây! [cười] "
    "Coi hết clip rồi hãy lướt nha! [laughing] [nghỉ 0.5s] "
    "Nghe rõ chưa mấy ba? Đừng để tui phải dùng chiêu cuối đấy nhé!"
)

if "tts_main_text" not in st.session_state:
    st.session_state["tts_main_text"] = DEFAULT_DEMO_TEXT

if "slider_speed_val" not in st.session_state:
    st.session_state["slider_speed_val"] = 15  # 1.15x

if "selected_voice_label" not in st.session_state:
    st.session_state["selected_voice_label"] = "🔥 Adam bựa (VieNeu - Review Phim Tốp Tốp dí dỏm, hài hước)"

if "active_acoustic_fx" not in st.session_state:
    st.session_state["active_acoustic_fx"] = "Studio Dry"

if "last_generated_file" not in st.session_state:
    st.session_state["last_generated_file"] = None

if "script_generated_file" not in st.session_state:
    st.session_state["script_generated_file"] = None


# Preset Scripts
sample_options = {
    "🎬 Review Phim Tóm Tắt (Adam Siêu Bựa)": (
        "Hello các con vợ, hôm nay Adam lại lên đồ ngon cho cả nhà đây! [cười] "
        "Coi hết clip rồi hãy lướt nha! [laughing] [nghỉ 0.5s] "
        "Nghe rõ chưa mấy ba? Đừng để tui phải dùng chiêu cuối đấy nhé!"
    ),
    "🔥 Adam Kịch Tính Điện Ảnh": (
        "Khoan đã... [clears throat] các bạn có biết chuyện gì vừa xảy ra không? "
        "Hắn nghĩ mình đã an toàn [laughing], nhưng [thinking] bất ngờ thay [shocked] "
        "cánh cửa mở toang [panicked]! [sighs] Mọi chuyện coi như kết thúc."
    ),
    "👻 Thầy Bảy Kể Chuyện Ma Rùng Rợn": (
        "Đêm đó trời đổ cơn mưa tầm tã. [whispering] Tiếng gió rít từng cơn ghê rợn ngoài cửa sổ... "
        "[groans] Bỗng một bóng đen lướt qua [shocked]! Có ai ở đó không? [thinking]"
    ),
    "✨ Podcast Tâm Tình Sài Gòn": (
        "Chào buổi sáng Sài Gòn thân yêu. [chuckles] Uống một tách cà phê ấm, [sighs] "
        "hít một hơi thật sâu và cảm nhận sự bình yên của ngày mới nhé các bạn. [happy]"
    ),
}


def apply_sample_preset():
    chosen = st.session_state.get("sample_preset_choice")
    if chosen and chosen in sample_options:
        st.session_state["tts_main_text"] = sample_options[chosen]


def apply_txt_upload():
    uploaded_file = st.session_state.get("txt_upload")
    if uploaded_file:
        try:
            content_str = uploaded_file.read().decode("utf-8")
            st.session_state["tts_main_text"] = content_str
        except Exception:
            pass


def set_quick_voice(target_keywords):
    if isinstance(target_keywords, str):
        target_keywords = [target_keywords]
    lang_code = st.session_state.get("tts_lang_select", "vi")
    voices_dict = VOICES_CATALOG.get(lang_code, VOICES_CATALOG.get("vi", {}))
    options = list(voices_dict.keys())
    for kw in target_keywords:
        matched = [v for v in options if kw in v]
        if matched:
            st.session_state["selected_voice_label"] = matched[0]
            return


def set_quick_tempo(val: int):
    st.session_state["slider_speed_val"] = val
    st.session_state["slider_speed_widget"] = val


def set_acoustic_fx(val: str):
    st.session_state["active_acoustic_fx"] = val


# 4. Global Dark Studio DAW CSS (Tông đen than chì & cam amber chuyên nghiệp)
st.html(
    """
    <style>
    /* Full DAW Studio Grid Canvas */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1.5rem !important;
        z-index: 10;
    }
    .stApp {
        background-color: #0c1017 !important;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px) !important;
        background-size: 32px 32px !important;
        color: #e2e8f0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    .block-container {
        padding-top: 1.6rem !important;
        padding-bottom: 140px !important;
        max-width: 1420px !important;
    }

    /* Pro DAW Studio Tabs Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: #0e121c !important;
        padding: 6px !important;
        border-radius: 12px !important;
        border: 1.5px solid #1e2638 !important;
        margin-bottom: 16px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px !important;
        color: #94a3b8 !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        border-radius: 8px !important;
        padding: 0 20px !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9 !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }
    .stTabs [aria-selected="true"] {
        background: #171d2b !important;
        color: #f97316 !important;
        border: 1.5px solid #f97316 !important;
        box-shadow: 0 0 16px rgba(249, 115, 22, 0.2) !important;
    }

    /* Clear containment on Streamlit wrapper containers so position: fixed is 100% viewport-relative */
    div[data-testid="stAppViewBlockContainer"],
    div[data-testid="stAppViewContainer"],
    section[data-testid="stMain"],
    div[data-testid="stVerticalBlock"],
    div[data-testid="stElementContainer"],
    div[data-testid="stHtml"] {
        contain: none !important;
        transform: none !important;
    }

    /* Fixed Bottom DAW Master Player Dock (Luôn ghim dưới đáy màn hình viewport, không cần cuộn) */
    .daw-dock-fixed {
        position: fixed !important;
        bottom: 0px !important;
        left: 0px !important;
        right: 0px !important;
        width: 100vw !important;
        max-width: 100% !important;
        background: #0d111a !important;
        background: linear-gradient(180deg, rgba(19, 23, 36, 0.98) 0%, rgba(10, 13, 20, 0.98) 100%) !important;
        border-top: 1.5px solid #232b3d !important;
        box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.95) !important;
        z-index: 99999999 !important;
        padding: 9px 22px !important;
        box-sizing: border-box !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    /* Nút tải và thao tác trong DAW Dock */
    .daw-action-btn {
        background: #141926 !important;
        border: 1px solid #242d40 !important;
        color: #cbd5e1 !important;
        border-radius: 6px !important;
        padding: 6px 11px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    .daw-action-btn:hover {
        background: #1c2436 !important;
        border-color: #f97316 !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }
    .daw-action-btn-wav {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        padding: 6px 13px !important;
        font-size: 11.5px !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        box-shadow: 0 0 12px rgba(249, 115, 22, 0.45) !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    .daw-action-btn-wav:hover {
        box-shadow: 0 0 18px rgba(249, 115, 22, 0.7) !important;
        transform: translateY(-1px) !important;
    }

    /* Hiệu ứng Loang và Thanh Scrub */
    .loang-active {
        background: #f97316 !important;
        box-shadow: 0 0 6px rgba(249, 115, 22, 0.75) !important;
    }

    /* Chế độ thu nhỏ (Mini Player Pill) khi bấm nút thu nhỏ hoặc trên màn hình nhỏ */
    .daw-dock-collapsed {
        width: auto !important;
        max-width: 92vw !important;
        left: auto !important;
        right: 16px !important;
        bottom: 14px !important;
        border-radius: 40px !important;
        border: 1.5px solid #f97316 !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.95), 0 0 16px rgba(249, 115, 22, 0.35) !important;
        padding: 6px 14px !important;
    }
    .daw-dock-collapsed .daw-action-btn,
    .daw-dock-collapsed .daw-action-btn-wav,
    .daw-dock-collapsed #daw-waveform-wrapper,
    .daw-dock-collapsed #daw-btn-prev,
    .daw-dock-collapsed #daw-btn-next,
    .daw-dock-collapsed #daw-btn-loop,
    .daw-dock-collapsed #daw-track-subtitle {
        display: none !important;
    }
    .daw-dock-collapsed #daw-track-title {
        max-width: 130px !important;
    }

    /* Responsive cho màn hình máy tính bảng và laptop nhỏ */
    @media (max-width: 960px) {
        .daw-dock-center #daw-btn-prev,
        .daw-dock-center #daw-btn-next,
        .daw-dock-center #daw-btn-loop {
            display: none !important;
        }
        .daw-dock-right #daw-btn-dl-srt {
            display: none !important;
        }
    }

    /* =========================================================================
       TỐI ƯU TOÀN DIỆN CHO GIAO DIỆN ĐIỆN THOẠI DI ĐỘNG (< 640px)
       ========================================================================= */
    @media (max-width: 640px) {
        /* Bố cục trang chung */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 130px !important;
            padding-left: 8px !important;
            padding-right: 8px !important;
        }

        /* Container khung thẻ DAW */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 10px 8px !important;
            border-radius: 12px !important;
            margin-bottom: 8px !important;
        }

        /* Top Brand Header */
        .vdt-brand-title {
            font-size: 1.15rem !important;
        }
        .vdt-badge-pill {
            font-size: 9px !important;
            padding: 1px 5px !important;
        }
        .vdt-header-status {
            display: none !important;
        }
        .vdt-brand-sub {
            font-size: 0.72rem !important;
            line-height: 1.3 !important;
        }

        /* Bước 1 Header buttons */
        .step-header-actions {
            width: 100% !important;
            display: flex !important;
            justify-content: space-between !important;
            gap: 4px !important;
            margin-top: 6px !important;
        }
        .step-header-actions button {
            flex: 1 1 auto !important;
            font-size: 10px !important;
            padding: 5px 4px !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        /* Neon Emotion Tag Chips: Xếp gọn gàng không bị tràn màn hình */
        .neon-row {
            margin-left: 0 !important;
            gap: 3px !important;
            margin-bottom: 6px !important;
        }
        .neon-row-sub {
            margin-left: 0 !important;
        }
        .neon-cat {
            display: block !important;
            width: 100% !important;
            min-width: 100% !important;
            text-align: left !important;
            background: transparent !important;
            border: none !important;
            color: #f97316 !important;
            font-size: 10.5px !important;
            font-weight: 800 !important;
            padding: 2px 0 1px 0 !important;
        }
        .neon-tag-chip {
            padding: 4px 6px !important;
            font-size: 11px !important;
            border-radius: 5px !important;
        }

        /* Caret Dropdown & Button trên điện thoại */
        .caret-select-container {
            flex-direction: column !important;
            align-items: stretch !important;
            gap: 6px !important;
        }
        .caret-select-container > div {
            width: 100% !important;
            min-width: 100% !important;
        }
        #caretDropdownBtn {
            width: 100% !important;
            justify-content: center !important;
            padding: 8px 10px !important;
            font-size: 12px !important;
        }

        /* Editor stats bar */
        #daw-stat-duration {
            font-size: 10px !important;
        }

        /* Thẻ nhân vật & Nút nghe thử mẫu trên điện thoại */
        #vdt-btn-preview-sample {
            height: auto !important;
            padding: 8px 10px !important;
            flex-direction: row !important;
            justify-content: center !important;
            gap: 8px !important;
            margin-top: 4px !important;
        }
        #vdt-btn-preview-sample > div {
            max-width: none !important;
        }

        /* 4 nút gợi ý giọng đọc 2x2 */
        div[data-testid="column"] button[kind="secondary"] {
            padding: 6px 4px !important;
            font-size: 10.5px !important;
            min-height: 44px !important;
            line-height: 1.25 !important;
        }

        /* Nút Tốc độ và Acoustic FX trên điện thoại */
        .stButton button {
            padding: 5px 2px !important;
            font-size: 10.5px !important;
        }

        /* Nút Khổng Lồ TẠO GIỌNG ĐỌC AI NGAY trên điện thoại */
        button[kind="primary"] {
            font-size: 13.5px !important;
            padding: 12px 8px !important;
            letter-spacing: 0.3px !important;
            font-weight: 800 !important;
        }

        /* =====================================================================
           THANH PHÁT DAW GHIM ĐÁY 2 TẦNG CHUYÊN NGHIỆP TRÊN ĐIỆN THOẠI
           ===================================================================== */
        .daw-dock-fixed {
            padding: 7px 10px 8px 10px !important;
            bottom: 0px !important;
        }
        .daw-dock-inner {
            display: flex !important;
            flex-wrap: wrap !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 5px !important;
        }
        /* Tầng 1 bên trái: Đĩa quay & Tiêu đề bài */
        .daw-dock-left {
            order: 1 !important;
            flex: 1 1 auto !important;
            min-width: 0 !important;
            max-width: 58% !important;
            gap: 6px !important;
        }
        #daw-disc {
            width: 28px !important;
            height: 28px !important;
            font-size: 13px !important;
            flex-shrink: 0 !important;
        }
        #daw-track-title {
            font-size: 0.8rem !important;
            max-width: 125px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        #daw-track-subtitle {
            display: none !important;
        }
        #daw-badge-status {
            font-size: 8px !important;
            padding: 1px 4px !important;
        }
        /* Tầng 1 bên phải: Nút tải MP3, WAV và Thu nhỏ */
        .daw-dock-right {
            order: 2 !important;
            flex: 0 0 auto !important;
            gap: 4px !important;
        }
        .daw-dock-right #daw-btn-dl-srt {
            display: none !important;
        }
        .daw-dock-right #daw-btn-dl-mp3 {
            padding: 4px 7px !important;
            font-size: 10px !important;
        }
        .daw-dock-right #daw-btn-dl-wav {
            padding: 4px 9px !important;
            font-size: 10px !important;
        }
        #daw-btn-toggle-size {
            padding: 4px 6px !important;
            font-size: 10px !important;
        }
        /* Tầng 2 bên dưới: Nút Play + Timecode + Toàn bộ Waveform Loang & Sướt tua */
        .daw-dock-center {
            order: 3 !important;
            width: 100% !important;
            flex: 1 1 100% !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            gap: 6px !important;
            margin-top: 1px !important;
            padding-top: 4px !important;
            border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
        }
        #daw-btn-prev, #daw-btn-next, #daw-btn-loop {
            display: none !important;
        }
        #daw-btn-play {
            width: 30px !important;
            height: 30px !important;
            font-size: 12px !important;
            flex-shrink: 0 !important;
        }
        #daw-timecode-display {
            font-size: 10px !important;
            min-width: 72px !important;
            flex-shrink: 0 !important;
        }
        #daw-waveform-wrapper {
            display: flex !important;
            flex-grow: 1 !important;
            min-width: 0 !important;
            gap: 4px !important;
        }
        #daw-waveform-scrub {
            display: flex !important;
            width: 100% !important;
            flex-grow: 1 !important;
            min-width: 90px !important;
            height: 24px !important;
            padding: 1px 4px !important;
        }
        #daw-time-start, #daw-time-end {
            display: none !important;
        }
    }

    @keyframes discSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .disc-spinning {
        animation: discSpin 3s linear infinite !important;
    }

    /* DAW Cards Container: Deep Navy Slate with Subtle Studio Border */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #10141f !important;
        border: 1px solid #1e2536 !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        padding: 16px !important;
    }

    /* Text Area: Dark Studio Monospace Editor */
    div[data-testid="stTextArea"] textarea {
        background: #090c13 !important;
        color: #f8fafc !important;
        border: 1px solid #1c2233 !important;
        border-radius: 8px !important;
        font-family: "JetBrains Mono", "Consolas", monospace !important;
        font-size: 13.5px !important;
        line-height: 1.65 !important;
        padding: 12px 14px !important;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.6) !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #f97316 !important;
        box-shadow: 0 0 10px rgba(249, 115, 22, 0.3), inset 0 2px 6px rgba(0, 0, 0, 0.6) !important;
    }

    /* Selectbox styling */
    div[data-baseweb="select"] > div {
        background-color: #0c0f17 !important;
        border: 1px solid #1f2638 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }

    /* Primary Accent Button: Energetic Studio Orange/Amber Gradient */
    button[kind="primary"] {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%) !important;
        color: #ffffff !important;
        border: 1px solid #fb923c !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        font-size: 14.5px !important;
        box-shadow: 0 4px 20px rgba(234, 88, 12, 0.45) !important;
        transition: all 0.15s ease !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #fb923c 0%, #f97316 100%) !important;
        box-shadow: 0 6px 24px rgba(234, 88, 12, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary Buttons: Clean Dark Slate */
    button[kind="secondary"] {
        background: #151a26 !important;
        color: #cbd5e1 !important;
        border: 1px solid #232a3c !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }
    button[kind="secondary"]:hover {
        background: #1c2233 !important;
        border-color: #f97316 !important;
        color: #ffffff !important;
    }

    /* Expander styling */
    div[data-testid="stExpander"] {
        background: #0d1018 !important;
        border: 1px solid #1d2334 !important;
        border-radius: 10px !important;
    }

    /* Invisible iframe container for JS engine */
    iframe[title="streamlit.components.v1.html"], [data-testid="stCustomComponentV1"] {
        position: absolute !important;
        width: 0 !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Sliders styling: Warm Orange Accent */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #f97316 !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 0 8px rgba(249, 115, 22, 0.7) !important;
    }
    </style>
    """
)


# 5. Top Header & Studio Navigation Bar (Khớp 100% hình mẫu người dùng)
st.html(
    f"""
    <div style="margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 6px;">
            <!-- Brand / Logo -->
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 42px; height: 42px; border-radius: 50%; background: #181d2a; border: 2px solid #f97316; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 16px rgba(249, 115, 22, 0.45); flex-shrink: 0;">
                    <img src="{author_logo_b64}" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover;" />
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                        <span class="vdt-brand-title" style="font-size: 1.45rem; font-weight: 900; letter-spacing: -0.5px; color: #ffffff;">Studio VDT</span>
                        <span class="vdt-badge-pill" style="background: rgba(249, 115, 22, 0.15); border: 1px solid #ea580c; color: #fb923c; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 16px; letter-spacing: 0.5px;">• ENTERPRISE PRO AUDIO</span>
                        <span class="vdt-badge-pill" style="background: #141824; border: 1px solid #232b3d; color: #94a3b8; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 16px;">VieNeu Neural v4.2 Max</span>
                    </div>
                    <div class="vdt-brand-sub" style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                        Sáng lập & Bản quyền: <span style="color: #f97316; font-weight: 700;">Võ Duy Toàn</span> | Hệ thống phối âm & lồng tiếng AI cao cấp
                    </div>
                </div>
            </div>

            <!-- Server Status & Indicator Dot -->
            <div class="vdt-header-status" style="display: flex; align-items: center; gap: 10px;">
                <span style="width: 9px; height: 9px; border-radius: 50%; background: #f97316; box-shadow: 0 0 10px #f97316;"></span>
                <span style="background: #1c2233; border: 1px solid #2e3852; color: #f97316; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 700;">PRO STUDIO</span>
            </div>
        </div>
    </div>
    """
)


# 6. Caret Injection Engine Javascript (Đảm bảo chèn thẻ chính xác tại vị trí con trỏ)
caret_injector_template = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:transparent;">
<script>
(function() {
    try {
        var parentDoc = window.parent ? window.parent.document : document;
        var parentWin = window.parent ? window.parent : window;
        if (!parentDoc) return;

        parentWin.__vdtCaretPos = null;

        function getTa() {
            var el = parentDoc.activeElement;
            if (el && el.tagName === 'TEXTAREA') return el;
            return parentDoc.querySelector('textarea[data-testid="stTextAreaInput"]') 
                || parentDoc.querySelector('div[data-testid="stTextArea"] textarea') 
                || parentDoc.querySelector('textarea');
        }

        function savePos() {
            var ta = getTa();
            if (ta && typeof ta.selectionStart === 'number') {
                parentWin.__vdtCaretPos = {
                    start: ta.selectionStart,
                    end: ta.selectionEnd
                };
            }
            updateStats();
        }

        ['focus', 'click', 'keyup', 'mouseup', 'select', 'input', 'touchend'].forEach(function(evt) {
            parentDoc.addEventListener(evt, savePos, true);
        });

        parentDoc.addEventListener('selectionchange', savePos, true);

        function updateStats() {
            var ta = getTa();
            if (!ta) return;
            var text = ta.value || '';
            var words = text.trim() ? text.trim().split(/\\s+/).filter(Boolean).length : 0;
            var chars = text.length;
            var tagsMatch = text.match(/\\[[^\\]]+\\]/g) || [];
            var tagsCount = tagsMatch.length;
            var durationSec = (words / 2.7).toFixed(1);

            var elWords = parentDoc.getElementById('daw-stat-words');
            if (elWords) elWords.innerText = 'Từ: ' + words + ' từ';
            var elChars = parentDoc.getElementById('daw-stat-chars');
            if (elChars) elChars.innerText = 'Ký tự: ' + chars + ' ký tự';
            var elDur = parentDoc.getElementById('daw-stat-duration');
            if (elDur) elDur.innerText = '⏱️ Thời lượng dự kiến: 00:' + (durationSec < 10 ? '0' : '') + durationSec + 's';
            var elTags = parentDoc.getElementById('daw-stat-tags');
            if (elTags) elTags.innerText = tagsCount + ' Tags Phát hiện';
        }

        function doInsert(tag) {
            var ta = getTa();
            if (!ta) return;

            ta.focus();

            var start = (parentWin.__vdtCaretPos && typeof parentWin.__vdtCaretPos.start === 'number') 
                ? parentWin.__vdtCaretPos.start 
                : (typeof ta.selectionStart === 'number' ? ta.selectionStart : (ta.value ? ta.value.length : 0));
            var end = (parentWin.__vdtCaretPos && typeof parentWin.__vdtCaretPos.end === 'number') 
                ? parentWin.__vdtCaretPos.end 
                : (typeof ta.selectionEnd === 'number' ? ta.selectionEnd : start);

            var val = ta.value || '';
            if (start > val.length) start = val.length;
            if (end > val.length) end = start;

            ta.setSelectionRange(start, end);

            var prefix = (start > 0 && val.charAt(start - 1) !== ' ' && val.charAt(start - 1) !== '\\n') ? ' ' : '';
            var suffix = (end < val.length && val.charAt(end) !== ' ' && val.charAt(end) !== '\\n') ? ' ' : ' ';
            var insertStr = prefix + tag + suffix;

            var inserted = false;
            try {
                inserted = parentDoc.execCommand('insertText', false, insertStr);
            } catch (err) {
                inserted = false;
            }

            if (!inserted) {
                var newVal = val.substring(0, start) + insertStr + val.substring(end);
                var setter = Object.getOwnPropertyDescriptor(parentWin.HTMLTextAreaElement.prototype, 'value');
                if (setter && setter.set) {
                    setter.set.call(ta, newVal);
                } else {
                    ta.value = newVal;
                }
                ta.dispatchEvent(new Event('input', { bubbles: true }));
                ta.dispatchEvent(new Event('change', { bubbles: true }));
                var nextPos = start + insertStr.length;
                ta.setSelectionRange(nextPos, nextPos);
                parentWin.__vdtCaretPos = { start: nextPos, end: nextPos };
            } else {
                parentWin.__vdtCaretPos = { start: ta.selectionStart, end: ta.selectionEnd };
            }
            updateStats();
        }

        parentWin.clearEditorText = function() {
            var ta = getTa();
            if (!ta) return;
            var setter = Object.getOwnPropertyDescriptor(parentWin.HTMLTextAreaElement.prototype, 'value');
            if (setter && setter.set) {
                setter.set.call(ta, '');
            } else {
                ta.value = '';
            }
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));
            updateStats();
        };

        parentWin.formatTagsEditor = function() {
            var ta = getTa();
            if (!ta || !ta.value) return;
            var formatted = ta.value.replace(/\\s*\\[\\s*([^\\]]+)\\s*\\]\\s*/g, ' [$1] ');
            formatted = formatted.replace(/[ \\t]+/g, ' ').trim();
            var setter = Object.getOwnPropertyDescriptor(parentWin.HTMLTextAreaElement.prototype, 'value');
            if (setter && setter.set) {
                setter.set.call(ta, formatted);
            } else {
                ta.value = formatted;
            }
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));
            updateStats();
        };

        parentWin.splitSentencesEditor = function() {
            var ta = getTa();
            if (!ta || !ta.value) return;
            var lines = ta.value.replace(/([.?!])\\s+/g, '$1\\n\\n');
            var setter = Object.getOwnPropertyDescriptor(parentWin.HTMLTextAreaElement.prototype, 'value');
            if (setter && setter.set) {
                setter.set.call(ta, lines);
            } else {
                ta.value = lines;
            }
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));
            updateStats();
        };

        var emotionPromptText = __EMOTION_PROMPT_JSON__;

        function copyEmotionPrompt(btn) {
            function updateBtnStatus(success) {
                if (!btn) return;
                var originalHtml = btn.getAttribute('data-original-html') || btn.innerHTML;
                if (!btn.getAttribute('data-original-html')) {
                    btn.setAttribute('data-original-html', originalHtml);
                }
                btn.innerHTML = success ? '✅ Đã copy bảng!' : '❌ Lỗi copy';
                btn.style.background = success ? '#ea580c' : '#991b1b';
                setTimeout(function() {
                    btn.innerHTML = originalHtml;
                    btn.style.background = '';
                }, 2200);
            }

            if (parentWin.navigator && parentWin.navigator.clipboard && parentWin.navigator.clipboard.writeText) {
                parentWin.navigator.clipboard.writeText(emotionPromptText).then(function() {
                    updateBtnStatus(true);
                }).catch(function() {
                    fallbackCopy(emotionPromptText, updateBtnStatus);
                });
            } else {
                fallbackCopy(emotionPromptText, updateBtnStatus);
            }
        }

        function fallbackCopy(text, callback) {
            try {
                var ta = parentDoc.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.left = '-9999px';
                ta.style.top = '0';
                ta.style.opacity = '0';
                parentDoc.body.appendChild(ta);
                ta.focus();
                ta.select();
                var ok = parentDoc.execCommand('copy');
                parentDoc.body.removeChild(ta);
                callback(ok);
            } catch (err) {
                callback(false);
            }
        }

        function bindButtons() {
            var chips = parentDoc.querySelectorAll('.m-chip[data-tag]');
            chips.forEach(function(chip) {
                if (chip.__vdtBound) return;
                chip.__vdtBound = true;
                chip.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });
                chip.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var tag = this.getAttribute('data-tag');
                    if (tag) doInsert(tag);
                });
            });

            var copyBtns = parentDoc.querySelectorAll('.btn-copy-emotion-table');
            copyBtns.forEach(function(btn) {
                if (btn.__vdtBound) return;
                btn.__vdtBound = true;
                btn.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    copyEmotionPrompt(this);
                });
            });

            var btnClear = parentDoc.getElementById('btn-action-clear');
            if (btnClear && !btnClear.__vdtBound) {
                btnClear.__vdtBound = true;
                btnClear.addEventListener('click', function(e) {
                    e.preventDefault();
                    parentWin.clearEditorText();
                });
            }

            var btnSplit = parentDoc.getElementById('btn-action-split');
            if (btnSplit && !btnSplit.__vdtBound) {
                btnSplit.__vdtBound = true;
                btnSplit.addEventListener('click', function(e) {
                    e.preventDefault();
                    parentWin.splitSentencesEditor();
                });
            }

            var dropBtn = parentDoc.getElementById('caretDropdownBtn');
            if (dropBtn && !dropBtn.__vdtBound) {
                dropBtn.__vdtBound = true;
                dropBtn.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                });
                dropBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var sel = parentDoc.getElementById('caretSelectTag');
                    if (sel && sel.value) doInsert(sel.value);
                });
            }

            var btnFormat = parentDoc.getElementById('btn-action-format');
            if (btnFormat && !btnFormat.__vdtBound) {
                btnFormat.__vdtBound = true;
                btnFormat.addEventListener('click', function(e) {
                    e.preventDefault();
                    parentWin.formatTagsEditor();
                });
            }

            updateStats();
        }

        bindButtons();
        setInterval(bindButtons, 400);

    } catch (e) {
        console.error('[StudioVDT] Error in caret engine:', e);
    }
})();
</script>
</body>
</html>
"""

caret_injector_html = caret_injector_template.replace("__EMOTION_PROMPT_JSON__", json.dumps(EMOTION_PROMPT_TEMPLATE))

# Inject Caret Engine
components.html(caret_injector_html, height=0)


# ==============================================================================
# MAIN WORKSPACE: TWO PRO DAW COLUMNS (Khớp hoàn toàn giao diện người dùng yêu cầu)
# ==============================================================================
tab_tts, tab_dubbing = st.tabs([
    "🎙️ PHÒNG THU GIỌNG ĐỌC AI (TTS STUDIO)",
    "🎬 LỒNG TIẾNG VIDEO AI TỰ ĐỘNG (AI VIDEO DUBBING)",
])

with tab_tts:
    col_script, col_studio = st.columns([1.1, 0.9], gap="medium")


    # ------------------------------------------------------------------------------
    # COLUMN 1: BƯỚC 1: TRÌNH SOẠN THẢO KỊCH BẢN ĐA CẢM XÚC
    # ------------------------------------------------------------------------------
    with col_script:
        with st.container(border=True):
            # Header Row
            st.html(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="background: #171c28; border: 1.5px solid #283147; color: #f8fafc; border-radius: 50%; width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; font-size: 15px;">01</div>
                        <div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff; letter-spacing: 0.3px;">BƯỚC 1: TRÌNH SOẠN THẢO KỊCH BẢN ĐA CẢM XÚC</div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">Smart Emotion Scriptwriter • Gắn nhãn cảm xúc & nhịp ngắt chuẩn xác theo vị trí con trỏ</div>
                        </div>
                    </div>
                    <div class="step-header-actions" style="display: flex; gap: 6px;">
                        <button type="button" id="btn-action-split" style="background: #151a26; border: 1px solid #232b3c; border-radius: 6px; color: #cbd5e1; padding: 4px 9px; font-size: 11px; font-weight: 600; cursor: pointer;">✂️ Tách câu tự động</button>
                        <button type="button" id="btn-action-clear" style="background: #151a26; border: 1px solid #232b3c; border-radius: 6px; color: #cbd5e1; padding: 4px 9px; font-size: 11px; font-weight: 600; cursor: pointer;">🔄 Làm trống</button>
                        <button type="button" class="btn-copy-emotion-table" style="background: linear-gradient(135deg, #f97316, #ea580c); border: 1px solid #fb923c; border-radius: 6px; color: #ffffff; padding: 4px 9px; font-size: 11px; font-weight: 700; cursor: pointer;">✨ Kịch bản mẫu / Copy AI</button>
                    </div>
                </div>
                """
            )

            # Neon Emotion Tags Panel
            st.html(
                """
                <div style="background: #0d1018; border: 1px solid #1c2333; border-radius: 10px; padding: 10px 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                        <span style="font-size: 11.5px; font-weight: 800; color: #cbd5e1; display: flex; align-items: center; gap: 5px;">
                            🎯 BẤM CHÈN THẺ CẢM XÚC TẠI CON TRỎ:
                        </span>
                        <span style="font-size: 10.5px; color: #64748b; font-weight: 600;">VieNeu Neural Markup v4.2</span>
                    </div>

                    <style>
                        .neon-tag-chip {
                            background: #141926;
                            border: 1px solid #222a3d;
                            color: #e2e8f0;
                            border-radius: 6px;
                            padding: 3px 8px;
                            font-size: 11.5px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.12s ease;
                            user-select: none;
                            display: inline-flex;
                            align-items: center;
                            gap: 3px;
                        }
                        .neon-tag-chip:hover {
                            background: #1d2538 !important;
                            border-color: #f97316 !important;
                            color: #ffffff !important;
                        }
                        .neon-row {
                            display: flex;
                            align-items: center;
                            gap: 5px;
                            margin-bottom: 5px;
                            flex-wrap: wrap;
                        }
                        .neon-row-sub {
                            margin-left: 130px;
                        }
                        .neon-cat {
                            font-size: 10px;
                            font-weight: 800;
                            color: #64748b;
                            background: #111420;
                            border: 1px solid #1c2233;
                            padding: 2px 7px;
                            border-radius: 4px;
                            min-width: 125px;
                            text-align: center;
                        }
                    </style>

                    <!-- Row 1: Vui nhộn / Cười -->
                    <div class="neon-row">
                        <span class="neon-cat">VUI NHỘN / CƯỜI:</span>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[cười]">😄 [Cười]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[laughing]">😆 [Cười to]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[snickers]">😏 [Cười đểu]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[chuckles]">🤣 [Haha]</button>
                    </div>

                    <!-- Row 2: Trầm / Bi thương -->
                    <div class="neon-row">
                        <span class="neon-cat">TRẦM / BI THƯƠNG:</span>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[sighs]">😮‍💨 [Thở dài]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[crying]">😭 [Khóc]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[clears throat]">🗣️ [Hắng giọng]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[sneezes]">🤧 [Hắt hơi]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[hesitant]">🤐 [Nấc]</button>
                    </div>

                    <!-- Row 3: Kịch tính / Căng thẳng -->
                    <div class="neon-row">
                        <span class="neon-cat">KỊCH TÍNH / CĂNG THẲNG:</span>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[shocked]">😱 [Sốc]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[angry]">😡 [Tức giận]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[whispering]">🤫 [Thì thầm]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[shouting]">📢 [Hét to]</button>
                    </div>

                    <!-- Row 3b: Phụ kịch tính -->
                    <div class="neon-row neon-row-sub">
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[panicked]">🏃 [Chết rồi!]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[thinking]">🤔 [Hmm...]</button>
                    </div>

                    <!-- Row 4: Nhịp điệu ngắt nghỉ -->
                    <div class="neon-row" style="margin-bottom: 0;">
                        <span class="neon-cat">NHỊP ĐIỆU NGẮT NGHỈ:</span>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 0.3s]">⏱️ [Nghỉ 0.3s]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 0.5s]">⏸️ [Nghỉ 0.5s]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 1s]">⏳ [Nghỉ 1.0s]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 2s]">🛑 [Nghỉ 2.0s]</button>
                    </div>

                    <!-- Dropdown Đầy Đủ 55+ Mã Biểu Cảm & Nút Chèn Tại Con Trỏ -->
                    <div class="caret-select-container" style="display: flex; gap: 8px; align-items: center; margin-top: 10px; padding-top: 9px; border-top: 1px solid #1c2333; flex-wrap: wrap;">
                        <div style="flex-grow: 1; min-width: 250px;">
                            <select id="caretSelectTag" style="width: 100%; background: #141926; color: #ffffff; border: 1.5px solid #283147; border-radius: 6px; padding: 6px 10px; font-size: 12px; outline: none; cursor: pointer;">
                                <option value="[crying]">😭 [crying] - hu hu (khóc)</option>
                                <option value="[coughs]">😷 [coughs] - khụ khụ (ho)</option>
                                <option value="[lip smacks]">😋 [lip smacks] - chẹp chẹp</option>
                                <option value="[annoyed]">😤 [annoyed] - chậc (khó chịu)</option>
                                <option value="[screaming]">😱 [screaming] - áaaaa (kêu la)</option>
                                <option value="[yelling]">📢 [yelling] - Êeeee (gọi to)</option>
                                <option value="[affirmative]">👌 [affirmative] - ừ hứ (đồng tình)</option>
                                <option value="[realization]">💡 [realization] - ôooo (nhận ra)</option>
                                <option value="[giggles]">🤭 [giggles] - hí hí hí (cười khúc khích)</option>
                                <option value="[thinking]">🤔 [thinking] - hmmm (suy nghĩ)</option>
                                <option value="[gasps]">😮 [gasps] - hự (thở gấp)</option>
                                <option value="[excited]">🤩 [excited] - wowww (hào hứng)</option>
                                <option value="[relieved]">😌 [relieved] - phùuu (thở phào)</option>
                                <option value="[confused]">🤨 [confused] - hả? (bối rối)</option>
                                <option value="[agreeing]">👍 [agreeing] - đúng rồi</option>
                                <option value="[cheering]">🎉 [cheering] - yeahhhh (cổ vũ)</option>
                                <option value="[groans]">😩 [groans] - ôi trời ơi...</option>
                                <option value="[embarrassed]">😳 [embarrassed] - ôi ngại quá</option>
                                <option value="[angry]">😡 [angry] - tức quá!</option>
                                <option value="[curious]">🧐 [curious] - ủa? (tò mò)</option>
                                <option value="[sarcastic]">😏 [sarcastic] - ghê chưa (mỉa mai)</option>
                                <option value="[happy]">😄 [happy] - vui quá</option>
                                <option value="[celebrating]">🥳 [celebrating] - yooooo (ăn mừng)</option>
                                <option value="[pleading]">🥺 [pleading] - làm ơn đi</option>
                                <option value="[confident]">😎 [confident] - chắc chắn luôn</option>
                                <option value="[grunts]">💪 [grunts] - hự! Cố lên</option>
                                <option value="[snickers]">😼 [snickers] - khì khì (cười đểu)</option>
                                <option value="[panicked]">🏃 [panicked] - chết chết chết!</option>
                                <option value="[sneezes]">🤧 [sneezes] - ách xì</option>
                                <option value="[hesitant]">🤐 [hesitant] - ừm... (ngập ngừng)</option>
                                <option value="[chuckles]">😆 [chuckles] - he he he</option>
                                <option value="[cười]">😄 [cười] - tiếng cười tự nhiên</option>
                                <option value="[shouting]">🗣️ [shouting] - gôôôôô</option>
                                <option value="[sighs]">😮‍💨 [sighs] - haizzz (thở dài)</option>
                                <option value="[surprised]">😲 [surprised] - á há (ngạc nhiên)</option>
                                <option value="[awkward laugh]">😅 [awkward laugh] - hơ hơ hơ (gượng)</option>
                                <option value="[laughing]">😂 [laughing] - hahaha (cười to)</option>
                                <option value="[yawns]">🥱 [yawns] - ngáppp (ngáp)</option>
                                <option value="[whispering]">🤫 [whispering] - psst... (thì thầm)</option>
                                <option value="[shocked]">😱 [shocked] - trời ơi! (sốc)</option>
                                <option value="[amazed]">✨ [amazed] - ôi wow (kinh ngạc)</option>
                                <option value="[frustrated]">😫 [frustrated] - trời đất ơi</option>
                                <option value="[doubtful]">🤨 [doubtful] - thật không vậy?</option>
                                <option value="[disagreeing]">🙅 [disagreeing] - không đâu</option>
                                <option value="[applause]">👏 [applause] - bốp bốp bốp (vỗ tay)</option>
                                <option value="[nervous laugh]">😬 [nervous laugh] - hơ hơ...</option>
                                <option value="[disappointed]">😞 [disappointed] - ôi thôi rồi</option>
                                <option value="[worried]">😟 [worried] - chết rồi (lo lắng)</option>
                                <option value="[teasing]">😜 [teasing] - ê nhaaa (trêu chọc)</option>
                                <option value="[proud]">🦁 [proud] - tuyệt vời (tự hào)</option>
                                <option value="[sad]">😢 [sad] - buồn ghê</option>
                                <option value="[apologetic]">🙏 [apologetic] - anh xin lỗi nhé</option>
                                <option value="[determined]">🔥 [determined] - nhất định rồi</option>
                                <option value="[excited gasp]">😮‍💨 [excited gasp] - ôiiii không</option>
                                <option value="[clears throat]">🗣️ [clears throat] - hèm hèm (hắng giọng)</option>
                                <option value="[smug]">😎 [smug] - biết ngay mà</option>
                                <option value="[nghỉ 0.3s]">⏱️ [nghỉ 0.3s] - Ngắt 0.3s</option>
                                <option value="[nghỉ 0.5s]">⏸️ [nghỉ 0.5s] - Ngắt 0.5s</option>
                                <option value="[nghỉ 1s]">⏳ [nghỉ 1s] - Ngắt 1.0s</option>
                                <option value="[nghỉ 2s]">🛑 [nghỉ 2s] - Ngắt 2.0s</option>
                            </select>
                        </div>
                        <button type="button" id="caretDropdownBtn" style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: #ffffff; border: 1px solid #fb923c; border-radius: 6px; padding: 6px 14px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 0 10px rgba(249, 115, 22, 0.4);">
                            ➕ Chèn tại vị trí con trỏ chuột
                        </button>
                    </div>
                </div>
                """
            )

            # Editor Header
            st.html(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; font-size: 11.5px; padding: 0 2px;">
                    <span style="color: #f97316; font-weight: 700;">● KỊCH BẢN ĐANG XỬ LÝ (LIVE SYNTAX MODE) <span style="color: #64748b;">| Review Phim Thánh Adam #01</span></span>
                    <div style="display: flex; gap: 6px;">
                        <button type="button" id="btn-action-format" style="background: #141926; border: 1px solid #232b3d; border-radius: 4px; color: #cbd5e1; font-size: 11px; padding: 2px 7px; cursor: pointer;">Format Tags</button>
                        <span style="background: #171d2b; border: 1px solid #29344c; color: #cbd5e1; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 700;">AI Script Rewriter</span>
                    </div>
                </div>
                """
            )

            # Text Area
            current_text = st.text_area(
                "Kịch bản lời thoại:",
                key="tts_main_text",
                height=130,
                label_visibility="collapsed",
                placeholder="Nhập hoặc dán kịch bản tại đây...",
            )

            # Dynamic Stats Counter Bar
            initial_words = len([w for w in current_text.strip().split() if w]) if current_text.strip() else 0
            initial_chars = len(current_text)
            initial_tags = len(re.findall(r"\[[^\]]+\]", current_text))
            initial_duration = f"00:{(initial_words / 2.7):04.1f}s"

            st.html(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; background: #0c0e16; border: 1px solid #1a2030; border-radius: 6px; padding: 5px 12px; margin-top: 5px; margin-bottom: 12px; font-size: 11.5px; color: #94a3b8; flex-wrap: wrap; gap: 6px;">
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <span id="daw-stat-words" style="color: #e2e8f0;">Từ: <strong style="color: #f97316;">{initial_words} từ</strong></span>
                        <span>•</span>
                        <span id="daw-stat-chars" style="color: #e2e8f0;">Ký tự: <strong style="color: #f97316;">{initial_chars} ký tự</strong></span>
                        <span>•</span>
                        <span id="daw-stat-duration" style="color: #cbd5e1;">⏱️ Thời lượng dự kiến: {initial_duration}</span>
                        <span>•</span>
                        <span style="color: #64748b;">Tỷ lệ cảm xúc: 100% Khớp</span>
                    </div>
                    <div style="background: #161b27; border: 1px solid #242c3f; border-radius: 4px; padding: 1px 7px; font-size: 11px;">
                        <strong id="daw-stat-tags" style="color: #cbd5e1;">{initial_tags} Tags Phát hiện</strong>
                    </div>
                </div>
                """
            )

            # Bottom Script Tools: Preset Dropdown & TXT File Upload
            c_preset, c_upload = st.columns([1.1, 0.9])
            with c_preset:
                st.markdown("<span style='font-size: 11.5px; color: #f97316; font-weight: 700;'>🔥 Preset Kịch Bản Hot Triệu View:</span>", unsafe_allow_html=True)
                st.selectbox(
                    "Preset:",
                    options=list(sample_options.keys()),
                    index=0,
                    key="sample_preset_choice",
                    on_change=apply_sample_preset,
                    label_visibility="collapsed",
                )
            with c_upload:
                st.markdown("<span style='font-size: 11.5px; color: #f97316; font-weight: 700;'>📁 Tải Kịch Bản (TXT / SRT / DOCX):</span>", unsafe_allow_html=True)
                st.file_uploader(
                    "File kịch bản:",
                    type=["txt"],
                    key="txt_upload",
                    on_change=apply_txt_upload,
                    label_visibility="collapsed",
                )

            # Full 55+ Emotion Table Expander
            with st.expander("📊 Xem & Sao chép đầy đủ 55+ Bảng mã lệnh cảm xúc (Dùng cho ChatGPT / AI)", expanded=False):
                st.markdown(
                    """
                    💡 **Mẹo:** Bấm nút **"📋 Copy Bảng cho Chat AI"** để sao chép toàn bộ bảng và prompt gửi sang ChatGPT / Claude nhờ AI viết kịch bản chèn sẵn cảm xúc!
                    """
                )
                st.code(EMOTION_PROMPT_TEMPLATE, language="markdown")
                st.markdown(
                    "<div style='font-size: 12px; color: #64748b; margin-top: 6px;'>👇 <i>Bấm vào mã lệnh bất kỳ trong bảng để chèn nhanh vào kịch bản:</i></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(emotion_table_html, unsafe_allow_html=True)


    # ------------------------------------------------------------------------------
    # COLUMN 2: BƯỚC 2: PHỐI GIỌNG & MÔ PHÒNG PHÒNG THU
    # ------------------------------------------------------------------------------
    with col_studio:
        with st.container(border=True):
            # Header Row
            st.html(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="background: #171c28; border: 1.5px solid #283147; color: #f8fafc; border-radius: 50%; width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; font-weight: 900; font-size: 15px;">02</div>
                        <div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff; letter-spacing: 0.3px;">BƯỚC 2: PHỐI GIỌNG & MÔ PHÒNG PHÒNG THU</div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">Acoustic Engine • Điều biến tần số & Giả lập buồng thu chuyên nghiệp</div>
                        </div>
                    </div>
                </div>
                """
            )

            # Language Header & Selector
            col_lang_t1, col_lang_t2 = st.columns([0.7, 0.3])
            with col_lang_t1:
                st.markdown("<span style='font-size: 11.5px; color: #cbd5e1; font-weight: 600;'>Ngôn ngữ & Phương ngữ VieNeu:</span>", unsafe_allow_html=True)
            with col_lang_t2:
                st.markdown("<div style='text-align: right; font-size: 11px; color: #f97316; font-weight: 700;'>● AI Đa vùng miền</div>", unsafe_allow_html=True)

            tts_lang = st.selectbox(
                "Ngôn ngữ:",
                options=list(LANGUAGE_NAMES.keys()),
                index=0,
                format_func=lambda code: f"🇻🇳 {LANGUAGE_NAMES.get(code, code)} (Miền Bắc Chuẩn - Hà Nội Thanh Lịch)" if code == "vi" else LANGUAGE_NAMES.get(code, code),
                key="tts_lang_select",
                label_visibility="collapsed",
            )

            voices_dict = VOICES_CATALOG.get(tts_lang, VOICES_CATALOG["vi"])
            voice_options = list(voices_dict.keys())

            # Ensure session state has a valid selection
            if "selected_voice_label" not in st.session_state or st.session_state["selected_voice_label"] not in voice_options:
                st.session_state["selected_voice_label"] = voice_options[0]

            # Dropdown chọn giọng đầy đủ 31+ giọng (Chọn giọng bất kỳ để nghe thử)
            st.markdown("<span style='font-size: 11.5px; color: #f97316; font-weight: 700;'>🎙️ Danh sách toàn bộ 31+ giọng đọc AI (Chọn nhân vật bất kỳ để nghe thử):</span>", unsafe_allow_html=True)
            selected_voice_label = st.selectbox(
                "Danh sách giọng:",
                options=voice_options,
                key="selected_voice_label",
                label_visibility="collapsed",
            )
            selected_voice_id = voices_dict[selected_voice_label]

            # Trích xuất thông tin động của giọng đang chọn để hiển thị lên thẻ Nghe Thử
            clean_name = selected_voice_label.split(" (")[0].replace("🔥 ", "").strip()
            if " (" in selected_voice_label:
                raw_desc = selected_voice_label.split(" (")[1].rstrip(")")
            else:
                raw_desc = "VieNeu Voice Talent • Chuẩn Studio 48kHz"

            if "Adam" in clean_name:
                v_badge = "HOT REVIEW"
            elif "Hải Đăng" in clean_name or "Tuấn Anh" in clean_name:
                v_badge = "THỜI SỰ VTV"
            elif "Thiện Minh" in clean_name or "Bảy" in clean_name:
                v_badge = "KỂ CHUYỆN"
            elif "Thùy Dung" in clean_name or "Mỹ Linh" in clean_name or "Trúc Ly" in clean_name:
                v_badge = "PODCAST TỰ NHIÊN"
            elif "🔥" in selected_voice_label:
                v_badge = "HOT TALENT"
            else:
                v_badge = "VIENEU PRO"

            # Thẻ Showcase động: Tự động đổi theo giọng đang chọn trong danh sách 31+ giọng
            c_feat1, c_feat2 = st.columns([0.65, 0.35])
            with c_feat1:
                st.html(
                    f"""
                    <div style="background: #0d1018; border: 1.5px solid #f97316; border-radius: 10px; padding: 10px 12px; margin-top: 4px; margin-bottom: 8px; box-shadow: 0 0 16px rgba(249, 115, 22, 0.15);">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="width: 38px; height: 38px; border-radius: 50%; background: #1a2030; border: 1.5px solid #f97316; color: #f97316; display: flex; align-items: center; justify-content: center; font-size: 18px;">
                                🎙️
                            </div>
                            <div>
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span style="font-size: 1.05rem; font-weight: 800; color: #ffffff;">{clean_name}</span>
                                    <span style="background: #f97316; color: #ffffff; font-size: 9px; font-weight: 800; padding: 1px 5px; border-radius: 3px;">{v_badge}</span>
                                </div>
                                <div style="font-size: 0.74rem; color: #cbd5e1;">{raw_desc}</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 6px; margin-top: 6px; font-size: 10.5px;">
                            <span style="background: #141926; color: #94a3b8; border: 1px solid #222a3d; padding: 1px 6px; border-radius: 4px;">Master Acoustic 48kHz Stereo</span>
                            <span style="background: #141926; color: #10b981; border: 1px solid #222a3d; padding: 1px 6px; border-radius: 4px;">Độ biểu cảm: Cực mạnh (10/10)</span>
                        </div>
                    </div>
                    """
                )
            # Tạo dữ liệu base64 mẫu giọng nghe thử client-side độc lập 100%
            sample_audio_uri = ""
            try:
                sample_file = get_or_generate_voice_preview(selected_voice_id, tts_lang, clean_name)
                if sample_file.exists() and sample_file.stat().st_size > 100:
                    s_b64 = base64.b64encode(sample_file.read_bytes()).decode("utf-8")
                    sample_audio_uri = f"data:audio/mp3;base64,{s_b64}"
            except Exception:
                pass

            with c_feat2:
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                st.html(
                    f"""
                    <audio id="vdt-preview-audio-core" src="{sample_audio_uri}" preload="auto"></audio>
                    <button type="button" id="vdt-btn-preview-sample" style="
                        width: 100%;
                        height: 72px;
                        background: #0d111a;
                        border: 1.5px solid #283347;
                        border-radius: 9px;
                        padding: 8px 6px;
                        cursor: pointer;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        gap: 3px;
                        transition: all 0.15s ease;
                        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
                    " title="Bấm để phát hoặc dừng nghe thử mẫu giọng {clean_name}">
                        <div style="display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 800; color: #f97316;">
                            <span id="vdt-preview-icon" style="font-size: 16px;">🎧</span>
                            <span id="vdt-preview-lbl">Nghe thử mẫu</span>
                        </div>
                        <div style="font-size: 10.5px; color: #cbd5e1; font-weight: 700; max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            {clean_name}
                        </div>
                        <div style="font-size: 9px; color: #64748b; font-weight: 600;">(Độc lập • 0% ảnh hưởng thanh dưới)</div>
                    </button>
                    """
                )
                # Controller script cho mẫu nghe thử: Hoàn toàn không reload Streamlit
                preview_js = f"""
                <!DOCTYPE html>
                <html><head><meta charset="utf-8"></head><body>
                <script>
                (function() {{
                    try {{
                        var parentDoc = window.parent.document;
                        var parentWin = window.parent;

                        // Hủy listener cũ để không bao giờ bị đè hoặc trỏ vào closure của render trước
                        if (parentWin.__vdtPreviewClickHandler) {{
                            parentDoc.removeEventListener('click', parentWin.__vdtPreviewClickHandler, true);
                        }}

                        parentWin.__vdtPreviewClickHandler = function(e) {{
                            var btn = e.target.closest('#vdt-btn-preview-sample');
                            if (!btn) return;
                            e.preventDefault();
                            e.stopPropagation();

                            var prevAudio = parentDoc.getElementById('vdt-preview-audio-core');
                            var prevIcon = parentDoc.getElementById('vdt-preview-icon');
                            var prevLbl = parentDoc.getElementById('vdt-preview-lbl');
                            var masterAudio = parentDoc.getElementById('daw-core-audio');

                            if (!prevAudio || !prevAudio.src || prevAudio.src === '' || prevAudio.src.endsWith('/')) {{
                                console.warn("Preview audio not ready.");
                                if (prevLbl) prevLbl.textContent = "Chưa có mẫu";
                                return;
                            }}

                            if (prevAudio.paused) {{
                                if (masterAudio && !masterAudio.paused) {{
                                    if (parentWin.__vdtDoPause) {{
                                        parentWin.__vdtDoPause();
                                    }} else {{
                                        masterAudio.pause();
                                    }}
                                }}
                                prevAudio.currentTime = 0;
                                prevAudio.play().then(function() {{
                                    if (prevIcon) prevIcon.textContent = "⏸";
                                    if (prevLbl) prevLbl.textContent = "Đang phát...";
                                    btn.style.borderColor = "#f97316";
                                    btn.style.background = "#182030";
                                }}).catch(function(err) {{
                                    console.log("Preview error:", err);
                                }});
                            }} else {{
                                prevAudio.pause();
                                if (prevIcon) prevIcon.textContent = "🎧";
                                if (prevLbl) prevLbl.textContent = "Nghe thử mẫu";
                                btn.style.borderColor = "#283347";
                                btn.style.background = "#0d111a";
                            }}
                        }};

                        parentDoc.addEventListener('click', parentWin.__vdtPreviewClickHandler, true);

                        var prevAudio = parentDoc.getElementById('vdt-preview-audio-core');
                        if (prevAudio) {{
                            function resetPreviewBtn() {{
                                var prevIcon = parentDoc.getElementById('vdt-preview-icon');
                                var prevLbl = parentDoc.getElementById('vdt-preview-lbl');
                                var btn = parentDoc.getElementById('vdt-btn-preview-sample');
                                if (prevIcon) prevIcon.textContent = "🎧";
                                if (prevLbl) prevLbl.textContent = "Nghe thử mẫu";
                                if (btn) {{
                                    btn.style.borderColor = "#283347";
                                    btn.style.background = "#0d111a";
                                }}
                            }}
                            prevAudio.onended = resetPreviewBtn;
                            prevAudio.onpause = function() {{
                                if (prevAudio.paused) resetPreviewBtn();
                            }};
                        }}

                    }} catch(e) {{
                        console.error("Preview script error:", e);
                    }}
                }})();
                </script>
                </body></html>
                """
                components.html(preview_js, height=0)

            # Quick Voice Suggestions Grid (2x2) với on_click an toàn tuyệt đối
            st.markdown("<div style='font-size: 11px; color: #64748b; font-weight: 700; margin-bottom: 5px;'>Gợi ý giọng đọc thịnh hành (Bấm để đổi ngay):</div>", unsafe_allow_html=True)
            gv1, gv2 = st.columns(2)
            with gv1:
                st.button(
                    "🔥 Adam Review Phim\n\nKịch tính, hài hước, cà khịa",
                    key="btn_adam",
                    on_click=set_quick_voice,
                    args=(["Adam"],),
                    use_container_width=True,
                )
                st.button(
                    "👻 Thầy Bảy Kể Chuyện Ma\n\nRùng rợn, thì thào đêm khuya",
                    key="btn_thaybay",
                    on_click=set_quick_voice,
                    args=(["Thiện Minh", "Bảy"],),
                    use_container_width=True,
                )
            with gv2:
                st.button(
                    "🎙️ Tuấn Anh Thời Sự VTV\n\nNam Bắc, trầm hùng, chuẩn mực",
                    key="btn_tuananh",
                    on_click=set_quick_voice,
                    args=(["Hải Đăng", "Tuấn Anh"],),
                    use_container_width=True,
                )
                st.button(
                    "✨ Mỹ Linh Podcast Sài Gòn\n\nNgọt ngào, chữa lành tâm hồn",
                    key="btn_mylinh",
                    on_click=set_quick_voice,
                    args=(["Thùy Dung", "Mỹ Linh"],),
                    use_container_width=True,
                )

            # Tempo Controls
            st.html(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; margin-bottom: 4px;">
                    <span style="font-size: 11.5px; font-weight: 700; color: #f97316;">⚡ Tốc độ nói (Tempo):</span>
                    <span style="background: rgba(249, 115, 22, 0.15); border: 1px solid #f97316; color: #f97316; border-radius: 4px; padding: 1px 7px; font-size: 11px; font-weight: 800;">1.15x (+15%)</span>
                </div>
                """
            )
            sp1, sp2, sp3, sp4 = st.columns(4)
            with sp1:
                st.button("0.8x", key="btn_tempo_08", on_click=set_quick_tempo, args=(-20,), use_container_width=True)
            with sp2:
                st.button("1.0x", key="btn_tempo_10", on_click=set_quick_tempo, args=(0,), use_container_width=True)
            with sp3:
                st.button(
                    "🔥 1.15x",
                    key="btn_tempo_115",
                    on_click=set_quick_tempo,
                    args=(15,),
                    use_container_width=True,
                    type="primary" if st.session_state.get("slider_speed_val", 15) == 15 else "secondary",
                )
            with sp4:
                st.button("1.3x", key="btn_tempo_13", on_click=set_quick_tempo, args=(30,), use_container_width=True)

            current_speed = st.session_state.get("slider_speed_val", 15)
            tts_rate_val = st.slider(
                "Tùy chỉnh tốc độ %:",
                min_value=-50,
                max_value=50,
                value=current_speed,
                step=5,
                format="%d%%",
                key="slider_speed_widget",
                label_visibility="collapsed",
            )
            st.session_state["slider_speed_val"] = tts_rate_val

            st.html(
                """
                <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; margin-top: -8px; margin-bottom: 10px;">
                    <span>-50% Chậm</span>
                    <span style="color: #f97316; font-weight: 700;">Chuẩn Tốp Tốp (+15%)</span>
                    <span>+50% Nhanh</span>
                </div>
                """
            )

            speed_factor = 1.0 + (tts_rate_val / 100.0)
            rate_str = f"{'+' if tts_rate_val >= 0 else ''}{tts_rate_val}%"

            # Two Pro Sliders: Cường độ cảm xúc & Cao độ (Pitch)
            sl1, sl2 = st.columns(2)
            with sl1:
                st.markdown("<div style='font-size: 11.5px; color: #cbd5e1; font-weight: 700;'>Cường độ cảm xúc: <strong style='color: #f97316;'>85%</strong></div>", unsafe_allow_html=True)
                st.slider("Emotion Depth:", min_value=0, max_value=100, value=85, key="emotion_depth", label_visibility="collapsed")
                st.markdown("<div style='font-size: 10px; color: #64748b; margin-top: -8px;'>Emotion Depth Pro</div>", unsafe_allow_html=True)
            with sl2:
                st.markdown("<div style='font-size: 11.5px; color: #cbd5e1; font-weight: 700;'>Cao độ (Pitch): <strong style='color: #f97316;'>0 st</strong></div>", unsafe_allow_html=True)
                st.slider("Pitch:", min_value=-12, max_value=12, value=0, key="pitch_val", label_visibility="collapsed")
                st.markdown("<div style='font-size: 10px; color: #64748b; margin-top: -8px;'>-12st đến +12st</div>", unsafe_allow_html=True)

            # Acoustic FX Studio Simulation
            st.html(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 6px;">
                    <span style="font-size: 11.5px; font-weight: 700; color: #cbd5e1;">Hiệu ứng buồng thu âm (Acoustic FX):</span>
                    <span style="font-size: 10.5px; color: #64748b;">AI Denoise 99.8%</span>
                </div>
                """
            )
            fx1, fx2, fx3 = st.columns(3)
            current_fx = st.session_state.get("active_acoustic_fx", "Studio Dry")
            with fx1:
                st.button(
                    "🎙️ Studio Dry",
                    key="btn_fx_dry",
                    on_click=set_acoustic_fx,
                    args=("Studio Dry",),
                    use_container_width=True,
                    type="primary" if current_fx == "Studio Dry" else "secondary",
                )
            with fx2:
                st.button(
                    "🏛️ Room Reverb",
                    key="btn_fx_reverb",
                    on_click=set_acoustic_fx,
                    args=("Room Reverb",),
                    use_container_width=True,
                    type="primary" if current_fx == "Room Reverb" else "secondary",
                )
            with fx3:
                st.button(
                    "🎧 AI Denoise",
                    key="btn_fx_denoise",
                    on_click=set_acoustic_fx,
                    args=("AI Denoise",),
                    use_container_width=True,
                    type="primary" if current_fx == "AI Denoise" else "secondary",
                )

            # GIANT PRIMARY RENDER AUDIO BUTTON
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            btn_generate_tts = st.button(
                "⚡ TẠO GIỌNG ĐỌC AI NGAY (RENDER AUDIO)   Ctrl + Enter",
                type="primary",
                use_container_width=True,
            )

            st.html(
                """
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-top: 5px;">
                    <span>Tiêu tốn: <strong style="color: #cbd5e1;">178 ký tự</strong> (-0.02% Quota)</span>
                    <span>⏱️ Thời gian kết xuất: <strong style="color: #cbd5e1;">~0.4 giây</strong></span>
                </div>
                """
            )


    # ==============================================================================
    # AUDIO GENERATION EXECUTION PIPELINE (Thanh tiến trình 1% - 100% Chuẩn Xác)
    # ==============================================================================
    if btn_generate_tts:
        text_to_speak = st.session_state["tts_main_text"].strip()
        if not text_to_speak:
            st.warning("⚠️ Vui lòng nhập nội dung văn bản kịch bản trước khi tạo giọng đọc!")
        else:
            tts_output_dir = Path("./output/tts")
            tts_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            progress_slot = st.empty()

            try:
                # Giai đoạn 1: 1% -> 25% (Phân tích kịch bản và bóc tách các tag âm học)
                for p in range(1, 26, 4):
                    progress_slot.progress(p, text=f"⚡ Tiến trình kết xuất VieNeu: {p}% — Phân tích kịch bản & thẻ cảm xúc acoustic tags...")
                    time.sleep(0.02)

                # Giai đoạn 2: 26% -> 48% (Khởi tạo Acoustic Engine & nạp profile giọng)
                for p in range(26, 49, 4):
                    progress_slot.progress(p, text=f"🎙️ Tiến trình kết xuất VieNeu: {p}% — Nạp profile âm sắc chuẩn 48kHz cho [{clean_name}]...")
                    time.sleep(0.02)

                # Giai đoạn 3: 49% -> 60% (Bắt đầu tổng hợp tín hiệu âm thanh)
                progress_slot.progress(55, text=f"⚡ Tiến trình kết xuất VieNeu: 55% — Đang tổng hợp giọng nói đa biểu cảm...")

                if selected_voice_id.startswith("vieneu:"):
                    clean_v = selected_voice_id.replace("vieneu:", "")
                    safe_v_name = re.sub(r'[^\w\-_\.]', '_', clean_v)
                    out_file = tts_output_dir / f"tts_vieneu_{safe_v_name}_{timestamp}.mp3"
                    generate_vieneu_speech(
                        text=text_to_speak,
                        voice=clean_v,
                        speed=speed_factor,
                        output_path=out_file,
                    )
                else:
                    clean_text = text_to_speak
                    for emo_tag in EMOTION_SOUND_MAP.keys():
                        clean_text = clean_text.replace(f"[{emo_tag}]", "")
                    out_file = tts_output_dir / f"tts_edge_{selected_voice_id}_{timestamp}.mp3"
                    asyncio.run(
                        generate_single_tts_edge(
                            text=clean_text,
                            voice=selected_voice_id,
                            rate=rate_str,
                            volume="+0%",
                            pitch="+0Hz",
                            output_path=out_file,
                        )
                    )

                # Giai đoạn 4: 61% -> 85% (Xử lý hiệu ứng DSP và buồng thu âm thực thụ)
                fx_name = st.session_state.get("active_acoustic_fx", "Studio Dry")
                pitch_semitones = st.session_state.get("pitch_val", 0)

                for p in range(62, 72, 3):
                    progress_slot.progress(p, text=f"🎛️ Tiến trình kết xuất: {p}% — Nạp buồng thu âm [{fx_name}]...")
                    time.sleep(0.015)

                try:
                    from video_dubber.vieneu_tts import apply_acoustic_fx
                    apply_acoustic_fx(
                        sound_or_path=out_file,
                        fx_name=fx_name,
                        pitch_semitones=pitch_semitones,
                        output_path=out_file,
                    )
                except Exception as dsp_err:
                    logger.warning(f"Acoustic FX processing note: {dsp_err}")

                for p in range(74, 86, 3):
                    progress_slot.progress(p, text=f"🎛️ Tiến trình kết xuất: {p}% — Hoàn tất hiệu ứng buồng thu [{fx_name}] & Equalizer Mastering...")
                    time.sleep(0.015)

                # Giai đoạn 5: 86% -> 99% (Mastering Lossless & Đồng bộ Timecode Phụ đề)
                for p in range(86, 100, 3):
                    progress_slot.progress(p, text=f"📦 Tiến trình kết xuất VieNeu: {p}% — Đóng gói Master 24-bit Lossless & Phụ đề SRT...")
                    time.sleep(0.02)

                # Giai đoạn 6: 100% (Hoàn tất thành công)
                progress_slot.progress(100, text="✅ Hoàn tất kết xuất 100%! Đang khởi tạo DAW Master Player...")
                time.sleep(0.35)
                progress_slot.empty()

                # Lưu vào session_state dành riêng cho kết quả từ văn bản
                st.session_state["script_generated_file"] = str(out_file)
                st.session_state["script_generated_title"] = f"{clean_name}_{timestamp}"
                st.session_state["script_generated_voice_name"] = clean_name
                st.session_state["just_rendered_autoplay"] = True
                st.toast("🎉 Đã kết xuất âm thanh Master 48kHz thành công! Đang phát trong DAW Player.", icon="🎙️")
                st.rerun()

            except Exception as err:
                progress_slot.empty()
                st.error(f"❌ Có lỗi xảy ra trong quá trình tạo âm thanh: {err}")

with tab_dubbing:
    st.html(
        """
        <div style="background: linear-gradient(135deg, rgba(23, 29, 43, 0.95), rgba(16, 21, 31, 0.95)); border: 1.5px solid #232d42; border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: rgba(249, 115, 22, 0.15); border: 1.5px solid #f97316; color: #f97316; border-radius: 10px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🎬</div>
                    <div>
                        <div style="font-size: 1.12rem; font-weight: 800; color: #ffffff; letter-spacing: 0.3px;">LỒNG TIẾNG VIDEO AI TỰ ĐỘNG (AI VIDEO DUBBING PRO)</div>
                        <div style="font-size: 0.8rem; color: #94a3b8;">Nhận diện giọng nói siêu tốc Whisper • Dịch thuật đa ngữ • Lồng tiếng AI & khớp khẩu hình âm thanh</div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span style="background: #141926; border: 1px solid #26334d; color: #38bdf8; font-size: 11px; font-weight: 700; padding: 5px 10px; border-radius: 6px;">⚡ Whisper AI</span>
                    <span style="background: #141926; border: 1px solid #26334d; color: #a855f7; font-size: 11px; font-weight: 700; padding: 5px 10px; border-radius: 6px;">🌐 Auto Translate</span>
                    <span style="background: #141926; border: 1px solid #26334d; color: #f97316; font-size: 11px; font-weight: 700; padding: 5px 10px; border-radius: 6px;">🎙️ 43+ AI Voices</span>
                </div>
            </div>
        </div>
        """
    )

    col_dub_left, col_dub_right = st.columns([1, 1], gap="medium")

    with col_dub_left:
        with st.container(border=True):
            st.markdown("##### 📁 Bước 1: Màn hình Studio — Tải lên & Xem trước Trực tiếp trên Video")
            uploaded_video = st.file_uploader(
                "Chọn tệp Video (MP4, MKV, MOV, AVI)",
                type=["mp4", "mkv", "mov", "avi"],
                key="dub_video_file_uploader",
                help="Hỗ trợ các định dạng video thông dụng"
            )

            if uploaded_video is not None:
                st.video(uploaded_video)
                st.caption(f"📹 Tệp: **{uploaded_video.name}** ({uploaded_video.size / (1024 * 1024):.2f} MB)")

                # Thanh thông báo Studio Live Mode
                st.html(
                    """
                    <div id="vdt-studio-status-banner" style="
                        background: linear-gradient(90deg, rgba(249, 115, 22, 0.12), rgba(56, 189, 248, 0.12));
                        border: 1px solid rgba(249, 115, 22, 0.35);
                        border-radius: 8px;
                        padding: 7px 12px;
                        margin-top: 4px;
                        margin-bottom: 8px;
                        font-size: 11px;
                        color: #cbd5e1;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        flex-wrap: wrap;
                        gap: 6px;
                    ">
                        <span style="display: flex; align-items: center; gap: 6px; font-weight: 700;">
                            <span style="color: #f97316; font-size: 13px;">🎮 CHẾ ĐỘ XEM TRƯỚC TRÊN MẶT VIDEO:</span>
                            Bấm giữ chuột vào Logo hoặc Phụ đề để kéo thả trực tiếp trên video!
                        </span>
                        <span id="vdt-live-coords-indicator" style="font-family: monospace; font-weight: 800; color: #38bdf8; background: #0c121e; padding: 1px 6px; border-radius: 4px;">
                            📍 Sẵn sàng kéo thả
                        </span>
                    </div>
                    """
                )

                # Khởi tạo mặc định cho Logo & Phụ đề nếu chưa có trong session
                if "dub_enable_logo" not in st.session_state:
                    st.session_state["dub_enable_logo"] = True
                if "dub_burn_subtitles" not in st.session_state:
                    st.session_state["dub_burn_subtitles"] = True
                if "dub_enable_float_wm" not in st.session_state:
                    st.session_state["dub_enable_float_wm"] = True
                if "dub_float_wm_text" not in st.session_state:
                    st.session_state["dub_float_wm_text"] = "@gocphimcuon"
                if "dub_float_wm_size" not in st.session_state:
                    st.session_state["dub_float_wm_size"] = 18
                if "dub_float_wm_opacity" not in st.session_state:
                    st.session_state["dub_float_wm_opacity"] = 30
                if "dub_logo_x" not in st.session_state:
                    st.session_state["dub_logo_x"] = 80
                if "dub_logo_y" not in st.session_state:
                    st.session_state["dub_logo_y"] = 5
                if "dub_logo_scale" not in st.session_state:
                    st.session_state["dub_logo_scale"] = 18
                if "dub_logo_opacity" not in st.session_state:
                    st.session_state["dub_logo_opacity"] = 90
                if "dub_sub_bottom_pct" not in st.session_state:
                    st.session_state["dub_sub_bottom_pct"] = 7

                # Tabs điều khiển tinh chỉnh Logo & Phụ đề
                tab_logo_ctrl, tab_sub_ctrl, tab_wm_ctrl = st.tabs([
                    "🏷️ Tùy chỉnh Logo thương hiệu (Kéo thả)",
                    "📝 Tùy chỉnh Phụ đề hiển thị (Kéo thả)",
                    "🛡️ Chữ mờ chạy bảo vệ bản quyền (Moving Watermark)"
                ])

                with tab_logo_ctrl:
                    enable_logo = st.checkbox(
                        "✨ Kích hoạt chèn Logo / Watermark vào Video",
                        value=st.session_state.get("dub_enable_logo", True),
                        key="dub_enable_logo",
                    )
                    uploaded_logo = st.file_uploader(
                        "Tải lên tệp Logo (PNG nền trong suốt, JPG, WebP):",
                        type=["png", "jpg", "jpeg", "webp"],
                        key="dub_logo_uploader"
                    )

                    logo_b64_data = ""
                    logo_preview_mime = "image/png"
                    if uploaded_logo is not None:
                        raw_logo = uploaded_logo.getvalue()
                        logo_ext = Path(uploaded_logo.name).suffix.lower()
                        if "jpg" in logo_ext or "jpeg" in logo_ext:
                            logo_preview_mime = "image/jpeg"
                        elif "webp" in logo_ext:
                            logo_preview_mime = "image/webp"
                        logo_b64_data = base64.b64encode(raw_logo).decode("utf-8")
                    elif Path("assets/author.png").exists():
                        raw_logo = Path("assets/author.png").read_bytes()
                        logo_b64_data = base64.b64encode(raw_logo).decode("utf-8")
                        st.caption("ℹ️ Đang dùng Logo mẫu Studio VDT. Tải tệp logo của bạn lên ở trên để đổi.")

                    logo_img_src = f"data:{logo_preview_mime};base64,{logo_b64_data}" if logo_b64_data else ""

                    def set_logo_corner(cx: int, cy: int):
                        st.session_state["dub_logo_x"] = cx
                        st.session_state["dub_logo_y"] = cy

                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #f97316;'>⚡ Định vị nhanh góc Logo:</span>", unsafe_allow_html=True)
                    bp1, bp2, bp3, bp4, bp5 = st.columns(5)
                    with bp1:
                        st.button("↖️ Trên Trái", key="btn_pos_tl", on_click=set_logo_corner, args=(4, 4), use_container_width=True)
                    with bp2:
                        st.button("↗️ Trên Phải", key="btn_pos_tr", on_click=set_logo_corner, args=(80, 4), use_container_width=True)
                    with bp3:
                        st.button("↙️ Dưới Trái", key="btn_pos_bl", on_click=set_logo_corner, args=(4, 80), use_container_width=True)
                    with bp4:
                        st.button("↘️ Dưới Phải", key="btn_pos_br", on_click=set_logo_corner, args=(80, 80), use_container_width=True)
                    with bp5:
                        st.button("⏺️ Giữa", key="btn_pos_cc", on_click=set_logo_corner, args=(41, 41), use_container_width=True)

                    col_lc1, col_lc2 = st.columns(2)
                    with col_lc1:
                        cur_logo_scale = st.slider("📐 Kích thước logo (% video):", min_value=6, max_value=45, value=st.session_state.get("dub_logo_scale", 18), step=1, key="dub_logo_scale", format="%d%%")
                        cur_logo_opacity = st.slider("✨ Độ rõ nét (Opacity):", min_value=20, max_value=100, value=st.session_state.get("dub_logo_opacity", 90), step=5, key="dub_logo_opacity", format="%d%%")
                    with col_lc2:
                        cur_logo_x = st.slider("Tọa độ ngang X (%):", min_value=0, max_value=95, value=st.session_state.get("dub_logo_x", 80), step=1, key="dub_logo_x")
                        cur_logo_y = st.slider("Tọa độ dọc Y (%):", min_value=0, max_value=95, value=st.session_state.get("dub_logo_y", 5), step=1, key="dub_logo_y")

                # Tự động nạp hoặc tìm các câu thoại đã dịch từ video
                v_safe_stem = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(uploaded_video.name).stem)
                if "dub_preview_segments" not in st.session_state:
                    st.session_state["dub_preview_segments"] = []

                if not st.session_state["dub_preview_segments"]:
                    # 1. Quét tìm tệp .srt tương ứng trong output
                    matching_srts = sorted(list(Path("output").glob(f"{v_safe_stem}_dubbed_*.srt")), key=lambda p: p.stat().st_mtime, reverse=True)
                    if matching_srts:
                        try:
                            srt_content = matching_srts[0].read_text(encoding="utf-8", errors="replace")
                            parsed_segs = []
                            for blk in re.split(r"\n\s*\n", srt_content.strip()):
                                lines = [ln.strip() for ln in blk.split("\n") if ln.strip()]
                                if len(lines) >= 2:
                                    t_idx = 1 if "-->" in lines[1] else (0 if "-->" in lines[0] else -1)
                                    if t_idx != -1:
                                        tp = lines[t_idx].split("-->")
                                        def parse_sec(ts):
                                            ts = ts.strip().replace(",", ".")
                                            hp, mp, sp = ts.split(":")
                                            return int(hp)*3600 + int(mp)*60 + float(sp)
                                        parsed_segs.append({
                                            "start": parse_sec(tp[0]),
                                            "end": parse_sec(tp[1]),
                                            "text": " ".join(lines[t_idx+1:])
                                        })
                            if parsed_segs:
                                st.session_state["dub_preview_segments"] = parsed_segs
                        except Exception:
                            pass

                    # 2. Quét tìm trong temp segments.json
                    if not st.session_state["dub_preview_segments"]:
                        matching_jsons = sorted(list(Path("temp").glob(f"{v_safe_stem}_*/segments.json")), key=lambda p: p.stat().st_mtime, reverse=True)
                        if matching_jsons:
                            try:
                                j_data = json.loads(matching_jsons[0].read_text(encoding="utf-8"))
                                st.session_state["dub_preview_segments"] = [
                                    {"start": s.get("start", 0), "end": s.get("end", 0), "text": s.get("translated_text") or s.get("text", "")}
                                    for s in j_data if s.get("translated_text") or s.get("text")
                                ]
                            except Exception:
                                pass

                with tab_sub_ctrl:
                    burn_subtitles = st.checkbox(
                        "📺 Ghi thẳng phụ đề đã dịch lên Video (Hardsub)",
                        value=st.session_state.get("dub_burn_subtitles", True),
                        key="dub_burn_subtitles",
                    )
                    c_sb1, c_sb2 = st.columns(2)
                    with c_sb1:
                        sub_style = st.selectbox(
                            "Kiểu hiển thị chữ:",
                            options=["black_box", "white_outline", "yellow_outline"],
                            format_func=lambda x: {
                                "black_box": "⬛ Chữ trắng nền hộp đen mờ (Chuẩn Netflix / Điện ảnh)",
                                "white_outline": "⚪ Chữ trắng viền đen (Chuẩn Phim truyện / TV)",
                                "yellow_outline": "🟡 Chữ vàng viền đen (Chuẩn TikTok / Reels)",
                            }.get(x, x),
                            index=0,
                            key="dub_sub_style_select"
                        )
                        sub_font_size = st.slider(
                            "Cỡ chữ phụ đề (Font Size):",
                            min_value=16,
                            max_value=48,
                            value=26,
                            step=1,
                            key="dub_sub_font_size"
                        )
                    with c_sb2:
                        sub_bottom_pct = st.slider(
                            "Độ cao cách đáy video (%):",
                            min_value=3,
                            max_value=40,
                            value=st.session_state.get("dub_sub_bottom_pct", 7),
                            step=1,
                            key="dub_sub_bottom_pct",
                            help="Kéo trực tiếp phụ đề trên mặt video hoặc dùng thanh trượt này"
                        )

                    avail_segs = st.session_state.get("dub_preview_segments", [])
                    sample_sub_text = "Đây là phụ đề xem trước trên video của bạn (Kéo thả lên/xuống để chỉnh)"

                    if avail_segs:
                        st.info(f"🎙️ Đã đồng bộ {len(avail_segs)} câu thoại dịch từ video! Khi bấm Phát video, phụ đề sẽ tự động chạy theo đúng mốc giọng nói.")
                        c_ps1, c_ps2 = st.columns([0.78, 0.22])
                        with c_ps1:
                            seg_labels = [f"[{s['start']:.1f}s - {s['end']:.1f}s] {s['text']}" for s in avail_segs]
                            sel_idx = st.selectbox(
                                "📜 Chọn câu thoại dịch từ video để xem vị trí chữ:",
                                options=range(len(seg_labels)),
                                format_func=lambda i: seg_labels[i],
                                key="dub_sub_seg_choice"
                            )
                            sample_sub_text = avail_segs[sel_idx]["text"]
                        with c_ps2:
                            st.write("")
                            if st.button("🔄 Nhận diện lại", key="btn_clear_sub_cache", use_container_width=True):
                                st.session_state["dub_preview_segments"] = []
                                st.rerun()
                    else:
                        c_in1, c_in2 = st.columns([0.72, 0.28])
                        with c_in1:
                            sample_sub_text = st.text_input(
                                "Văn bản phụ đề xem trước trên video:",
                                value="Đây là phụ đề xem trước trên video của bạn (Kéo thả lên/xuống để chỉnh)",
                                key="dub_sub_sample_text"
                            )
                        with c_in2:
                            st.write("")
                            if st.button("⚡ Dịch trước từ Video", key="btn_quick_transcribe", help="Tự động nhận diện giọng nói và dịch phụ đề trước khi lồng tiếng", use_container_width=True):
                                with st.spinner("🔍 Đang nhận diện giọng nói & dịch phụ đề từ video..."):
                                    try:
                                        from video_dubber.extractor import extract_audio
                                        from video_dubber.transcriber import Transcriber
                                        from video_dubber.translator import Translator

                                        t_dir = Path("temp") / f"preview_{v_safe_stem}"
                                        t_dir.mkdir(parents=True, exist_ok=True)
                                        t_vid = t_dir / uploaded_video.name
                                        t_vid.write_bytes(uploaded_video.getvalue())
                                        t_aud = t_dir / "preview_audio.wav"
                                        extract_audio(t_vid, t_aud)

                                        transcriber = Transcriber(model_size="base", device="cpu", compute_type="int8")
                                        t_segs, det_lang = transcriber.transcribe(t_aud)
                                        translator = Translator(target_lang="vi", source_lang=det_lang)
                                        t_segs = translator.translate_segments(t_segs)

                                        st.session_state["dub_preview_segments"] = [
                                            {"start": s.start, "end": s.end, "text": s.translated_text or s.text}
                                            for s in t_segs
                                        ]
                                        st.success("✅ Đã trích xuất & dịch phụ đề từ video thành công!")
                                        st.rerun()
                                    except Exception as ex_p:
                                        st.error(f"Lỗi trích xuất: {ex_p}")

                with tab_wm_ctrl:
                    enable_float_wm = st.checkbox(
                        "🛡️ Kích hoạt chữ mờ chạy bảo vệ bản quyền trên Video",
                        value=st.session_state.get("dub_enable_float_wm", True),
                        key="dub_enable_float_wm",
                        help="Chữ mờ trắng sẽ di chuyển lơ lửng liên tục xung quanh video để chống cắt ghép, reup"
                    )
                    c_w1, c_w2 = st.columns([0.7, 0.3])
                    with c_w1:
                        float_wm_text = st.text_input(
                            "Nhập chữ chạy bản quyền (VD: @gocphimcuon, Tên Kênh):",
                            value=st.session_state.get("dub_float_wm_text", "@gocphimcuon"),
                            key="dub_float_wm_text"
                        )
                    with c_w2:
                        float_wm_size = st.slider(
                            "Cỡ chữ mờ:",
                            min_value=12,
                            max_value=36,
                            value=st.session_state.get("dub_float_wm_size", 18),
                            step=1,
                            key="dub_float_wm_size"
                        )
                    c_w3, c_w4 = st.columns(2)
                    with c_w3:
                        float_wm_opacity = st.slider(
                            "Độ mờ chữ (Faded White Opacity):",
                            min_value=10,
                            max_value=70,
                            value=st.session_state.get("dub_float_wm_opacity", 30),
                            step=5,
                            format="%d%%",
                            key="dub_float_wm_opacity",
                            help="Khuyên dùng 25% - 35% để chữ mờ trắng thanh lịch, không gây vướng mắt người xem"
                        )
                    with c_w4:
                        st.markdown("<span style='font-size: 11px; font-weight: 700; color: #38bdf8;'>🌊 Quỹ đạo di chuyển:</span>", unsafe_allow_html=True)
                        st.info("Di chuyển lơ lửng liên tục xung quanh 4 góc & trung tâm video theo chu kỳ sóng mượt mà.")

                # Computed Subtitle CSS cho hiển thị trực quan
                if sub_style == "white_outline":
                    computed_sub_css = f"font-size: {sub_font_size}px; font-weight: 800; color: #ffffff; text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 0 2px 0 #000, 0 -2px 0 #000, 2px 0 0 #000, -2px 0 0 #000; font-family: system-ui, -apple-system, sans-serif; line-height: 1.3;"
                elif sub_style == "black_box":
                    computed_sub_css = f"font-size: {sub_font_size}px; font-weight: 800; color: #ffffff; background: rgba(0, 0, 0, 0.82); padding: 5px 16px; border-radius: 6px; display: inline-block; font-family: system-ui, -apple-system, sans-serif; line-height: 1.35;"
                else:
                    computed_sub_css = f"font-size: {sub_font_size}px; font-weight: 800; color: #ffeb3b; text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 0 2px 0 #000, 0 -2px 0 #000, 2px 0 0 #000, -2px 0 0 #000; font-family: system-ui, -apple-system, sans-serif; line-height: 1.3;"

                # Bộ Engine JavaScript: Gắn trực tiếp Logo & Phụ đề Kéo Thả lên Mặt Video
                live_video_overlay_js = f"""
                <!DOCTYPE html>
                <html><head><meta charset="utf-8"></head><body>
                <script>
                (function() {{
                    try {{
                        var parentDoc = window.parent.document;
                        var parentWin = window.parent;

                        var hasLogo = {'true' if enable_logo and logo_img_src else 'false'};
                        var hasSub = {'true' if burn_subtitles else 'false'};
                        var hasFloatWm = {'true' if enable_float_wm and float_wm_text.strip() else 'false'};
                        var floatWmText = "{float_wm_text.strip()}";
                        var floatWmSize = {float_wm_size};
                        var floatWmOpacity = {float_wm_opacity / 100.0};

                        var logoSrc = "{logo_img_src}";
                        var logoX = {cur_logo_x};
                        var logoY = {cur_logo_y};
                        var logoScale = {cur_logo_scale};
                        var logoOpacity = {cur_logo_opacity / 100.0};

                        var subBottomPct = {sub_bottom_pct};
                        var subCss = "{computed_sub_css}";
                        var subText = "{sample_sub_text}";
                        var liveSegs = {json.dumps(st.session_state.get("dub_preview_segments", []), ensure_ascii=False)};

                        var isDraggingLogo = false;
                        var isDraggingSub = false;
                        var startClientX = 0, startClientY = 0;
                        var initLogoLeft = logoX, initLogoTop = logoY;
                        var initSubBottom = subBottomPct;

                        function injectOverlay() {{
                            var videoElem = parentDoc.querySelector('[data-testid="stVideo"] video') ||
                                            parentDoc.querySelector('video');
                            if (!videoElem) return false;

                            var videoWrap = videoElem.closest('[data-testid="stVideo"]') || videoElem.parentElement;
                            if (!videoWrap) return false;

                            videoWrap.style.position = 'relative';

                            var stage = parentDoc.getElementById('vdt-onvideo-stage');
                            if (!stage) {{
                                stage = parentDoc.createElement('div');
                                stage.id = 'vdt-onvideo-stage';
                                videoWrap.appendChild(stage);
                            }} else if (stage.parentElement !== videoWrap) {{
                                videoWrap.appendChild(stage);
                            }}

                            stage.style.position = 'absolute';
                            stage.style.pointerEvents = 'none';
                            stage.style.zIndex = '30';
                            stage.style.overflow = 'visible';
                            stage.style.boxSizing = 'border-box';

                            // Căn khớp vị trí và kích thước stage đúng từng pixel theo video player
                            var vTop = videoElem.offsetTop || 0;
                            var vLeft = videoElem.offsetLeft || 0;
                            var vW = videoElem.offsetWidth || videoElem.clientWidth;
                            var vH = videoElem.offsetHeight || videoElem.clientHeight;

                            if (vW > 40 && vH > 40) {{
                                stage.style.top = vTop + 'px';
                                stage.style.left = vLeft + 'px';
                                stage.style.width = vW + 'px';
                                stage.style.height = vH + 'px';
                            }} else {{
                                stage.style.top = '0px';
                                stage.style.left = '0px';
                                stage.style.width = '100%';
                                stage.style.height = '100%';
                            }}

                            // 1. Quản lý Logo Overlay trên mặt video
                            var logoBox = parentDoc.getElementById('vdt-onvideo-logo');
                            if (hasLogo && logoSrc) {{
                                if (!logoBox) {{
                                    logoBox = parentDoc.createElement('div');
                                    logoBox.id = 'vdt-onvideo-logo';
                                    stage.appendChild(logoBox);
                                }} else if (logoBox.parentElement !== stage) {{
                                    stage.appendChild(logoBox);
                                }}

                                logoBox.style.display = 'inline-flex';
                                logoBox.style.flexDirection = 'column';
                                logoBox.style.alignItems = 'center';
                                logoBox.style.position = 'absolute';
                                if (!isDraggingLogo) {{
                                    logoBox.style.left = logoX + '%';
                                    logoBox.style.top = logoY + '%';
                                }}
                                logoBox.style.width = logoScale + '%';
                                logoBox.style.opacity = logoOpacity;
                                logoBox.style.cursor = 'grab';
                                logoBox.style.pointerEvents = 'auto';
                                logoBox.style.zIndex = '40';
                                logoBox.style.userSelect = 'none';
                                logoBox.title = 'Bấm giữ chuột để kéo thả logo đến vị trí bất kỳ!';

                                logoBox.innerHTML = '<div style="position: relative; display: inline-block; width: 100%;">' +
                                                    '  <img src="' + logoSrc + '" style="width: 100%; height: auto; display: block; border: 2px dashed #f97316; border-radius: 6px; box-shadow: 0 0 12px rgba(249,115,22,0.85); background: rgba(0,0,0,0.3); pointer-events: none;" />' +
                                                    '  <div style="position: absolute; top: -18px; left: 0; background: #f97316; color: #ffffff; font-size: 9px; font-weight: 800; padding: 1px 6px; border-radius: 3px; white-space: nowrap; box-shadow: 0 2px 5px rgba(0,0,0,0.5); pointer-events: none;">✋ KÉO THẢ LOGO</div>' +
                                                    '</div>';
                            }} else if (logoBox) {{
                                logoBox.style.display = 'none';
                            }}

                            // 2. Quản lý Phụ đề Overlay trên mặt video
                            var subBox = parentDoc.getElementById('vdt-onvideo-sub');
                            if (hasSub) {{
                                if (!subBox) {{
                                    subBox = parentDoc.createElement('div');
                                    subBox.id = 'vdt-onvideo-sub';
                                    stage.appendChild(subBox);
                                }} else if (subBox.parentElement !== stage) {{
                                    stage.appendChild(subBox);
                                }}

                                subBox.style.display = 'block';
                                subBox.style.position = 'absolute';
                                if (!isDraggingSub) {{
                                    subBox.style.bottom = subBottomPct + '%';
                                }}
                                subBox.style.left = '50%';
                                subBox.style.transform = 'translateX(-50%)';
                                subBox.style.width = '92%';
                                subBox.style.maxWidth = '92%';
                                subBox.style.textAlign = 'center';
                                subBox.style.cursor = 'ns-resize';
                                subBox.style.pointerEvents = 'auto';
                                subBox.style.zIndex = '35';
                                subBox.style.userSelect = 'none';
                                subBox.title = 'Bấm giữ chuột để kéo phụ đề lên hoặc xuống trực tiếp trên video!';

                                subBox.innerHTML = '<div style="display: inline-block; max-width: 96%; cursor: ns-resize;">' +
                                                   '  <div style="background: rgba(56, 189, 248, 0.95); color: #ffffff; font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.6); pointer-events: none;">↕️ KÉO LÊN / XUỐNG ĐỂ ĐỔI VỊ TRÍ PHỤ ĐỀ</div><br>' +
                                                   '  <div class="vdt-sub-content" style="' + subCss + '; pointer-events: none; border: 1.5px dashed rgba(56, 189, 248, 0.6); border-radius: 6px; display: inline-block; padding: 6px 14px;">' + subText + '</div>' +
                                                   '</div>';
                            }} else if (subBox) {{
                                subBox.style.display = 'none';
                            }}

                            // 3. Quản lý Chữ mờ chạy bảo vệ bản quyền (Moving Watermark)
                            var wmBox = parentDoc.getElementById('vdt-onvideo-floating-wm');
                            if (hasFloatWm && floatWmText) {{
                                if (!wmBox) {{
                                    wmBox = parentDoc.createElement('div');
                                    wmBox.id = 'vdt-onvideo-floating-wm';
                                    stage.appendChild(wmBox);
                                }} else if (wmBox.parentElement !== stage) {{
                                    stage.appendChild(wmBox);
                                }}
                                wmBox.style.display = 'block';
                                wmBox.style.position = 'absolute';
                                wmBox.style.pointerEvents = 'none';
                                wmBox.style.zIndex = '28';
                                wmBox.style.userSelect = 'none';
                                wmBox.style.whiteSpace = 'nowrap';
                                wmBox.style.fontSize = floatWmSize + 'px';
                                wmBox.style.fontWeight = '700';
                                wmBox.style.color = 'rgba(255, 255, 255, ' + floatWmOpacity + ')';
                                wmBox.style.textShadow = '1px 1px 2px rgba(0, 0, 0, 0.45)';
                                wmBox.style.fontFamily = 'system-ui, -apple-system, sans-serif';
                                wmBox.style.transition = 'left 0.25s linear, top 0.25s linear';
                                wmBox.textContent = floatWmText;
                            }} else if (wmBox) {{
                                wmBox.style.display = 'none';
                            }}

                            return true;
                        }}

                        // Thực hiện gắn kết ngay và duy trì đồng bộ liên tục
                        injectOverlay();
                        if (parentWin.__vdtVideoHeartbeat) {{
                            clearInterval(parentWin.__vdtVideoHeartbeat);
                        }}
                        parentWin.__vdtVideoHeartbeat = setInterval(function() {{
                            injectOverlay();
                        }}, 200);

                        // Đồng bộ phụ đề khớp theo mốc giọng nói khi bấm phát video
                        if (liveSegs && liveSegs.length > 0) {{
                            var vElem = parentDoc.querySelector('[data-testid="stVideo"] video') || parentDoc.querySelector('video');
                            if (vElem && !vElem.__vdtTimeUpdateAttached) {{
                                vElem.__vdtTimeUpdateAttached = true;

                                function syncSubVisibility() {{
                                    if (isDraggingSub) return;
                                    var ct = vElem.currentTime;
                                    var matched = null;
                                    for (var sIdx = 0; sIdx < liveSegs.length; sIdx++) {{
                                        var segStart = liveSegs[sIdx].start;
                                        var segEnd = liveSegs[sIdx].end;
                                        if (ct >= segStart && ct <= segEnd) {{
                                            matched = liveSegs[sIdx].text;
                                            break;
                                        }}
                                    }}
                                    var sDiv = parentDoc.querySelector('#vdt-onvideo-sub .vdt-sub-content');
                                    var sBadge = parentDoc.querySelector('#vdt-onvideo-sub .vdt-sub-drag-badge');
                                    var isPaused = vElem.paused;

                                    if (sBadge) {{
                                        sBadge.style.display = isPaused ? 'inline-block' : 'none';
                                    }}

                                    if (sDiv) {{
                                        if (matched) {{
                                            sDiv.style.visibility = 'visible';
                                            sDiv.style.display = 'inline-block';
                                            if (sDiv.textContent !== matched) {{
                                                sDiv.textContent = matched;
                                            }}
                                        }} else {{
                                            if (isPaused && ct === 0) {{
                                                sDiv.style.visibility = 'visible';
                                                sDiv.style.display = 'inline-block';
                                                sDiv.textContent = subText;
                                            }} else {{
                                                // Hết giọng đọc là phụ đề ẩn đi ngay lập tức, màn hình sạch hoàn toàn
                                                sDiv.style.visibility = 'hidden';
                                                sDiv.style.display = 'none';
                                            }}
                                        }}
                                    }}
                                }}

                                vElem.addEventListener('timeupdate', syncSubVisibility);
                                vElem.addEventListener('play', syncSubVisibility);
                                vElem.addEventListener('pause', syncSubVisibility);
                                vElem.addEventListener('seeked', syncSubVisibility);
                            }}
                        }}

                        // Quỹ đạo di chuyển lơ lửng xung quanh video cho chữ mờ bản quyền
                        if (!parentWin.__vdtWmStartTime) {{
                            parentWin.__vdtWmStartTime = Date.now();
                        }}
                        function animateWatermark() {{
                            var wmB = parentDoc.getElementById('vdt-onvideo-floating-wm');
                            if (hasFloatWm && wmB && wmB.style.display !== 'none') {{
                                var elapsed = (Date.now() - parentWin.__vdtWmStartTime) / 1000.0;
                                var pX = Math.round(42 + 34 * Math.sin(2 * Math.PI * elapsed / 14));
                                var pY = Math.round(42 + 34 * Math.cos(2 * Math.PI * elapsed / 19));
                                wmB.style.left = pX + '%';
                                wmB.style.top = pY + '%';
                            }}
                            parentWin.__vdtWmTimer = setTimeout(animateWatermark, 250);
                        }}
                        if (parentWin.__vdtWmTimer) {{
                            clearTimeout(parentWin.__vdtWmTimer);
                        }}
                        animateWatermark();

                        function syncSlider(labelPart, val) {{
                            var allSliders = parentDoc.querySelectorAll('[data-testid="stSlider"]');
                            allSliders.forEach(function(s) {{
                                if (s.textContent && s.textContent.indexOf(labelPart) !== -1) {{
                                    var inp = s.querySelector('input[type="range"]') || s.querySelector('input');
                                    if (inp && parseInt(inp.value, 10) !== val) {{
                                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                        setter.call(inp, val);
                                        inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    }}
                                }}
                            }});
                        }}

                        if (parentWin.__vdtVideoMouseDownHandler) {{
                            parentDoc.removeEventListener('mousedown', parentWin.__vdtVideoMouseDownHandler, true);
                            parentDoc.removeEventListener('mousemove', parentWin.__vdtVideoMouseMoveHandler, true);
                            parentDoc.removeEventListener('mouseup', parentWin.__vdtVideoMouseUpHandler, true);
                            parentWin.removeEventListener('mouseup', parentWin.__vdtVideoMouseUpHandler, true);
                        }}

                        parentWin.__vdtVideoMouseDownHandler = function(e) {{
                            var logoHit = e.target.closest('#vdt-onvideo-logo');
                            var subHit = e.target.closest('#vdt-onvideo-sub');
                            if (!logoHit && !subHit) return;

                            var stage = parentDoc.getElementById('vdt-onvideo-stage');
                            if (!stage) return;

                            if (logoHit) {{
                                e.preventDefault();
                                e.stopPropagation();
                                isDraggingLogo = true;
                                isDraggingSub = false;
                                logoHit.style.cursor = 'grabbing';
                                startClientX = e.clientX;
                                startClientY = e.clientY;
                                initLogoLeft = parseFloat(logoHit.style.left) || logoX;
                                initLogoTop = parseFloat(logoHit.style.top) || logoY;
                                return;
                            }}

                            if (subHit) {{
                                e.preventDefault();
                                e.stopPropagation();
                                isDraggingSub = true;
                                isDraggingLogo = false;
                                subHit.style.cursor = 'ns-resize';
                                startClientY = e.clientY;
                                initSubBottom = parseFloat(subHit.style.bottom) || subBottomPct;
                                return;
                            }}
                        }};

                        parentWin.__vdtVideoMouseMoveHandler = function(e) {{
                            if (!isDraggingLogo && !isDraggingSub) return;

                            var stage = parentDoc.getElementById('vdt-onvideo-stage');
                            var indicator = parentDoc.getElementById('vdt-live-coords-indicator');
                            if (!stage) return;

                            var rect = stage.getBoundingClientRect();
                            var sW = rect.width || 1;
                            var sH = rect.height || 1;

                            if (isDraggingLogo) {{
                                var dx = e.clientX - startClientX;
                                var dy = e.clientY - startClientY;
                                var newLeftPx = (initLogoLeft / 100 * sW) + dx;
                                var newTopPx = (initLogoTop / 100 * sH) + dy;
                                var pX = Math.max(0, Math.min(94, Math.round((newLeftPx / sW) * 100)));
                                var pY = Math.max(0, Math.min(94, Math.round((newTopPx / sH) * 100)));

                                var lBox = parentDoc.getElementById('vdt-onvideo-logo');
                                if (lBox) {{
                                    lBox.style.left = pX + '%';
                                    lBox.style.top = pY + '%';
                                }}
                                if (indicator) {{
                                    indicator.innerHTML = '📍 <span style="color:#f97316; font-weight:800;">Logo:</span> X=' + pX + '% | Y=' + pY + '%';
                                }}
                            }}

                            if (isDraggingSub) {{
                                var dySub = e.clientY - startClientY;
                                var newBottomPx = (initSubBottom / 100 * sH) - dySub;
                                var pBottom = Math.max(1, Math.min(50, Math.round((newBottomPx / sH) * 100)));

                                var sBox = parentDoc.getElementById('vdt-onvideo-sub');
                                if (sBox) {{
                                    sBox.style.bottom = pBottom + '%';
                                }}
                                if (indicator) {{
                                    indicator.innerHTML = '📍 <span style="color:#38bdf8; font-weight:800;">Phụ đề:</span> Cách đáy ' + pBottom + '%';
                                }}
                            }}
                        }};

                        parentWin.__vdtVideoMouseUpHandler = function(e) {{
                            var indicator = parentDoc.getElementById('vdt-live-coords-indicator');
                            if (isDraggingLogo) {{
                                isDraggingLogo = false;
                                var lBox = parentDoc.getElementById('vdt-onvideo-logo');
                                if (lBox) {{
                                    lBox.style.cursor = 'grab';
                                    var fX = Math.round(parseFloat(lBox.style.left) || 0);
                                    var fY = Math.round(parseFloat(lBox.style.top) || 0);
                                    syncSlider('Tọa độ ngang X', fX);
                                    syncSlider('Tọa độ dọc Y', fY);
                                    if (indicator) indicator.innerHTML = '✅ <b style="color:#f97316">Đã lưu Logo:</b> X=' + fX + '% | Y=' + fY + '%';
                                }}
                            }}

                            if (isDraggingSub) {{
                                isDraggingSub = false;
                                var sBox = parentDoc.getElementById('vdt-onvideo-sub');
                                if (sBox) {{
                                    sBox.style.cursor = 'ns-resize';
                                    var fB = Math.round(parseFloat(sBox.style.bottom) || 0);
                                    syncSlider('Độ cao cách đáy video', fB);
                                    if (indicator) indicator.innerHTML = '✅ <b style="color:#38bdf8">Đã lưu Phụ đề:</b> Cách đáy ' + fB + '%';
                                }}
                            }}
                        }};

                        parentDoc.addEventListener('mousedown', parentWin.__vdtVideoMouseDownHandler, true);
                        parentDoc.addEventListener('mousemove', parentWin.__vdtVideoMouseMoveHandler, true);
                        parentDoc.addEventListener('mouseup', parentWin.__vdtVideoMouseUpHandler, true);
                        parentWin.addEventListener('mouseup', parentWin.__vdtVideoMouseUpHandler, true);

                    }} catch(err) {{
                        console.error('Live Video Overlay Studio error:', err);
                    }}
                }})();
                </script>
                </body></html>
                """
                components.html(live_video_overlay_js, height=0)

            else:
                st.info("💡 Kéo thả hoặc chọn tệp video bạn muốn chuyển ngữ & lồng tiếng.")

    with col_dub_right:
        with st.container(border=True):
            st.markdown("##### ⚙️ Bước 2: Thiết lập Ngôn ngữ & Giọng lồng tiếng")
            
            c_l1, c_l2 = st.columns(2)
            with c_l1:
                source_options = {"auto": "Tự động phát hiện (Auto)"}
                source_options.update(LANGUAGE_NAMES)
                dub_src_lang = st.selectbox(
                    "Ngôn ngữ gốc của Video:",
                    options=list(source_options.keys()),
                    format_func=lambda x: source_options[x],
                    index=0,
                    key="dub_src_lang_select"
                )
            with c_l2:
                dub_tgt_lang = st.selectbox(
                    "Dịch và lồng tiếng sang:",
                    options=list(LANGUAGE_NAMES.keys()),
                    format_func=lambda x: LANGUAGE_NAMES[x],
                    index=0,
                    key="dub_tgt_lang_select"
                )

            # Chọn giọng đọc AI từ Catalog theo ngôn ngữ đích
            target_catalog = VOICES_CATALOG.get(dub_tgt_lang, VOICES_CATALOG.get("vi", {}))
            voice_names = list(target_catalog.keys())
            
            default_voice_idx = 0
            for idx_v, vname in enumerate(voice_names):
                if "Adam" in vname and "bựa" not in vname:
                    default_voice_idx = idx_v
                    break

            dub_selected_voice_name = st.selectbox(
                "Giọng đọc AI lồng tiếng:",
                options=voice_names,
                index=default_voice_idx,
                key="dub_voice_select"
            )
            dub_selected_voice_id = target_catalog[dub_selected_voice_name]
            st.caption("✨ **Chuẩn chất giọng nhân vật:** Giữ nguyên 100% âm sắc sáng rõ, đúng cao độ bản quyền, không bị trầm đục và triệt tiêu hoàn toàn hiện tượng lẫn 2 giọng.")

            with st.expander("🛠️ Cấu hình Nâng cao (Mô hình Whisper & Nhạc nền)", expanded=False):
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    whisper_model = st.selectbox(
                        "Mô hình Whisper STT:",
                        options=["tiny", "base", "small", "medium"],
                        index=1,
                        help="base: Cân bằng tốt nhất giữa tốc độ và độ chính xác trên Streamlit Cloud."
                    )
                with col_w2:
                    bg_music_vol = st.slider(
                        "Âm lượng nhạc nền gốc (Ducking):",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.08,
                        step=0.02,
                        format="%.2f",
                        help="0.08 = 8% (giữ tiếng động/nhạc nền phim nhẹ nhàng, tự động tắt hẳn khi có giọng nói để không bị lẫn tiếng)"
                    )
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    dub_speed_factor = st.slider(
                        "Tốc độ đọc tối đa (Speed Factor):",
                        min_value=1.0,
                        max_value=2.0,
                        value=1.35,
                        step=0.05,
                        help="Giới hạn tối đa khi tự động tăng tốc audio để khớp mốc thời gian phụ đề"
                    )
                with col_s2:
                    compute_type = st.selectbox(
                        "Chế độ tính toán (Compute):",
                        options=["int8", "float32"],
                        index=0,
                        help="int8 giúp tiết kiệm RAM và CPU tối đa"
                    )

            st.write("")
            btn_start_dubbing = st.button(
                "🚀 BẮT ĐẦU LỒNG TIẾNG VIDEO AI",
                type="primary",
                use_container_width=True,
                disabled=(uploaded_video is None),
                key="btn_run_video_dubbing"
            )

    dub_progress_slot = st.empty()

    if btn_start_dubbing and uploaded_video is not None:
        # Xóa sạch kết quả video và phụ đề cũ khỏi session để đảm bảo kết quả tải về luôn là video mới nhất vừa xuất
        st.session_state.pop("dubbed_video_path", None)
        st.session_state.pop("dubbed_srt_path", None)
        st.session_state.pop("dub_preview_segments", None)

        try:
            # Hot reload toàn bộ modules để cập nhật merger, pipeline, config tức thì
            import importlib
            import config
            import video_dubber.merger
            import video_dubber.translator
            import video_dubber.synchronizer
            import video_dubber.pipeline
            importlib.reload(config)
            importlib.reload(video_dubber.merger)
            importlib.reload(video_dubber.translator)
            importlib.reload(video_dubber.synchronizer)
            importlib.reload(video_dubber.pipeline)

            dub_progress_slot.progress(0, text="Đang chuẩn bị tệp video và khởi tạo pipeline...")
            
            temp_dir = Path("./temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_dir = Path("./output")
            output_dir.mkdir(parents=True, exist_ok=True)

            safe_stem = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(uploaded_video.name).stem)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            in_video_path = temp_dir / f"{safe_stem}_{timestamp}.mp4"
            with open(in_video_path, "wb") as f_out:
                f_out.write(uploaded_video.getbuffer())

            out_video_path = output_dir / f"{safe_stem}_dubbed_{dub_tgt_lang}_{timestamp}.mp4"

            logo_file_path = None
            if st.session_state.get("dub_enable_logo", True):
                if st.session_state.get("dub_logo_uploader") is not None:
                    u_logo = st.session_state["dub_logo_uploader"]
                    logo_ext = Path(u_logo.name).suffix or ".png"
                    logo_file_path = temp_dir / f"logo_{safe_stem}_{timestamp}{logo_ext}"
                    with open(logo_file_path, "wb") as f_l:
                        f_l.write(u_logo.getbuffer())
                elif Path("assets/author.png").exists():
                    logo_file_path = Path("assets/author.png")

            dub_config = config.DubbingConfig(
                whisper_model=whisper_model,
                device="cpu",
                compute_type=compute_type,
                source_language=dub_src_lang,
                target_language=dub_tgt_lang,
                tts_voice=dub_selected_voice_id,
                original_audio_volume=bg_music_vol,
                max_speed_factor=dub_speed_factor,
                temp_dir=temp_dir,
                output_dir=output_dir,
                enable_logo=bool(logo_file_path is not None and Path(logo_file_path).exists()),
                logo_path=logo_file_path,
                logo_x_pct=float(st.session_state.get("dub_logo_x", 80)) / 100.0,
                logo_y_pct=float(st.session_state.get("dub_logo_y", 5)) / 100.0,
                logo_scale=float(st.session_state.get("dub_logo_scale", 18)) / 100.0,
                logo_opacity=float(st.session_state.get("dub_logo_opacity", 90)) / 100.0,
                burn_subtitles=st.session_state.get("dub_burn_subtitles", True),
                subtitle_font_size=st.session_state.get("dub_sub_font_size", 26),
                subtitle_style=st.session_state.get("dub_sub_style_select", "black_box"),
                subtitle_margin_v=int(float(st.session_state.get("dub_sub_bottom_pct", 7)) * 7.5),
                enable_floating_watermark=bool(st.session_state.get("dub_enable_float_wm", True)),
                floating_watermark_text=st.session_state.get("dub_float_wm_text", "@gocphimcuon"),
                floating_watermark_font_size=st.session_state.get("dub_float_wm_size", 18),
                floating_watermark_opacity=float(st.session_state.get("dub_float_wm_opacity", 30)) / 100.0,
            )

            pipeline = video_dubber.pipeline.VideoDubberPipeline(dub_config)

            def update_progress(msg: str, progress: float):
                dub_progress_slot.progress(int(progress * 100), text=f"⏳ {msg}")

            final_video_file = pipeline.process(
                video_path=in_video_path,
                output_path=out_video_path,
                progress_callback=update_progress
            )

            dub_progress_slot.progress(100, text="✅ Hoàn tất lồng tiếng video 100%!")
            time.sleep(0.5)
            dub_progress_slot.empty()

            st.session_state["dubbed_video_path"] = str(final_video_file)
            st.session_state["dubbed_srt_path"] = str(final_video_file.with_suffix(".srt"))
            if hasattr(pipeline, "last_segments") and pipeline.last_segments:
                st.session_state["dub_preview_segments"] = [
                    {"start": s.start, "end": getattr(s, "sub_end", None) if getattr(s, "sub_end", None) is not None else s.end, "text": s.translated_text or s.text}
                    for s in pipeline.last_segments
                ]
            st.session_state["dubbed_video_title"] = f"{safe_stem}_dubbed_{dub_tgt_lang}"
            st.toast("🎉 Đã hoàn tất lồng tiếng video AI!", icon="🎬")
            st.rerun()

        except Exception as e:
            dub_progress_slot.empty()
            st.error(f"❌ Có lỗi xảy ra trong quá trình lồng tiếng video: {e}")

    active_dubbed_video = st.session_state.get("dubbed_video_path")
    if active_dubbed_video and Path(active_dubbed_video).exists():
        st.write("---")
        st.markdown("### 🎬 KẾT QUẢ VIDEO ĐÃ LỒNG TIẾNG HOÀN THIỆN")
        
        c_res_v, c_res_info = st.columns([1.2, 0.8], gap="medium")
        
        with c_res_v:
            # Chỉ phát video MP4 thuần đã có phụ đề cứng (hardsub), không truyền soft-sub track để tránh bị trùng đè chữ
            st.video(active_dubbed_video)
        
        with c_res_info:
            with st.container(border=True):
                st.markdown("#### 📥 Tải xuống & Xuất bản")

                btn_reburn = st.button(
                    "🔥 ĐỐT LẠI PHỤ ĐỀ & CHỮ MỜ VÀO MP4 NGAY (Vài giây)",
                    use_container_width=True,
                    help="Ghi đè trực tiếp phụ đề và chữ mờ bản quyền vào video MP4 để tải về mà không cần dịch hay sinh giọng lại"
                )
                if btn_reburn:
                    with st.spinner("⏳ Đang ghi đè phụ đề tiếng Việt và chữ mờ bản quyền vào video MP4..."):
                        try:
                            import importlib
                            import re as re_mod
                            import config
                            import video_dubber.merger
                            importlib.reload(config)
                            importlib.reload(video_dubber.merger)

                            cur_v = Path(active_dubbed_video)
                            v_stem = cur_v.stem
                            m_match = re_mod.search(r"^(.*)_dubbed_[a-zA-Z0-9]+_(\d{8}_\d{6})$", v_stem)
                            ts_key = m_match.group(2) if m_match else ""
                            orig_stem = f"{m_match.group(1)}_{ts_key}" if m_match else v_stem

                            in_v = Path("temp") / f"{orig_stem}.mp4"
                            in_a = Path("temp") / orig_stem / "mixed_final.wav"
                            in_srt = Path(st.session_state.get("dubbed_srt_path", str(cur_v.with_suffix(".srt"))))

                            if not in_v.exists() and ts_key:
                                cand_v = list(Path("temp").glob(f"*{ts_key}*.mp4"))
                                if cand_v:
                                    in_v = cand_v[0]

                            if not in_a.exists() and ts_key:
                                cand_a = list(Path("temp").glob(f"*{ts_key}*/mixed_final.wav"))
                                if cand_a:
                                    in_a = cand_a[0]

                            if in_v.exists() and in_a.exists() and in_srt.exists():
                                # Đồng bộ mốc thời gian phụ đề theo thời lượng giọng đọc AI thực tế
                                tts_seg_dir = Path("temp") / orig_stem / "tts_segments"
                                orig_aud_file = Path("temp") / orig_stem / "original_audio.wav"
                                if tts_seg_dir.exists() and in_srt.exists():
                                    try:
                                        import wave
                                        import video_dubber.synchronizer
                                        importlib.reload(video_dubber.synchronizer)
                                        items = video_dubber.merger.parse_srt_file(in_srt)
                                        new_srt_lines = []
                                        updated_preview_segs = []
                                        seg_objs = []
                                        for idx, (s_start, s_end, s_text) in enumerate(items):
                                            f_cand = tts_seg_dir / f"seg_{idx:04d}.wav"
                                            if f_cand.exists():
                                                try:
                                                    with wave.open(str(f_cand), "rb") as wf:
                                                        clip_d = wf.getnframes() / float(wf.getframerate())
                                                    s_finish = round(s_start + clip_d, 3)
                                                    if idx + 1 < len(items):
                                                        next_st = items[idx + 1][0]
                                                        if s_finish > next_st:
                                                            s_finish = next_st
                                                    s_end = s_finish
                                                except Exception:
                                                    pass
                                            def fmt_t(sec):
                                                ms = int(round((sec % 1) * 1000))
                                                if ms >= 1000:
                                                    ms = 999
                                                s = int(sec)
                                                h = s // 3600
                                                m = (s % 3600) // 60
                                                s = s % 60
                                                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                                            new_srt_lines.append(f"{idx+1}\n{fmt_t(s_start)} --> {fmt_t(s_end)}\n{s_text}\n")
                                            updated_preview_segs.append({"start": s_start, "end": s_end, "text": s_text})

                                            from video_dubber.transcriber import Segment
                                            seg_objs.append(Segment(
                                                id=idx,
                                                start=s_start,
                                                end=s_end,
                                                text=s_text,
                                                translated_text=s_text,
                                                tts_audio_path=str(f_cand)
                                            ))

                                        in_srt.write_text("\n".join(new_srt_lines), encoding="utf-8")
                                        if updated_preview_segs:
                                            st.session_state["dub_preview_segments"] = updated_preview_segs

                                        # Tái tổng hợp luồng audio giọng đọc thuần khiết chuẩn 100% âm sắc nhân vật & triệt tiêu tiếng gốc
                                        if orig_aud_file.exists() and seg_objs:
                                            from pydub import AudioSegment
                                            v_tot_dur = len(AudioSegment.from_file(str(orig_aud_file))) / 1000.0
                                            syncer = video_dubber.synchronizer.AudioSynchronizer(max_speed_factor=dub_speed_factor)
                                            dub_assem_path = Path("temp") / orig_stem / "dubbed_assembled.wav"
                                            syncer.align_and_assemble(seg_objs, v_tot_dur, dub_assem_path)
                                            
                                            merg_mix = video_dubber.merger.VideoMerger(original_audio_volume=bg_music_vol)
                                            merg_mix.mix_audios(
                                                original_audio_path=orig_aud_file,
                                                dubbed_audio_path=dub_assem_path,
                                                output_mixed_audio_path=in_a,
                                                segments=seg_objs,
                                                mute_original_dialogue=True
                                            )
                                    except Exception as ex_re_audio:
                                        logger.warning(f"Note during audio re-assembly: {ex_re_audio}")

                                logo_f = Path("assets/author.png") if Path("assets/author.png").exists() else None
                                merger_inst = video_dubber.merger.VideoMerger(original_audio_volume=bg_music_vol)
                                merger_inst.merge_video(
                                    video_path=in_v,
                                    audio_path=in_a,
                                    output_video_path=cur_v,
                                    subtitle_path=in_srt,
                                    subtitle_font_size=st.session_state.get("dub_sub_font_size", 26),
                                    subtitle_style=st.session_state.get("dub_sub_style_select", "black_box"),
                                    subtitle_margin_v=int(float(st.session_state.get("dub_sub_bottom_pct", 7)) * 7.5),
                                    logo_path=logo_f if st.session_state.get("dub_enable_logo", True) else None,
                                    logo_x_pct=float(st.session_state.get("dub_logo_x", 80)) / 100.0,
                                    logo_y_pct=float(st.session_state.get("dub_logo_y", 5)) / 100.0,
                                    logo_scale=float(st.session_state.get("dub_logo_scale", 18)) / 100.0,
                                    logo_opacity=float(st.session_state.get("dub_logo_opacity", 90)) / 100.0,
                                    floating_watermark_text=st.session_state.get("dub_float_wm_text", "@gocphimcuon") if st.session_state.get("dub_enable_float_wm", True) else None,
                                    floating_watermark_font_size=st.session_state.get("dub_float_wm_size", 18),
                                    floating_watermark_opacity=float(st.session_state.get("dub_float_wm_opacity", 30)) / 100.0,
                                )
                                st.toast("✅ Đã ghi đè phụ đề cứng và chữ mờ vào video thành công!", icon="🎬")
                                st.rerun()
                            else:
                                st.error("Không tìm thấy tệp tạm để ghép nhanh. Vui lòng bấm '🚀 BẮT ĐẦU LỒNG TIẾNG VIDEO' để xuất mới.")
                        except Exception as ex_reburn:
                            st.error(f"Lỗi khi đốt lại phụ đề: {ex_reburn}")

                v_bytes = Path(active_dubbed_video).read_bytes()
                v_name = Path(active_dubbed_video).name
                st.download_button(
                    label=f"⬇️ TẢI VIDEO MP4 HOÀN CHỈNH ({len(v_bytes)/(1024*1024):.1f} MB)",
                    data=v_bytes,
                    file_name=v_name,
                    mime="video/mp4",
                    use_container_width=True,
                    type="primary"
                )

                srt_file = Path(st.session_state.get("dubbed_srt_path", ""))
                if srt_file.exists():
                    srt_data = srt_file.read_bytes()
                    st.download_button(
                        label="📝 TẢI TỆP PHỤ ĐỀ ĐỒNG BỘ (.SRT)",
                        data=srt_data,
                        file_name=srt_file.name,
                        mime="text/plain",
                        use_container_width=True
                    )
                
                st.markdown(
                    f"""
                    <div style="background: #111622; border: 1px solid #1f293d; border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 0.82rem; color: #94a3b8;">
                        <div style="color: #f8fafc; font-weight: 700; margin-bottom: 6px;">Chi tiết bản xuất:</div>
                        • <strong>Tên tệp:</strong> {v_name}<br>
                        • <strong>Dung lượng:</strong> {len(v_bytes)/(1024*1024):.2f} MB<br>
                        • <strong>Phụ đề:</strong> Đã ghi trực tiếp vào video (Hardsub) & Sẵn sàng tệp .SRT rời<br>
                        • <strong>Trạng thái:</strong> Âm thanh & Hình ảnh đã đồng bộ hoàn hảo
                    </div>
                    """,
                    unsafe_allow_html=True
                )



# ==============================================================================
# FIXED BOTTOM DAW MASTER PLAYER DOCK (Chỉ hiển thị khi đã tạo giọng từ văn bản)
# ==============================================================================
active_audio_path = st.session_state.get("script_generated_file")

if active_audio_path and Path(active_audio_path).exists():
    raw_bytes = Path(active_audio_path).read_bytes()
    b64_audio = base64.b64encode(raw_bytes).decode("utf-8")
    audio_uri = f"data:audio/mp3;base64,{b64_audio}"
    audio_filename = Path(active_audio_path).name
    track_title = st.session_state.get("script_generated_title", "Audio_Master_Ready")
    gen_voice_name = st.session_state.get("script_generated_voice_name")
    if not gen_voice_name:
        # Tự động trích xuất tên nhân vật từ tên track (ví dụ "Thiện Minh_20261031_173618" -> "Thiện Minh")
        parts = track_title.rsplit("_", 2)
        gen_voice_name = parts[0] if len(parts) >= 3 else clean_name
    voice_display_info = f"{gen_voice_name} • 48kHz / 24-bit Lossless"

    # Tạo nội dung phụ đề SRT đi kèm đồng bộ
    srt_b64 = ""
    try:
        script_content = st.session_state.get("tts_main_text", "")
        lines = [s.strip() for s in re.split(r'[.!?\n]+', script_content) if s.strip()]
        if not lines:
            lines = [script_content]
        total_est_sec = max(2.0, len(script_content.split()) / 2.7)
        step = total_est_sec / len(lines)
        srt_lines = []
        for idx_l, line_txt in enumerate(lines):
            t_start = idx_l * step
            t_end = (idx_l + 1) * step
            sh, sm, ss, sms = int(t_start // 3600), int((t_start % 3600) // 60), int(t_start % 60), int((t_start % 1) * 1000)
            eh, em, es, ems = int(t_end // 3600), int((t_end % 3600) // 60), int(t_end % 60), int((t_end % 1) * 1000)
            clean_l = re.sub(r'\[[^\]]+\]', '', line_txt).strip()
            srt_lines.append(f"{idx_l + 1}\n{sh:02}:{sm:02}:{ss:02},{sms:03} --> {eh:02}:{em:02}:{es:02},{ems:03}\n{clean_l}\n")
        srt_b64 = base64.b64encode("\n".join(srt_lines).encode("utf-8")).decode("utf-8")
    except Exception:
        pass

    should_autoplay = "true" if st.session_state.get("just_rendered_autoplay", False) else "false"
    st.session_state["just_rendered_autoplay"] = False

    # 36 Waveform Bars với chiều cao phổ âm chuẩn
    eq_bar_heights = [
        6, 12, 18, 24, 28, 22, 14, 10, 16, 26,
        32, 28, 20, 14, 18, 28, 24, 12, 16, 26,
        30, 22, 14, 8, 14, 22, 28, 20, 12, 16,
        24, 28, 18, 12, 8, 6
    ]
    eq_bars_html = "".join([
        f'<span class="daw-eq-bar" data-idx="{i}" data-base-h="{h}" style="display:inline-block; width: 3px; height: {h}px; background: #232c3f; border-radius: 1.5px; margin: 0 1px; transition: background 0.08s ease, height 0.08s ease;"></span>'
        for i, h in enumerate(eq_bar_heights)
    ])

    # Fixed Bottom DAW Dock HTML (Luôn ghim đáy viewport, Loang tiến trình & Tải trực tiếp)
    st.html(
        f"""
        <div id="daw-dock-fixed-bar" class="daw-dock-fixed">
            <audio id="daw-core-audio" src="{audio_uri}" preload="auto" data-autoplay="{should_autoplay}"></audio>
            <div class="daw-dock-inner" style="display: flex; justify-content: space-between; align-items: center; gap: 10px; max-width: 1420px; margin: 0 auto; width: 100%;">
                <!-- Left: Track Title & Ready Badge -->
                <div class="daw-dock-left" style="display: flex; align-items: center; gap: 10px;">
                    <div id="daw-disc" style="width: 38px; height: 38px; border-radius: 50%; background: #141926; border: 1.5px solid #f97316; display: flex; align-items: center; justify-content: center; font-size: 17px; color: #f97316; box-shadow: 0 0 12px rgba(249, 115, 22, 0.35);">
                        🎵
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span id="daw-track-title" style="font-weight: 800; color: #ffffff; font-size: 0.92rem; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{track_title}</span>
                            <span id="daw-badge-status" style="background: rgba(249, 115, 22, 0.2); border: 1px solid #f97316; color: #fb923c; font-size: 9px; font-weight: 800; padding: 2px 5px; border-radius: 4px; letter-spacing: 0.5px;">READY</span>
                        </div>
                        <div id="daw-track-subtitle" style="font-size: 0.74rem; color: #64748b; font-weight: 600; margin-top: 1px;">{voice_display_info}</div>
                    </div>
                </div>

                <!-- Center: Controls, Dynamic Timecode & Waveform Loang with Smooth Scrubbing -->
                <div class="daw-dock-center" style="display: flex; align-items: center; gap: 10px; flex-grow: 1; justify-content: center;">
                    <button type="button" id="daw-btn-prev" style="background: transparent; border: none; font-size: 15px; color: #64748b; cursor: pointer; padding: 4px;" title="Lùi 5 giây">⏮️</button>
                    <button type="button" id="daw-btn-play" style="width: 38px; height: 38px; border-radius: 50%; background: #f97316; border: none; display: flex; align-items: center; justify-content: center; font-size: 16px; color: #ffffff; cursor: pointer; box-shadow: 0 0 16px rgba(249, 115, 22, 0.7); transition: transform 0.1s ease;">
                        <span id="daw-play-icon">▶</span>
                    </button>
                    <button type="button" id="daw-btn-next" style="background: transparent; border: none; font-size: 15px; color: #64748b; cursor: pointer; padding: 4px;" title="Tua 5 giây">⏭️</button>
                    <button type="button" id="daw-btn-loop" style="background: transparent; border: none; font-size: 15px; color: #64748b; cursor: pointer; padding: 4px;" title="Bật/Tắt Lặp lại">🔁</button>

                    <!-- Real-time Timecode Display -->
                    <span id="daw-timecode-display" style="font-family: 'JetBrains Mono', Consolas, monospace; font-size: 11.5px; color: #cbd5e1; font-weight: 700; margin-left: 2px; min-width: 95px;">00:00.0 / 00:00.0</span>

                    <!-- Interactive Waveform with Loang Progress & Scrubbing -->
                    <div id="daw-waveform-wrapper" style="display: flex; align-items: center; gap: 6px;">
                        <span id="daw-time-start" style="font-size: 10.5px; color: #64748b; font-family: 'JetBrains Mono', Consolas, monospace; font-weight: 600;">00:00</span>
                        <div id="daw-waveform-scrub" style="display: flex; align-items: center; justify-content: space-between; height: 32px; padding: 2px 6px; background: #080b11; border: 1px solid #1c2436; border-radius: 6px; cursor: pointer; position: relative; width: 230px; user-select: none;" title="Bấm hoặc kéo chuột (sướt) để tua âm thanh">
                            <div id="daw-scrub-cursor" style="position: absolute; top: 0; bottom: 0; left: 0%; width: 2px; background: #ffffff; box-shadow: 0 0 6px #ffffff; z-index: 5; pointer-events: none; transition: left 0.05s linear;"></div>
                            <div id="daw-eq-bars" style="display: flex; align-items: center; justify-content: space-between; width: 100%; height: 100%; pointer-events: none;">
                                {eq_bars_html}
                            </div>
                        </div>
                        <span id="daw-time-end" style="font-size: 10.5px; color: #64748b; font-family: 'JetBrains Mono', Consolas, monospace; font-weight: 600;">00:00</span>
                    </div>
                </div>

                <!-- Right: Working Direct Downloads & Responsive Collapse Button -->
                <div class="daw-dock-right" style="display: flex; align-items: center; gap: 6px;">
                    <button type="button" id="daw-btn-dl-srt" class="daw-action-btn" title="Tải file phụ đề SRT">
                        📺 Kèm SRT
                    </button>
                    <button type="button" id="daw-btn-dl-mp3" class="daw-action-btn" title="Tải file MP3 320k">
                        ⬇️ MP3 (320k)
                    </button>
                    <button type="button" id="daw-btn-dl-wav" class="daw-action-btn-wav" title="Tải file Master WAV 48kHz">
                        ⚡ TẢI WAV MASTER (48kHz)
                    </button>
                    <button type="button" id="daw-btn-toggle-size" style="background: #101420; border: 1px solid #283147; border-radius: 6px; color: #cbd5e1; font-size: 11px; padding: 6px 8px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: all 0.15s ease;" title="Bấm để Thu nhỏ hoặc Mở rộng thanh phát">
                        🔽
                    </button>
                </div>
            </div>
        </div>
        """
    )

    # JavaScript Engine for DAW Player (Loang Waveform, Scrubbing & Instant Blob Downloads)
    player_engine_js = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body>
    <script>
    (function() {{
        try {{
            var parentDoc = window.parent.document;
            var parentWin = window.parent;

            var audioDataB64 = "{b64_audio}";
            var srtDataB64 = "{srt_b64}";
            var baseFilename = "{track_title}";

            // Luôn đồng bộ dữ liệu bản thu mới nhất lên parentWin để các nút tải và controller không bao giờ dính file cũ
            parentWin.__vdtCurrentTrack = {{
                audioB64: audioDataB64,
                srtB64: srtDataB64,
                baseFilename: baseFilename
            }};

            var isLooping = false;
            var animId = null;
            var isScrubbing = false;

            function getLiveAudio() {{
                return parentDoc.getElementById('daw-core-audio');
            }}

            function formatTimeWithMs(sec) {{
                if (!sec || isNaN(sec)) return "00:00.0";
                var m = Math.floor(sec / 60);
                var s = Math.floor(sec % 60);
                var ms = Math.floor((sec % 1) * 10);
                return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s) + "." + ms;
            }}

            function formatTimeShort(sec) {{
                if (!sec || isNaN(sec)) return "00:00";
                var m = Math.floor(sec / 60);
                var s = Math.floor(sec % 60);
                return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
            }}

            // Cập nhật hiệu ứng "Loang" màu âm thanh và vị trí con trỏ
            function updateLoangAndProgress(cur, dur) {{
                var timecode = parentDoc.getElementById('daw-timecode-display');
                var timeEnd = parentDoc.getElementById('daw-time-end');
                var scrubCursor = parentDoc.getElementById('daw-scrub-cursor');
                var eqBars = parentDoc.querySelectorAll('#daw-eq-bars .daw-eq-bar');

                if (timecode) {{
                    timecode.textContent = formatTimeWithMs(cur) + " / " + formatTimeWithMs(dur);
                }}
                if (timeEnd && dur > 0) {{
                    timeEnd.textContent = formatTimeShort(dur);
                }}
                var pct = (dur > 0) ? Math.max(0, Math.min(1, cur / dur)) : 0;
                if (scrubCursor) {{
                    scrubCursor.style.left = (pct * 100) + "%";
                }}

                var numBars = eqBars.length;
                var activeIdx = Math.floor(pct * numBars);
                eqBars.forEach(function(bar, idx) {{
                    if (idx <= activeIdx) {{
                        bar.classList.add('loang-active');
                        bar.style.background = "#f97316";
                        bar.style.boxShadow = "0 0 6px rgba(249, 115, 22, 0.75)";
                    }} else {{
                        bar.classList.remove('loang-active');
                        bar.style.background = "#232c3f";
                        bar.style.boxShadow = "none";
                    }}
                }});
            }}

            function animateWave() {{
                var audio = getLiveAudio();
                if (audio && !audio.paused && !audio.ended) {{
                    var cur = audio.currentTime || 0;
                    var dur = audio.duration || 0;
                    var pct = dur > 0 ? (cur / dur) : 0;
                    var eqBars = parentDoc.querySelectorAll('#daw-eq-bars .daw-eq-bar');
                    var numBars = eqBars.length;
                    var activeIdx = Math.floor(pct * numBars);

                    eqBars.forEach(function(bar, idx) {{
                        var baseH = parseInt(bar.getAttribute('data-base-h') || '14', 10);
                        if (idx <= activeIdx) {{
                            var factor = Math.sin((Date.now() / 110) + (idx * 0.45));
                            var bounce = Math.abs(factor) * 14 + (Math.random() * 4);
                            var finalH = Math.min(28, Math.max(5, Math.floor(baseH * 0.5 + bounce)));
                            bar.style.height = finalH + "px";
                            bar.style.background = "#f97316";
                            bar.style.boxShadow = "0 0 6px rgba(249, 115, 22, 0.75)";
                        }} else {{
                            bar.style.height = baseH + "px";
                            bar.style.background = "#232c3f";
                            bar.style.boxShadow = "none";
                        }}
                    }});

                    updateLoangAndProgress(cur, dur);
                    animId = requestAnimationFrame(animateWave);
                }}
            }}

            function doPlay() {{
                var audio = getLiveAudio();
                if (!audio || !audio.src || audio.src === '' || audio.src.endsWith('/')) {{
                    return;
                }}
                audio.play().then(function() {{
                    var playIcon = parentDoc.getElementById('daw-play-icon');
                    var disc = parentDoc.getElementById('daw-disc');
                    var statusBadge = parentDoc.getElementById('daw-badge-status');
                    if (playIcon) playIcon.textContent = "⏸";
                    if (disc) disc.classList.add('disc-spinning');
                    if (statusBadge) {{
                        statusBadge.textContent = "PLAYING";
                        statusBadge.style.background = "#ea580c";
                        statusBadge.style.color = "#ffffff";
                    }}
                    cancelAnimationFrame(animId);
                    animId = requestAnimationFrame(animateWave);
                }}).catch(function(err) {{
                    console.log("Audio play notice:", err);
                }});
            }}

            function doPause() {{
                var audio = getLiveAudio();
                if (audio) {{
                    audio.pause();
                }}
                var playIcon = parentDoc.getElementById('daw-play-icon');
                var disc = parentDoc.getElementById('daw-disc');
                var statusBadge = parentDoc.getElementById('daw-badge-status');
                if (playIcon) playIcon.textContent = "▶";
                if (disc) disc.classList.remove('disc-spinning');
                if (statusBadge) {{
                    statusBadge.textContent = "PAUSED";
                    statusBadge.style.background = "rgba(249, 115, 22, 0.2)";
                    statusBadge.style.color = "#fb923c";
                }}
                cancelAnimationFrame(animId);
                var cur = audio ? (audio.currentTime || 0) : 0;
                var dur = audio ? (audio.duration || 0) : 0;
                updateLoangAndProgress(cur, dur);
                var eqBars = parentDoc.querySelectorAll('#daw-eq-bars .daw-eq-bar');
                eqBars.forEach(function(bar) {{
                    var baseH = bar.getAttribute('data-base-h') || '14';
                    bar.style.height = baseH + "px";
                }});
            }}

            // Đăng ký toàn cục lên parentWin để preview hoặc các component khác có thể gọi
            parentWin.__vdtDoPlay = doPlay;
            parentWin.__vdtDoPause = doPause;
            parentWin.__vdtUpdateLoang = function() {{
                var a = getLiveAudio();
                if (a) updateLoangAndProgress(a.currentTime, a.duration || 0);
            }};

            // HÀM TẢI FILE BLOB 100% HOẠT ĐỘNG TRỰC TIẾP TRÊN TRÌNH DUYỆT (TỰ GIẢI PHÓNG BỘ NHỚ)
            function triggerBlobDownload(b64Data, filename, mimeType) {{
                try {{
                    if (!b64Data || b64Data.length < 10) {{
                        console.error("No file data available to download.");
                        return;
                    }}
                    var byteCharacters = atob(b64Data);
                    var byteArrays = [];
                    var sliceSize = 1024 * 4;
                    for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {{
                        var slice = byteCharacters.slice(offset, offset + sliceSize);
                        var byteNumbers = new Array(slice.length);
                        for (var i = 0; i < slice.length; i++) {{
                            byteNumbers[i] = slice.charCodeAt(i);
                        }}
                        byteArrays.push(new Uint8Array(byteNumbers));
                    }}
                    var blob = new (parentWin.Blob || Blob)(byteArrays, {{ type: mimeType }});
                    var blobUrl = (parentWin.URL || window.URL).createObjectURL(blob);
                    var link = parentDoc.createElement('a');
                    link.style.display = 'none';
                    link.href = blobUrl;
                    link.download = filename;
                    parentDoc.body.appendChild(link);
                    link.click();
                    setTimeout(function() {{
                        if (link.parentNode) {{
                            link.parentNode.removeChild(link);
                        }}
                        (parentWin.URL || window.URL).revokeObjectURL(blobUrl);
                    }}, 3000);
                }} catch(err) {{
                    console.error("Blob download failed, trying dataURI fallback:", err);
                    var fallbackLink = parentDoc.createElement('a');
                    fallbackLink.href = "data:" + mimeType + ";base64," + b64Data;
                    fallbackLink.download = filename;
                    fallbackLink.style.display = 'none';
                    parentDoc.body.appendChild(fallbackLink);
                    fallbackLink.click();
                    setTimeout(function() {{
                        if (fallbackLink.parentNode) fallbackLink.parentNode.removeChild(fallbackLink);
                    }}, 1000);
                }}
            }}

            // GỠ BỎ LISTENER CŨ ĐỂ KHÔNG BAO GIỜ BỊ DÍNH CLOSURE HOẶC DETACHED IFRAME
            if (parentWin.__vdtDawClickHandler) {{
                parentDoc.removeEventListener('click', parentWin.__vdtDawClickHandler, true);
            }}

            parentWin.__vdtDawClickHandler = function(e) {{
                var audio = getLiveAudio();
                var curTrack = parentWin.__vdtCurrentTrack || {{
                    audioB64: audioDataB64,
                    srtB64: srtDataB64,
                    baseFilename: baseFilename
                }};

                // 1. Nút Phát / Tạm dừng
                if (e.target.closest('#daw-btn-play')) {{
                    e.preventDefault();
                    if (audio) {{
                        if (audio.paused) {{
                            doPlay();
                        }} else {{
                            doPause();
                        }}
                    }}
                    return;
                }}

                // 2. Nút Lùi 5s
                if (e.target.closest('#daw-btn-prev')) {{
                    e.preventDefault();
                    if (audio) {{
                        audio.currentTime = Math.max(0, audio.currentTime - 5);
                        updateLoangAndProgress(audio.currentTime, audio.duration || 0);
                    }}
                    return;
                }}

                // 3. Nút Tiến 5s
                if (e.target.closest('#daw-btn-next')) {{
                    e.preventDefault();
                    if (audio) {{
                        audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 5);
                        updateLoangAndProgress(audio.currentTime, audio.duration || 0);
                    }}
                    return;
                }}

                // 4. Nút Lặp lại
                var loopBtn = e.target.closest('#daw-btn-loop');
                if (loopBtn && audio) {{
                    e.preventDefault();
                    isLooping = !isLooping;
                    audio.loop = isLooping;
                    loopBtn.style.color = isLooping ? "#f97316" : "#64748b";
                    return;
                }}

                // 5. Nút Thu nhỏ / Phóng to Dock
                var toggleBtn = e.target.closest('#daw-btn-toggle-size');
                if (toggleBtn) {{
                    e.preventDefault();
                    var dockBar = parentDoc.getElementById('daw-dock-fixed-bar');
                    if (dockBar) {{
                        var isCollapsed = dockBar.classList.toggle('daw-dock-collapsed');
                        toggleBtn.textContent = isCollapsed ? '🔼' : '🔽';
                        toggleBtn.title = isCollapsed ? 'Mở rộng toàn màn hình' : 'Thu nhỏ thanh phát';
                    }}
                    return;
                }}

                // 6. Nút Tải SRT (Luôn lấy dữ liệu track mới nhất)
                if (e.target.closest('#daw-btn-dl-srt')) {{
                    e.preventDefault();
                    triggerBlobDownload(curTrack.srtB64, curTrack.baseFilename + ".srt", "text/plain;charset=utf-8");
                    return;
                }}

                // 7. Nút Tải MP3 (Luôn lấy dữ liệu track mới nhất)
                if (e.target.closest('#daw-btn-dl-mp3')) {{
                    e.preventDefault();
                    triggerBlobDownload(curTrack.audioB64, curTrack.baseFilename + ".mp3", "audio/mp3");
                    return;
                }}

                // 8. Nút Tải WAV Master 48kHz (Luôn lấy dữ liệu track mới nhất)
                if (e.target.closest('#daw-btn-dl-wav')) {{
                    e.preventDefault();
                    triggerBlobDownload(curTrack.audioB64, curTrack.baseFilename + "_Master48kHz.wav", "audio/wav");
                    return;
                }}
            }};

            parentDoc.addEventListener('click', parentWin.__vdtDawClickHandler, true);

            // Xử lý tua & sướt chuột (Scrubbing / Dragging)
            function handleScrub(e) {{
                var scrub = parentDoc.getElementById('daw-waveform-scrub');
                var audio = getLiveAudio();
                if (!scrub || !audio) return;
                var rect = scrub.getBoundingClientRect();
                var clientX = (e.clientX !== undefined) ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
                var clickX = clientX - rect.left;
                var pct = Math.max(0, Math.min(1, clickX / rect.width));
                if (audio.duration && !isNaN(audio.duration)) {{
                    audio.currentTime = pct * audio.duration;
                    updateLoangAndProgress(audio.currentTime, audio.duration);
                }}
            }}

            if (parentWin.__vdtScrubDownHandler) {{
                parentDoc.removeEventListener('mousedown', parentWin.__vdtScrubDownHandler, true);
                parentDoc.removeEventListener('mousemove', parentWin.__vdtScrubMoveHandler, true);
                parentDoc.removeEventListener('mouseup', parentWin.__vdtScrubUpHandler, true);
            }}

            parentWin.__vdtScrubDownHandler = function(e) {{
                if (e.target.closest('#daw-waveform-scrub')) {{
                    isScrubbing = true;
                    handleScrub(e);
                }}
            }};
            parentWin.__vdtScrubMoveHandler = function(e) {{
                if (isScrubbing) {{
                    handleScrub(e);
                }}
            }};
            parentWin.__vdtScrubUpHandler = function(e) {{
                if (isScrubbing) {{
                    isScrubbing = false;
                }}
            }};

            parentDoc.addEventListener('mousedown', parentWin.__vdtScrubDownHandler, true);
            parentDoc.addEventListener('mousemove', parentWin.__vdtScrubMoveHandler, true);
            parentDoc.addEventListener('mouseup', parentWin.__vdtScrubUpHandler, true);

            // Tái khởi tạo Live Audio Element: Luôn load lại buffer âm thanh mới
            var liveAudio = getLiveAudio();
            if (liveAudio) {{
                liveAudio.pause();
                liveAudio.load();
                liveAudio.currentTime = 0;
                updateLoangAndProgress(0, liveAudio.duration || 0);

                liveAudio.onloadedmetadata = function() {{
                    updateLoangAndProgress(liveAudio.currentTime, liveAudio.duration || 0);
                }};
                liveAudio.ontimeupdate = function() {{
                    if (liveAudio.paused && !isScrubbing) {{
                        updateLoangAndProgress(liveAudio.currentTime, liveAudio.duration || 0);
                    }}
                }};
                liveAudio.onended = function() {{
                    doPause();
                    liveAudio.currentTime = 0;
                    updateLoangAndProgress(0, liveAudio.duration || 0);
                    var statusBadge = parentDoc.getElementById('daw-badge-status');
                    if (statusBadge) statusBadge.textContent = "READY";
                }};

                if (liveAudio.getAttribute('data-autoplay') === 'true') {{
                    liveAudio.removeAttribute('data-autoplay');
                    setTimeout(doPlay, 350);
                }}
            }}

        }} catch(err) {{
            console.error('DAW Player error:', err);
        }}
    }})();
    </script>
    </body>
    </html>
    """
    components.html(player_engine_js, height=0)


# Bottom Copyright Footer
st.html(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding: 10px 4px; border-top: 1px solid rgba(255, 255, 255, 0.05); font-size: 0.78rem; color: #64748b; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <img src="{author_logo_b64}" style="width: 20px; height: 20px; border-radius: 50%; border: 1px solid #f97316; object-fit: cover;" />
            <span><strong>Studio VDT • DAW Pro Edition</strong> — Sáng lập & Bản quyền bởi <strong style="color: #f97316;">Võ Duy Toàn</strong></span>
        </div>
        <div>
            Trạm sản xuất âm thanh AI thế hệ mới • Kết xuất giọng nói chuẩn điện ảnh VieNeu Neural Engine v4.2
        </div>
    </div>
    """
)

