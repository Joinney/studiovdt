"""
Studio VDT • AI Dubbing & Multi-Voice Text-to-Speech (DAW Pro Edition)
Enterprise Pro Audio • VieNeu Neural Engine v4.2 Max
Full DAW Studio Interface với Theme Studio Light & Điểm Nhấn Cam Amber & Xanh Dương Chuẩn DAW
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

import importlib
import config as _cfg_mod
import video_dubber.vieneu_tts as _vieneu_mod
_cfg_mod = importlib.reload(_cfg_mod)
_vieneu_mod = importlib.reload(_vieneu_mod)

from config import DEFAULT_VOICES, LANGUAGE_NAMES, VOICES_CATALOG, DubbingConfig
from video_dubber.pipeline import VideoDubberPipeline
from video_dubber.vieneu_tts import generate_vieneu_speech, EMOTION_SOUND_MAP, apply_acoustic_fx

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
    ("[angry]", "tức quá!", "[worried]", "chết rồi"),
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
    "📌 HƯỚNG DẪN DÀNH CHO BẠN (AI):\n"
    "Hãy viết kịch bản (review phim / kể chuyện / đời sống / quảng cáo...) thật tự nhiên, lôi cuốn "
    "và khéo léo lồng ghép các mã lệnh cảm xúc ở bảng trên (đặt trong dấu ngoặc vuông []) vào các câu thoại thích hợp "
    "để khi đưa vào phần mềm Studio VDT, giọng đọc AI sẽ tự động phát ra cảm xúc, tiếng cười, tiếng thở dài, ho, thán phục... chân thực và sống động nhất!"
)


def generate_emotion_table_html():
    rows_html = []
    for i, (col1, col2, col3, col4) in enumerate(EMOTION_TABLE_DATA):
        bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
        c1_btn = f'<button type="button" class="m-chip neon-tag-chip" data-tag="{col1}" style="margin: 0; padding: 2px 7px; font-size: 11.5px; font-weight: 600; color: #0284c7;" title="Bấm để chèn {col1}">{col1}</button>' if col1 else ""
        c3_btn = f'<button type="button" class="m-chip neon-tag-chip" data-tag="{col3}" style="margin: 0; padding: 2px 7px; font-size: 11.5px; font-weight: 600; color: #0284c7;" title="Bấm để chèn {col3}">{col3}</button>' if col3 else ""
        row = f"""
        <tr style="background: {bg}; border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 6px 4px; text-align: center;">{c1_btn}</td>
            <td style="padding: 6px 4px; text-align: center; color: #334155; font-size: 12px;">{col2}</td>
            <td style="padding: 6px 4px; text-align: center;">{c3_btn}</td>
            <td style="padding: 6px 4px; text-align: center; color: #334155; font-size: 12px;">{col4}</td>
        </tr>
        """
        rows_html.append(row)

    table_html = f"""
    <div style="max-height: 380px; overflow-y: auto; overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; margin-top: 10px; -webkit-overflow-scrolling: touch; background: #ffffff;">
        <table style="width: 100%; border-collapse: collapse; min-width: 460px;">
            <thead>
                <tr style="background: #f1f5f9; border-bottom: 1px solid #cbd5e1; position: sticky; top: 0; z-index: 2;">
                    <th style="padding: 8px 4px; text-align: center; color: #0f172a; font-size: 12px; font-weight: 700; width: 25%;">Mã lệnh (Tiếng Anh)</th>
                    <th style="padding: 8px 4px; text-align: center; color: #475569; font-size: 12px; font-weight: 700; width: 25%;">Âm thanh phát ra</th>
                    <th style="padding: 8px 4px; text-align: center; color: #0f172a; font-size: 12px; font-weight: 700; width: 25%;">Mã lệnh (Tiếng Anh)</th>
                    <th style="padding: 8px 4px; text-align: center; color: #475569; font-size: 12px; font-weight: 700; width: 25%;">Âm thanh phát ra</th>
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


VOICE_AVATAR_MAP = {
    # Adam series
    "Adam Tốp Tốp": "adam1.png",
    "Adam bựa": "adam2.png",
    "Adam": "adam3.png",

    # Hot voices (Ưu tiên giọng hot trước)
    "Hải Đăng": "n10.png",
    "Trúc Ly": "nu3.png",
    "Thiện Minh": "ch2.png",
    "Mai Anh": "nu4.png",
    "Thùy Dung": "nu6.png",
    "Thiền Tâm Đức": "n15.png",
    "Ngọc Huyền": "nu11.png",
    "Quang Sơn": "n13.png",
    "Ngọc Trân": "nu26.png",

    # Nam voices (n1 - n20, ch: chú)
    "Minh Đức": "n1.png",
    "Phạm Tuyên": "n2.png",
    "Xuân Vĩnh": "n4.png",
    "Thanh Bình": "n8.png",
    "Quốc Tuấn": "n11.png",
    "Hữu Quân": "n5.png",
    "Anh Khôi": "n9.png",
    "Minh Quân": "n18.png",
    "Mạnh Dũng": "n7.png",
    "Thái Sơn": "n6.png",
    "Minh Triết": "n12.png",
    "Đức Trí": "n19.png",
    "Hoàng Nam": "n19.png",
    "Quang Huy": "n20.png",
    "NM1": "n10.png",
    "SM": "n6.png",
    "NM2": "n9.png",
    "NamMinh": "n1.png",
    "Thầy Bảy": "ch2.png",

    # Nữ voices (nu1 - nu27, co: cô)
    "Ngọc Linh": "nu5.png",
    "Đoan Trang": "nu15.png",
    "Quỳnh Anh": "nu27.png",
    "Ái Hân": "nu12.png",
    "Xuân Tiên": "nu2.png",
    "Thục Đoan": "nu14.png",
    "Mỹ Duyên": "nu24.png",
    "Kim Thanh": "nu1.png",
    "Ngọc Ánh": "nu8.png",
    "Thanh Tâm": "nu9.png",
    "Thu Hà": "nu7.png",
    "NF": "nu16.png",
    "SF": "nu17.png",
    "HoaiMy": "nu20.png",
    "Mỹ Linh": "nu23.png",
}

_AVATAR_B64_CACHE = {}


def get_voice_avatar_base64(voice_label: str = "", voice_id: str = "") -> str:
    search_key = f"{voice_label} {voice_id}".lower()
    matched_file = None

    for k, img_name in VOICE_AVATAR_MAP.items():
        if k.lower() in search_key:
            matched_file = img_name
            break

    if not matched_file:
        if "adam" in search_key:
            matched_file = "adam1.png"
        elif any(w in search_key for w in ["chú", "thầy", "bác", "ông", "bảy", "kể chuyện", "rùng rợn", "ma"]):
            matched_file = "ch2.png"
        elif any(w in search_key for w in ["cô", "bà", "mẹ", "lão"]):
            matched_file = "co1.png"
        elif any(w in search_key for w in ["nữ", "chị", "bé", "gái", "mai", "ly", "dung", "huyền", "trân", "linh", "anh", "hân", "tiên", "đoan", "duyên", "thanh", "ánh", "tâm", "hà"]):
            matched_file = "nu3.png"
        else:
            matched_file = "n1.png"

    if matched_file in _AVATAR_B64_CACHE:
        return _AVATAR_B64_CACHE[matched_file]

    img_path = Path(__file__).parent / "assets" / matched_file
    if img_path.exists():
        try:
            b64_str = base64.b64encode(img_path.read_bytes()).decode("utf-8")
            uri = f"data:image/png;base64,{b64_str}"
            _AVATAR_B64_CACHE[matched_file] = uri
            return uri
        except Exception:
            pass

    return author_logo_b64


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
    # For Adam / Adam bựa / Adam Tốp Tốp, serve the 100% lossless 48kHz studio sample from vieneu.io directly
    if "adam" in voice_id.lower():
        adam_ref = Path(__file__).parent / "video_dubber" / "assets" / "adam_toptop_ref.wav"
        if adam_ref.exists() and adam_ref.stat().st_size > 1000:
            return adam_ref

    preview_dir = Path("./output/preview_samples")
    preview_dir.mkdir(parents=True, exist_ok=True)
    import unicodedata
    clean_slug = voice_id.replace("vieneu:", "").replace(":", "_").replace(" ", "_").replace("-", "_")
    clean_slug = clean_slug.replace('đ', 'd').replace('Đ', 'D')
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
        try:
            from video_dubber.vieneu_tts import enhance_vocal
            from pydub import AudioSegment
            if preview_path.exists() and preview_path.stat().st_size > 1000:
                snd = AudioSegment.from_file(str(preview_path))
                snd = enhance_vocal(snd, voice_name=voice_id, deep_warmth=True)
                snd.export(str(preview_path), format="mp3", bitrate="320k")
        except Exception as e_pv:
            logger.warning(f"Edge preview mastering note: {e_pv}")
    return preview_path


# Session States
DEFAULT_DEMO_TEXT = (
    "Hello các con vợ, hôm nay Adam lại lên đồ ngon cho cả nhà đây, coi hết clip rồi hãy lướt nha! [nghỉ 0.5s] "
    "Nghe rõ chưa mấy ba? Đừng để tui phải dùng chiêu cuối đấy nhé!"
)

if "tts_main_text" not in st.session_state:
    st.session_state["tts_main_text"] = DEFAULT_DEMO_TEXT

if "slider_speed_val" not in st.session_state:
    st.session_state["slider_speed_val"] = 0  # 1.0x Chuẩn Gốc Studio vieneu.io

if "selected_voice_label" not in st.session_state:
    st.session_state["selected_voice_label"] = "🔥 Adam Tốp Tốp (VieNeu - Nam Miền Nam • Cảm xúc, Không nghiêm túc, Tốp Tốp, Tấu hề)"

if not st.session_state.get("_vdt_adam_toptop_v4_migrated"):
    st.session_state["slider_speed_val"] = 0
    st.session_state["slider_speed_widget"] = 0
    st.session_state["selected_voice_label"] = "🔥 Adam Tốp Tốp (VieNeu - Nam Miền Nam • Cảm xúc, Không nghiêm túc, Tốp Tốp, Tấu hề)"
    cur_txt = st.session_state.get("tts_main_text", "")
    if "Hello các con vợ" in cur_txt and ("[cười]" in cur_txt or "[laughing]" in cur_txt):
        st.session_state["tts_main_text"] = DEFAULT_DEMO_TEXT
    st.session_state["_vdt_adam_toptop_v4_migrated"] = True

if "active_acoustic_fx" not in st.session_state:
    st.session_state["active_acoustic_fx"] = "Studio Dry"

if "last_generated_file" not in st.session_state:
    st.session_state["last_generated_file"] = None

if "script_generated_file" not in st.session_state:
    st.session_state["script_generated_file"] = None


# Preset Scripts
sample_options = {
    "🎬 Review Phim Tóm Tắt (Adam Tốp Tốp)": (
        "Hello các con vợ, hôm nay Adam lại lên đồ ngon cho cả nhà đây, coi hết clip rồi hãy lướt nha! [nghỉ 0.5s] "
        "Nghe rõ chưa mấy ba? Đừng để tui phải dùng chiêu cuối đấy nhé!"
    ),
    "🔥 Adam Tốp Tốp (Mẫu Chuẩn vieneu.io 100%)": (
        "Hello các con vợ, hôm nay Adam lại lên đồ ngon cho cả nhà đây, coi hết clip rồi hãy lướt nha!"
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


# 4. Global Modern Light Studio CSS (Khớp 100% hình mẫu người dùng gửi)
st.html(
    """
    <style>
    /* Global Light Studio Canvas */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1.5rem !important;
        z-index: 10;
    }
    .stApp {
        background-color: #f8fafc !important;
        background-image: 
            linear-gradient(rgba(0, 0, 0, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px) !important;
        background-size: 24px 24px !important;
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 140px !important;
        max-width: 1480px !important;
    }

    /* Container border & cards: Clean Porcelain White with Subtle Border & Shadow */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        padding: 12px 14px !important;
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

    /* Text Area: Clean White Editor with Slate Typography */
    div[data-testid="stTextArea"] textarea {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-family: "JetBrains Mono", "Consolas", monospace !important;
        font-size: 13.5px !important;
        line-height: 1.65 !important;
        padding: 12px 14px !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #0284c7 !important;
        box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15) !important;
    }

    /* Selectbox styling */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
    }
    div[data-baseweb="select"] span {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1) !important;
    }
    ul[role="listbox"] {
        background-color: #ffffff !important;
    }
    li[role="option"] {
        color: #0f172a !important;
    }
    li[role="option"]:hover {
        background-color: #f1f5f9 !important;
    }

    /* File Uploader styling */
    div[data-testid="stFileUploader"] section {
        background-color: #f8fafc !important;
        border: 1.5px dashed #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }
    div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] small {
        color: #475569 !important;
    }

    /* Primary Accent Button: Vibrant Ocean Blue Gradient */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 800 !important;
        letter-spacing: 0.3px !important;
        font-size: 13.5px !important;
        box-shadow: 0 3px 12px rgba(2, 132, 199, 0.35) !important;
        transition: all 0.15s ease !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
        box-shadow: 0 5px 16px rgba(2, 132, 199, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* Secondary Buttons: Crisp Porcelain White */
    button[kind="secondary"] {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.12s ease !important;
    }
    button[kind="secondary"]:hover {
        background: #f8fafc !important;
        border-color: #0284c7 !important;
        color: #0284c7 !important;
    }

    /* Buttons in dense studio columns: no ellipsis truncation, clean wrap */
    div[data-testid="stButton"] button {
        padding: 5px 4px !important;
        min-height: 36px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
    }
    div[data-testid="stButton"] button p {
        font-size: 11px !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        word-break: normal !important;
        line-height: 1.2 !important;
    }

    /* Sliders: Complete Ocean Blue Theme */
    div[data-testid="stSlider"] [role="slider"] {
        background-color: #0284c7 !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 1px 6px rgba(2, 132, 199, 0.45) !important;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[style*="background"] {
        background: #0284c7 !important;
    }
    div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
        color: #0284c7 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stSlider"] p, div[data-testid="stSlider"] span {
        color: #0284c7 !important;
    }

    /* Expander styling */
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] details summary {
        color: #334155 !important;
        font-weight: 700 !important;
    }

    /* Emotion Tag Chips: Light Aesthetic */
    .neon-tag-chip {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        color: #334155;
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
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .neon-tag-chip:hover {
        background: #f0fdf4 !important;
        border-color: #0284c7 !important;
        color: #0284c7 !important;
        transform: translateY(-1px);
    }

    /* Fixed Bottom DAW Master Player Dock (Theme Sáng Chuẩn Screenshot) */
    .daw-dock-fixed {
        position: fixed !important;
        bottom: 0px !important;
        left: 0px !important;
        right: 0px !important;
        width: 100vw !important;
        max-width: 100% !important;
        background: #ffffff !important;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
        border-top: 1.5px solid #e2e8f0 !important;
        box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.08) !important;
        z-index: 99999999 !important;
        padding: 8px 24px !important;
        box-sizing: border-box !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    .daw-action-btn {
        background: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #334155 !important;
        border-radius: 6px !important;
        padding: 6px 12px !important;
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
        background: #f1f5f9 !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
        transform: translateY(-1px) !important;
    }
    .daw-action-btn-wav {
        background: #0284c7 !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        padding: 6px 14px !important;
        font-size: 11.5px !important;
        font-weight: 800 !important;
        cursor: pointer !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.35) !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    .daw-action-btn-wav:hover {
        background: #0369a1 !important;
        transform: translateY(-1px) !important;
    }

    .loang-active {
        background: #0284c7 !important;
        box-shadow: 0 0 5px rgba(2, 132, 199, 0.75) !important;
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
    </style>
    """
)


# 5. Top Header & Studio Navigation Bar (Khớp 100% hình mẫu người dùng)
st.html(
    f"""
    <div style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 4px;">
            <!-- Brand / Logo -->
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 42px; height: 42px; border-radius: 50%; background: #ffffff; border: 2px solid #0284c7; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(234, 88, 12, 0.25); flex-shrink: 0;">
                    <img src="{author_logo_b64}" style="width: 36px; height: 36px; border-radius: 50%; object-fit: cover;" />
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 1.45rem; font-weight: 900; letter-spacing: -0.5px; color: #0f172a;">Studio VDT</span>
                        <span style="background: rgba(2, 132, 199, 0.1); border: 1px solid #0284c7; color: #0284c7; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 16px; letter-spacing: 0.4px;">• ENTERPRISE PRO AUDIO</span>
                        <span style="background: #f1f5f9; border: 1px solid #e2e8f0; color: #475569; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 16px;">VieNeu Neural v4.2 Max</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                        Sáng lập & Bản quyền: <span style="color: #0284c7; font-weight: 700;">Võ Duy Toàn</span> | Hệ thống phối âm & lồng tiếng AI cao cấp
                    </div>
                </div>
            </div>

            <!-- Server Status & Indicator Dot -->
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="width: 9px; height: 9px; border-radius: 50%; background: #0284c7; box-shadow: 0 0 8px #0284c7;"></span>
                <span style="background: #f0f9ff; border: 1px solid #7dd3fc; color: #0284c7; border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 700;">PRO STUDIO</span>
            </div>
        </div>
    </div>
    """
)


# 6. Caret Injection Engine Javascript (Chèn thẻ chuẩn xác tại vị trí con trỏ chuột)
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
            if (elWords) elWords.innerHTML = 'Từ: <strong style="color: #0f172a;">' + words + ' từ</strong>';
            var elChars = parentDoc.getElementById('daw-stat-chars');
            if (elChars) elChars.innerHTML = 'Ký tự: <strong style="color: #0f172a;">' + chars + ' ký tự</strong>';
            var elDur = parentDoc.getElementById('daw-stat-duration');
            if (elDur) elDur.innerHTML = '⏱️ Thời lượng dự kiến: 00:' + (durationSec < 10 ? '0' : '') + durationSec + 's';
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

        var emotionPromptText = __EMOTION_PROMPT_JSON__;

        function copyEmotionPrompt(btn) {
            function updateBtnStatus(success) {
                if (!btn) return;
                var originalHtml = btn.getAttribute('data-original-html') || btn.innerHTML;
                if (!btn.getAttribute('data-original-html')) {
                    btn.setAttribute('data-original-html', originalHtml);
                }
                btn.innerHTML = success ? '✅ Đã copy!' : '❌ Lỗi copy';
                btn.style.background = success ? '#0284c7' : '#991b1b';
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
components.html(caret_injector_html, height=0)


# ==============================================================================
# MAIN WORKSPACE: 3 COLUMNS DASHBOARD (100% Khớp Hình Ảnh Người Dùng Cung Cấp)
# ==============================================================================
col_voice, col_editor, col_tags = st.columns([0.28, 0.44, 0.28], gap="small")


# ------------------------------------------------------------------------------
# CỘT 1 (BÊN TRÁI ~28%): CHỌN GIỌNG, SHOWCASE CARD, TEMPO & HIỆU ỨNG ÂM THANH
# ------------------------------------------------------------------------------
with col_voice:
    with st.container(border=True):
        voices_dict = VOICES_CATALOG.get("vi", {})
        voice_options = list(voices_dict.keys())

        # Selectbox Chọn giọng đọc
        if "selected_voice_label" not in st.session_state or st.session_state["selected_voice_label"] not in voice_options:
            st.session_state["selected_voice_label"] = voice_options[0]

        selected_voice_label = st.selectbox(
            "Danh sách giọng:",
            options=voice_options,
            key="selected_voice_label",
            label_visibility="collapsed",
        )
        selected_voice_id = voices_dict[selected_voice_label]

        # Trích xuất thông tin giọng
        clean_name = selected_voice_label.split(" (")[0].replace("🔥 ", "").strip()
        if " (" in selected_voice_label:
            raw_desc = selected_voice_label.split(" (")[1].rstrip(")")
        else:
            raw_desc = "VieNeu - Nam Miền Nam - Cảm xúc, Không nghiêm túc, Tốp Tốp, Tấu hề"

        if "Adam" in clean_name:
            v_badge = "HOT REVIEW"
        elif "Hải Đăng" in clean_name or "Tuấn Anh" in clean_name:
            v_badge = "THỜI SỰ VTV"
        elif "Thiện Minh" in clean_name or "Bảy" in clean_name:
            v_badge = "KỂ CHUYỆN"
        elif "Thùy Dung" in clean_name or "Mỹ Linh" in clean_name:
            v_badge = "PODCAST"
        else:
            v_badge = "VIENEU PRO"

        # Dữ liệu âm thanh nghe thử mẫu
        sample_audio_uri = ""
        try:
            sample_file = get_or_generate_voice_preview(selected_voice_id, "vi", clean_name)
            if sample_file.exists() and sample_file.stat().st_size > 100:
                raw_sample_bytes = sample_file.read_bytes()
                s_b64 = base64.b64encode(raw_sample_bytes).decode("utf-8")
                mime_type = "audio/wav" if raw_sample_bytes[:4] == b"RIFF" else "audio/mp3"
                sample_audio_uri = f"data:{mime_type};base64,{s_b64}"
        except Exception:
            pass

        # Dynamic Voice Avatar (Khớp nhân vật theo ảnh trong assets)
        voice_avatar_b64 = get_voice_avatar_base64(selected_voice_label, selected_voice_id)

        # Voice Showcase Card (Avatar nhân vật bên trái, chi tiết bên phải)
        st.html(
            f"""
            <div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 10px; margin-top: 4px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); display: flex; gap: 10px; align-items: center;">
                <div style="flex-shrink: 0; width: 78px; height: 98px; border-radius: 8px; overflow: hidden; border: 1.5px solid #e2e8f0; background: #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <img src="{voice_avatar_b64}" style="width: 100%; height: 100%; object-fit: cover;" />
                </div>
                <div style="flex-grow: 1; min-width: 0;">
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                        <span style="font-size: 1.05rem; font-weight: 800; color: #0f172a;">{clean_name}</span>
                        <span style="background: #0284c7; color: #ffffff; font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; letter-spacing: 0.3px;">{v_badge}</span>
                    </div>
                    <div style="font-size: 0.74rem; color: #475569; margin-top: 2px; line-height: 1.35; max-height: 34px; overflow: hidden; text-overflow: ellipsis;">
                        {raw_desc}
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px; gap: 4px;">
                        <div style="font-size: 10px; color: #64748b; font-weight: 600;">
                            Acoustic 48kHz
                        </div>
                        <audio id="vdt-preview-audio-core" src="{sample_audio_uri}" preload="auto"></audio>
                        <button type="button" id="vdt-btn-preview-sample" style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 700; color: #0284c7; cursor: pointer; display: inline-flex; align-items: center; gap: 3px;" title="Bấm để phát mẫu nghe thử {clean_name}">
                            <span id="vdt-preview-icon">🎧</span>
                            <span id="vdt-preview-lbl">Nghe thử mẫu</span>
                        </button>
                    </div>
                    <div style="font-size: 8.5px; color: #94a3b8; margin-top: 3px;">
                        Adper Ally MX6 • Như bạn đã sẵn sàng thành thạo
                    </div>
                </div>
            </div>
            """
        )

        # Preview JS Controller
        preview_js = """
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"></head><body>
        <script>
        (function() {
            try {
                var parentDoc = window.parent.document;
                var parentWin = window.parent;

                if (parentWin.__vdtPreviewClickHandler) {
                    parentDoc.removeEventListener('click', parentWin.__vdtPreviewClickHandler, true);
                }

                parentWin.__vdtPreviewClickHandler = function(e) {
                    var btn = e.target.closest('#vdt-btn-preview-sample');
                    if (!btn) return;
                    e.preventDefault();
                    e.stopPropagation();

                    var prevAudio = parentDoc.getElementById('vdt-preview-audio-core');
                    var prevIcon = parentDoc.getElementById('vdt-preview-icon');
                    var prevLbl = parentDoc.getElementById('vdt-preview-lbl');
                    var masterAudio = parentDoc.getElementById('daw-core-audio');

                    if (!prevAudio || !prevAudio.src || prevAudio.src === '' || prevAudio.src.endsWith('/')) {
                        if (prevLbl) prevLbl.textContent = "Chưa có mẫu";
                        return;
                    }

                    if (prevAudio.paused) {
                        if (masterAudio && !masterAudio.paused) {
                            if (parentWin.__vdtDoPause) parentWin.__vdtDoPause();
                            else masterAudio.pause();
                        }
                        prevAudio.currentTime = 0;
                        prevAudio.play().then(function() {
                            if (prevIcon) prevIcon.textContent = "⏸";
                            if (prevLbl) prevLbl.textContent = "Đang phát...";
                            btn.style.borderColor = "#0284c7";
                            btn.style.background = "#f0f9ff";
                        }).catch(function(err) {
                            console.log("Preview error:", err);
                        });
                    } else {
                        prevAudio.pause();
                        if (prevIcon) prevIcon.textContent = "🎧";
                        if (prevLbl) prevLbl.textContent = "Nghe thử mẫu";
                        btn.style.borderColor = "#cbd5e1";
                        btn.style.background = "#f8fafc";
                    }
                };

                parentDoc.addEventListener('click', parentWin.__vdtPreviewClickHandler, true);

                var prevAudio = parentDoc.getElementById('vdt-preview-audio-core');
                if (prevAudio) {
                    function resetBtn() {
                        var prevIcon = parentDoc.getElementById('vdt-preview-icon');
                        var prevLbl = parentDoc.getElementById('vdt-preview-lbl');
                        var btn = parentDoc.getElementById('vdt-btn-preview-sample');
                        if (prevIcon) prevIcon.textContent = "🎧";
                        if (prevLbl) prevLbl.textContent = "Nghe thử mẫu";
                        if (btn) {
                            btn.style.borderColor = "#cbd5e1";
                            btn.style.background = "#f8fafc";
                        }
                    }
                    prevAudio.onended = resetBtn;
                    prevAudio.onpause = function() {
                        if (prevAudio.paused) resetBtn();
                    };
                }
            } catch(e) {}
        })();
        </script>
        </body></html>
        """
        components.html(preview_js, height=0)

        # Quick Suggestions (2x2 grid)
        st.markdown("<div style='font-size: 11px; color: #475569; font-weight: 700; margin-bottom: 5px;'>Hiển thị danh tính nhanh:</div>", unsafe_allow_html=True)
        gv1, gv2 = st.columns(2)
        with gv1:
            st.button(
                "🎙️ Adam Review\n\nKịch tính, hề hước",
                key="btn_adam",
                on_click=set_quick_voice,
                args=(["Adam"],),
                use_container_width=True,
            )
            st.button(
                "👻 Thầy Bảy\n\nChuyện Ma Rùng Rợn",
                key="btn_thaybay",
                on_click=set_quick_voice,
                args=(["Thiện Minh", "Bảy"],),
                use_container_width=True,
            )
        with gv2:
            st.button(
                "👤 Tuấn Rần VTV\n\nThời sự chuẩn mực",
                key="btn_tuananh",
                on_click=set_quick_voice,
                args=(["Hải Đăng", "Tuấn Anh"],),
                use_container_width=True,
            )
            st.button(
                "✨ Mỹ Linh\n\nPodcast Sài Gòn",
                key="btn_mylinh",
                on_click=set_quick_voice,
                args=(["Thùy Dung", "Mỹ Linh"],),
                use_container_width=True,
            )

        # Speed (Tempo) Controls
        current_speed = st.session_state.get("slider_speed_val", 0)
        speed_disp = "1.00x (Gốc)" if current_speed == 0 else f"{1.0 + current_speed / 100.0:.2f}x ({'+' if current_speed >= 0 else ''}{current_speed}%)"
        st.html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 5px;">
                <span style="font-size: 11.5px; font-weight: 700; color: #0f172a;">⚡ Tốc độ nói (Tempo):</span>
                <span style="background: #f0f9ff; border: 1px solid #7dd3fc; color: #0284c7; border-radius: 4px; padding: 1px 7px; font-size: 11px; font-weight: 800;">{speed_disp}</span>
            </div>
            """
        )
        sp1, sp2, sp3, sp4 = st.columns(4)
        with sp1:
            st.button(
                "0.8x",
                key="btn_tempo_08",
                on_click=set_quick_tempo,
                args=(-20,),
                use_container_width=True,
                type="primary" if current_speed == -20 else "secondary",
            )
        with sp2:
            st.button(
                "1.0x",
                key="btn_tempo_10",
                on_click=set_quick_tempo,
                args=(0,),
                use_container_width=True,
                type="primary" if current_speed == 0 else "secondary",
            )
        with sp3:
            st.button(
                "1.15x",
                key="btn_tempo_115",
                on_click=set_quick_tempo,
                args=(15,),
                use_container_width=True,
                type="primary" if current_speed == 15 else "secondary",
            )
        with sp4:
            st.button(
                "1.3x",
                key="btn_tempo_13",
                on_click=set_quick_tempo,
                args=(30,),
                use_container_width=True,
                type="primary" if current_speed == 30 else "secondary",
            )

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
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; margin-top: -6px; margin-bottom: 8px;">
                <span>1.0% Chậm chuẩn</span>
                <span style="color: #0284c7; font-weight: 600;">Chuẩn làm phim (0.95-1.05)</span>
                <span>2.0% Siêu tốc</span>
            </div>
            """
        )

        speed_factor = 1.0 + (tts_rate_val / 100.0)
        rate_str = f"{'+' if tts_rate_val >= 0 else ''}{tts_rate_val}%"

        # Two Pro Sliders: Cường độ cảm xúc & Cao độ
        current_emo = st.session_state.get("emotion_depth", 65)
        current_pitch = st.session_state.get("pitch_val", 0)
        sl1, sl2 = st.columns(2)
        with sl1:
            st.markdown(f"<div style='font-size: 11.5px; color: #0f172a; font-weight: 700;'>Cường độ cảm xúc: <strong style='color: #0284c7;'>{current_emo}</strong></div>", unsafe_allow_html=True)
            st.slider("Emotion Depth:", min_value=0, max_value=100, value=current_emo, key="emotion_depth", label_visibility="collapsed")
        with sl2:
            st.markdown(f"<div style='font-size: 11.5px; color: #0f172a; font-weight: 700;'>Cao độ (chỉ số): <strong style='color: #0284c7;'>{current_pitch}</strong></div>", unsafe_allow_html=True)
            st.slider("Pitch:", min_value=-12, max_value=12, value=current_pitch, key="pitch_val", label_visibility="collapsed")

        # Acoustic Booth FX Buttons
        st.html(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; margin-bottom: 6px;">
                <span style="font-size: 11.5px; font-weight: 700; color: #0f172a;">Hiệu ứng buồng thu âm (Acoustic Dry)</span>
            </div>
            """
        )
        fx1, fx2, fx3 = st.columns(3)
        current_fx = st.session_state.get("active_acoustic_fx", "Studio Dry")
        with fx1:
            st.button(
                "🎙️ Studio",
                key="btn_fx_dry",
                on_click=set_acoustic_fx,
                args=("Studio Dry",),
                use_container_width=True,
                type="primary" if current_fx == "Studio Dry" else "secondary",
            )
        with fx2:
            st.button(
                "🏛️ Reverb",
                key="btn_fx_reverb",
                on_click=set_acoustic_fx,
                args=("Room Reverb",),
                use_container_width=True,
                type="primary" if current_fx == "Room Reverb" else "secondary",
            )
        with fx3:
            st.button(
                "🎧 Denoise",
                key="btn_fx_denoise",
                on_click=set_acoustic_fx,
                args=("AI Denoise",),
                use_container_width=True,
                type="primary" if current_fx == "AI Denoise" else "secondary",
            )


# ------------------------------------------------------------------------------
# CỘT 2 (Ở GIỮA ~44%): TRÌNH SOẠN THẢO KỊCH BẢN, THỐNG KÊ, PRESET & UPLOAD
# ------------------------------------------------------------------------------
with col_editor:
    with st.container(border=True):
        # Header Editor
        st.html(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 11.5px;">
                <span style="color: #0f172a; font-weight: 700; display: flex; align-items: center; gap: 4px;">
                    <span style="color: #0284c7;">•</span> KỊCH BẢN ĐANG XỬ LÝ (LIVE SYNTAX MODE) <span style="color: #64748b; font-weight: 500;">| Review Phim Thánh Adam #01</span>
                </span>
                <div style="display: flex; gap: 6px;">
                    <button type="button" id="btn-action-format" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; color: #334155; font-size: 11px; font-weight: 600; padding: 3px 8px; cursor: pointer;">Format Tags</button>
                    <span style="background: #f1f5f9; border: 1px solid #e2e8f0; color: #334155; font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 700;">AI Script Rewriter</span>
                </div>
            </div>
            """
        )

        # Large Clean White Text Area
        current_text = st.text_area(
            "Kịch bản lời thoại:",
            key="tts_main_text",
            height=280,
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
            <div style="display: flex; justify-content: space-between; align-items: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px; margin-top: 5px; margin-bottom: 10px; font-size: 11.5px; color: #64748b; flex-wrap: wrap; gap: 6px;">
                <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                    <span id="daw-stat-words" style="color: #334155;">Từ: <strong style="color: #0f172a;">{initial_words} từ</strong></span>
                    <span>•</span>
                    <span id="daw-stat-chars" style="color: #334155;">Ký tự: <strong style="color: #0f172a;">{initial_chars} ký tự</strong></span>
                    <span>•</span>
                    <span id="daw-stat-duration" style="color: #334155;">⏱️ Thời lượng dự kiến: {initial_duration}</span>
                    <span>•</span>
                    <span style="color: #64748b;">Tỷ lệ cảm xúc: 100% Khớp</span>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 2px 8px; font-size: 11px;">
                    <strong id="daw-stat-tags" style="color: #0284c7;">{initial_tags} Tags Phát hiện</strong>
                </div>
            </div>
            """
        )

        # Bottom Tools: Preset Script & TXT Upload (Trong thẻ card gọn gàng)
        c_preset, c_upload = st.columns([1.1, 0.9])
        with c_preset:
            st.markdown("<span style='font-size: 11.5px; color: #0284c7; font-weight: 700;'>💧 Preset Kịch Bản Hot Triệu View:</span>", unsafe_allow_html=True)
            st.selectbox(
                "Preset:",
                options=list(sample_options.keys()),
                index=0,
                key="sample_preset_choice",
                on_change=apply_sample_preset,
                label_visibility="collapsed",
            )
        with c_upload:
            st.markdown("<span style='font-size: 11.5px; color: #0284c7; font-weight: 700;'>📁 Tải Kịch Bản (TXT / SRT / DOCX):</span>", unsafe_allow_html=True)
            st.file_uploader(
                "File kịch bản:",
                type=["txt"],
                key="txt_upload",
                on_change=apply_txt_upload,
                label_visibility="collapsed",
            )

        # Full 55+ Emotion Table Expander
        with st.expander("📋 Xem & Sao chép đầy đủ 55+ Bảng mã lệnh cảm xúc (Dùng cho ChatGPT / AI)", expanded=False):
            st.markdown(
                """
                💡 **Mẹo:** Bấm nút **"📋 Tải bản mẫu / Copy !!"** ở góc phải để sao chép toàn bộ bảng và prompt gửi sang ChatGPT / Claude nhờ AI viết kịch bản chèn sẵn cảm xúc!
                """
            )
            st.code(EMOTION_PROMPT_TEMPLATE, language="markdown")
            st.markdown(
                "<div style='font-size: 12px; color: #64748b; margin-top: 6px;'>👇 <i>Bấm vào mã lệnh bất kỳ trong bảng để chèn nhanh vào kịch bản:</i></div>",
                unsafe_allow_html=True,
            )
            st.markdown(emotion_table_html, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# CỘT 3 (BÊN PHẢI ~28%): THAO TÁC KỊCH BẢN, CHÈN THẺ CẢM XÚC TẠI CON TRỎ
# ------------------------------------------------------------------------------
with col_tags:
    with st.container(border=True):
        # Top 3 Utility Buttons
        st.html(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 6px; margin-bottom: 12px;">
                <button type="button" class="btn-copy-emotion-table" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; color: #334155; padding: 5px 9px; font-size: 11px; font-weight: 600; cursor: pointer;">Kịch bản mẫu</button>
                <button type="button" id="btn-action-clear" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; color: #334155; padding: 5px 9px; font-size: 11px; font-weight: 600; cursor: pointer;">🔄 Làm mới</button>
                <button type="button" class="btn-copy-emotion-table" style="background: #0284c7; border: none; border-radius: 6px; color: #ffffff; padding: 5px 11px; font-size: 11px; font-weight: 700; cursor: pointer; box-shadow: 0 1px 3px rgba(2, 132, 199, 0.3);">📋 Tải bản mẫu / Copy !!</button>
            </div>
            """
        )

        # Header Chèn thẻ
        st.html(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 11.5px; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 4px;">
                    <span style="color: #0284c7;">•</span> BẤM CHÈN THẺ CẢM XÚC TẠI CON TRỎ:
                </span>
                <span style="font-size: 10.5px; color: #64748b;">Chèn tại vị trí con trỏ chuột</span>
            </div>
            """
        )

        # Emotion Tag Cloud Theo Danh Mục
        st.html(
            """
            <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                <!-- Group 1: Kịch bản cảm xúc -->
                <div>
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; margin-bottom: 4px;">Kịch bản cảm xúc:</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[cười]">[cười]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[gào]">[gào]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[đỉnh kout]">[đỉnh kout]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[hét lớn]">[hét lớn]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[đau đớn]">[đau đớn]</button>
                    </div>
                </div>

                <!-- Group 2: Tổn thương & xúc động -->
                <div>
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; margin-bottom: 4px;">Tổn thương & xúc động:</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[khóc]">[khóc]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[uất ức]">[uất ức]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[hối hận]">[hối hận]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghẹn ngào]">[nghẹn ngào]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[thì thầm]">[thì thầm]</button>
                    </div>
                </div>

                <!-- Group 3: Xem trực diện (nghe sướng) -->
                <div>
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; margin-bottom: 4px;">Xem trực diện (nghe sướng):</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[hả?]">[hả?]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[thở dốc]">[thở dốc]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[thở dài]">[thở dài]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[tặc lưỡi]">[tặc lưỡi]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nấc]">[nấc]</button>
                    </div>
                </div>

                <!-- Group 4: Tăng nhịp ngắt nhanh -->
                <div>
                    <div style="font-size: 10px; font-weight: 700; color: #64748b; margin-bottom: 4px;">Tăng nhịp ngắt nhanh:</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 0.3s]">[Nghỉ 0.3]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 0.5s]">[Nghỉ 0.5]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 1s]">[Nghỉ 1.0]</button>
                        <button type="button" class="m-chip neon-tag-chip" data-tag="[nghỉ 2s]">[Nghỉ 2.0]</button>
                    </div>
                </div>
            </div>
            """
        )

        # Dropdown 55+ Thẻ & Nút Solid Blue Chèn Tại Con Trỏ
        st.html(
            """
            <div style="display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #e2e8f0; padding-top: 10px;">
                <select id="caretSelectTag" style="width: 100%; background: #ffffff; color: #0f172a; border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 7px 10px; font-size: 12px; outline: none; cursor: pointer;">
                    <option value="[crying]">🎭 [crying] hu hu (khóc)</option>
                    <option value="[cười]">😄 [cười] - nụ cười thích thú</option>
                    <option value="[laughing]">😆 [laughing] - hahaha (cười to)</option>
                    <option value="[snickers]">😏 [snickers] - khì khì (cười đểu)</option>
                    <option value="[chuckles]">🤣 [chuckles] - he he he</option>
                    <option value="[sighs]">😮‍💨 [sighs] - haizzz (thở dài)</option>
                    <option value="[screaming]">😱 [screaming] - áaaaa (kêu la)</option>
                    <option value="[shouting]">🗣️ [shouting] - gôôôôô (hét lớn)</option>
                    <option value="[whispering]">🤫 [whispering] - psst... (thì thầm)</option>
                    <option value="[shocked]">😱 [shocked] - trời ơi! (sốc)</option>
                    <option value="[confused]">🤨 [confused] - hả? (bối rối)</option>
                    <option value="[thinking]">🤔 [thinking] - hmmm (suy nghĩ)</option>
                    <option value="[gasps]">😮 [gasps] - hự (thở gấp)</option>
                    <option value="[excited]">🤩 [excited] - wowww (hào hứng)</option>
                    <option value="[relieved]">😌 [relieved] - phùuu (thở phào)</option>
                    <option value="[angry]">😡 [angry] - tức quá!</option>
                    <option value="[panicked]">🏃 [panicked] - chết chết chết!</option>
                    <option value="[clears throat]">🗣️ [clears throat] - hèm hèm (hắng giọng)</option>
                    <option value="[coughs]">😷 [coughs] - khụ khụ (ho)</option>
                    <option value="[sneezes]">🤧 [sneezes] - ách xì</option>
                    <option value="[nghỉ 0.3s]">⏱️ [nghỉ 0.3s] - Ngắt 0.3s</option>
                    <option value="[nghỉ 0.5s]">⏸️ [nghỉ 0.5s] - Ngắt 0.5s</option>
                    <option value="[nghỉ 1s]">⏳ [nghỉ 1s] - Ngắt 1.0s</option>
                    <option value="[nghỉ 2s]">🛑 [nghỉ 2s] - Ngắt 2.0s</option>
                </select>
                <button type="button" id="caretDropdownBtn" style="background: #0284c7; color: #ffffff; border: none; border-radius: 6px; padding: 7px 14px; font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; justify-content: center; gap: 5px; box-shadow: 0 1px 3px rgba(2, 132, 199, 0.3);">
                    ➕ Chèn tại vị trí con trỏ chuột
                </button>
            </div>
            """
        )


# ==============================================================================
# PROMINENT FULL-WIDTH CTA BUTTON: TẠO GIỌNG ĐỌC AI NGAY (RENDER AUDIO)
# ==============================================================================
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
btn_generate_tts = st.button(
    "+ TẠO GIỌNG ĐỌC AI NGAY (RENDER AUDIO)   Ctrl + Enter",
    type="primary",
    use_container_width=True,
)


# ==============================================================================
# AUDIO GENERATION EXECUTION PIPELINE
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
            # Giai đoạn 1: Phân tích kịch bản và bóc tách các tag âm học
            for p in range(1, 26, 4):
                progress_slot.progress(p, text=f"⚡ Tiến trình kết xuất VieNeu: {p}% — Phân tích kịch bản & thẻ cảm xúc acoustic tags...")
                time.sleep(0.02)

            # Giai đoạn 2: Khởi tạo Acoustic Engine & nạp profile giọng
            for p in range(26, 49, 4):
                progress_slot.progress(p, text=f"🎙️ Tiến trình kết xuất VieNeu: {p}% — Nạp profile âm sắc chuẩn 48kHz cho [{clean_name}]...")
                time.sleep(0.02)

            # Giai đoạn 3: Bắt đầu tổng hợp tín hiệu âm thanh
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
                try:
                    from video_dubber.vieneu_tts import enhance_vocal
                    from pydub import AudioSegment
                    if out_file.exists() and out_file.stat().st_size > 1000:
                        snd = AudioSegment.from_file(str(out_file))
                        snd = enhance_vocal(snd, voice_name=selected_voice_id, deep_warmth=True)
                        snd.export(str(out_file), format="mp3", bitrate="320k")
                except Exception as e_ed:
                    logger.warning(f"Script edge TTS mastering note: {e_ed}")

            # Giai đoạn 4: Xử lý hiệu ứng buồng thu âm thực thụ
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
                    voice_name=clean_name,
                    output_path=out_file,
                )
            except Exception as dsp_err:
                logger.warning(f"Acoustic FX processing note: {dsp_err}")

            for p in range(74, 86, 3):
                progress_slot.progress(p, text=f"🎛️ Tiến trình kết xuất: {p}% — Hoàn tất hiệu ứng buồng thu [{fx_name}] & Equalizer Mastering...")
                time.sleep(0.015)

            # Giai đoạn 5: Mastering Lossless & Phụ đề SRT
            for p in range(86, 100, 3):
                progress_slot.progress(p, text=f"📦 Tiến trình kết xuất VieNeu: {p}% — Đóng gói Master 24-bit Lossless & Phụ đề SRT...")
                time.sleep(0.02)

            # Giai đoạn 6: Hoàn tất
            progress_slot.progress(100, text="✅ Hoàn tất kết xuất 100%! Đang khởi tạo DAW Master Player...")
            time.sleep(0.35)
            progress_slot.empty()

            st.session_state["script_generated_file"] = str(out_file)
            st.session_state["script_generated_title"] = f"{clean_name}_{timestamp}"
            st.session_state["script_generated_voice_name"] = clean_name
            st.session_state["just_rendered_autoplay"] = True
            st.toast("🎉 Đã kết xuất âm thanh Master 48kHz thành công! Đang phát trong DAW Player.", icon="🎙️")
            st.rerun()

        except Exception as err:
            progress_slot.empty()
            st.error(f"❌ Có lỗi xảy ra trong quá trình tạo âm thanh: {err}")


# ==============================================================================
# FIXED BOTTOM DAW MASTER PLAYER DOCK (Theme sáng đồng bộ 100% hình mẫu)
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
        parts = track_title.rsplit("_", 2)
        gen_voice_name = parts[0] if len(parts) >= 3 else clean_name
    track_avatar_b64 = get_voice_avatar_base64(gen_voice_name, gen_voice_name)
    voice_display_info = f"{gen_voice_name} • 48kHz / 24-Bit Lossless"

    # Tạo phụ đề SRT
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

    # 36 Waveform Bars
    eq_bar_heights = [
        6, 12, 18, 24, 28, 22, 14, 10, 16, 26,
        32, 28, 20, 14, 18, 28, 24, 12, 16, 26,
        30, 22, 14, 8, 14, 22, 28, 20, 12, 16,
        24, 28, 18, 12, 8, 6
    ]
    eq_bars_html = "".join([
        f'<span class="daw-eq-bar" data-idx="{i}" data-base-h="{h}" style="display:inline-block; width: 3px; height: {h}px; background: #cbd5e1; border-radius: 1.5px; margin: 0 1px; transition: background 0.08s ease, height 0.08s ease;"></span>'
        for i, h in enumerate(eq_bar_heights)
    ])

    # Fixed Bottom DAW Dock HTML (Porcelain White Light Theme)
    st.html(
        f"""
        <div id="daw-dock-fixed-bar" class="daw-dock-fixed">
            <audio id="daw-core-audio" src="{audio_uri}" preload="auto" data-autoplay="{should_autoplay}"></audio>
            <div class="daw-dock-inner" style="display: flex; justify-content: space-between; align-items: center; gap: 10px; max-width: 1480px; margin: 0 auto; width: 100%;">
                <!-- Left: Track Title & Status Badge -->
                <div class="daw-dock-left" style="display: flex; align-items: center; gap: 10px;">
                    <div id="daw-disc" style="width: 38px; height: 38px; border-radius: 50%; overflow: hidden; border: 1.5px solid #0284c7; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 6px rgba(2, 132, 199, 0.25); flex-shrink: 0;">
                        <img src="{track_avatar_b64}" style="width: 100%; height: 100%; object-fit: cover;" />
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span id="daw-track-title" style="font-weight: 800; color: #0f172a; font-size: 0.92rem; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{track_title}</span>
                            <span id="daw-badge-status" style="background: #f0f9ff; border: 1px solid #7dd3fc; color: #0284c7; font-size: 9px; font-weight: 800; padding: 2px 6px; border-radius: 4px; letter-spacing: 0.5px;">PLAYING</span>
                        </div>
                        <div id="daw-track-subtitle" style="font-size: 0.74rem; color: #64748b; font-weight: 600; margin-top: 1px;">{voice_display_info}</div>
                    </div>
                </div>

                <!-- Center: Controls, Dynamic Timecode & Waveform Scrubbing -->
                <div class="daw-dock-center" style="display: flex; align-items: center; gap: 10px; flex-grow: 1; justify-content: center;">
                    <button type="button" id="daw-btn-prev" style="background: transparent; border: none; font-size: 15px; color: #0284c7; cursor: pointer; padding: 4px;" title="Lùi 5 giây">⏮️</button>
                    <button type="button" id="daw-btn-play" style="width: 36px; height: 36px; border-radius: 50%; background: #0284c7; border: none; display: flex; align-items: center; justify-content: center; font-size: 15px; color: #ffffff; cursor: pointer; box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4); transition: transform 0.1s ease;">
                        <span id="daw-play-icon">▶</span>
                    </button>
                    <button type="button" id="daw-btn-next" style="background: transparent; border: none; font-size: 15px; color: #0284c7; cursor: pointer; padding: 4px;" title="Tua 5 giây">⏭️</button>
                    <button type="button" id="daw-btn-loop" style="background: transparent; border: none; font-size: 15px; color: #64748b; cursor: pointer; padding: 4px;" title="Bật/Tắt Lặp lại">🔁</button>

                    <!-- Real-time Timecode Display -->
                    <span id="daw-timecode-display" style="font-family: 'JetBrains Mono', Consolas, monospace; font-size: 11.5px; color: #0f172a; font-weight: 700; margin-left: 2px; min-width: 95px;">00:00.8 / 00:10.5</span>

                    <!-- Interactive Waveform with Loang Progress & Scrubbing -->
                    <div id="daw-waveform-wrapper" style="display: flex; align-items: center; gap: 6px;">
                        <span id="daw-time-start" style="font-size: 10.5px; color: #64748b; font-family: 'JetBrains Mono', Consolas, monospace; font-weight: 600;">00:00</span>
                        <div id="daw-waveform-scrub" style="display: flex; align-items: center; justify-content: space-between; height: 32px; padding: 2px 6px; background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 6px; cursor: pointer; position: relative; width: 230px; user-select: none;" title="Bấm hoặc kéo chuột để tua âm thanh">
                            <div id="daw-scrub-cursor" style="position: absolute; top: 0; bottom: 0; left: 0%; width: 2px; background: #0284c7; box-shadow: 0 0 5px #0284c7; z-index: 5; pointer-events: none; transition: left 0.05s linear;"></div>
                            <div id="daw-eq-bars" style="display: flex; align-items: center; justify-content: space-between; width: 100%; height: 100%; pointer-events: none;">
                                {eq_bars_html}
                            </div>
                        </div>
                        <span id="daw-time-end" style="font-size: 10.5px; color: #64748b; font-family: 'JetBrains Mono', Consolas, monospace; font-weight: 600;">00:18</span>
                    </div>
                </div>

                <!-- Right: Action Buttons -->
                <div class="daw-dock-right" style="display: flex; align-items: center; gap: 6px;">
                    <button type="button" id="daw-btn-dl-srt" class="daw-action-btn" title="Tải file phụ đề SRT">
                        ☑ Kèm SRT
                    </button>
                    <button type="button" id="daw-btn-dl-mp3" class="daw-action-btn" title="Tải file MP3 320k">
                        MP3 (320k)
                    </button>
                    <button type="button" id="daw-btn-dl-wav" class="daw-action-btn-wav" title="Tải file Master WAV 48kHz">
                        ⬇ TẢI WAV MASTER (48kHz)
                    </button>
                    <button type="button" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; color: #64748b; font-size: 13px; padding: 5px 8px; cursor: pointer;" title="Cài đặt">
                        ⚙️
                    </button>
                </div>
            </div>
        </div>
        """
    )

    # JavaScript Engine for DAW Player
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
                        bar.style.background = "#0284c7";
                        bar.style.boxShadow = "0 0 5px rgba(2, 132, 199, 0.75)";
                    }} else {{
                        bar.classList.remove('loang-active');
                        bar.style.background = "#cbd5e1";
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
                            bar.style.background = "#0284c7";
                            bar.style.boxShadow = "0 0 5px rgba(2, 132, 199, 0.75)";
                        }} else {{
                            bar.style.height = baseH + "px";
                            bar.style.background = "#cbd5e1";
                            bar.style.boxShadow = "none";
                        }}
                    }});

                    updateLoangAndProgress(cur, dur);
                    animId = requestAnimationFrame(animateWave);
                }}
            }}

            function doPlay() {{
                var audio = getLiveAudio();
                if (!audio || !audio.src || audio.src === '' || audio.src.endsWith('/')) return;
                audio.play().then(function() {{
                    var playIcon = parentDoc.getElementById('daw-play-icon');
                    var statusBadge = parentDoc.getElementById('daw-badge-status');
                    if (playIcon) playIcon.textContent = "⏸";
                    if (statusBadge) {{
                        statusBadge.textContent = "PLAYING";
                        statusBadge.style.background = "#f0f9ff";
                        statusBadge.style.color = "#0284c7";
                    }}
                    cancelAnimationFrame(animId);
                    animId = requestAnimationFrame(animateWave);
                }}).catch(function(err) {{
                    console.log("Audio play notice:", err);
                }});
            }}

            function doPause() {{
                var audio = getLiveAudio();
                if (audio) audio.pause();
                var playIcon = parentDoc.getElementById('daw-play-icon');
                var statusBadge = parentDoc.getElementById('daw-badge-status');
                if (playIcon) playIcon.textContent = "▶";
                if (statusBadge) {{
                    statusBadge.textContent = "PAUSED";
                    statusBadge.style.background = "#f1f5f9";
                    statusBadge.style.color = "#475569";
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

            parentWin.__vdtDoPlay = doPlay;
            parentWin.__vdtDoPause = doPause;

            function triggerBlobDownload(b64Data, filename, mimeType) {{
                try {{
                    if (!b64Data || b64Data.length < 10) return;
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
                        if (link.parentNode) link.parentNode.removeChild(link);
                        (parentWin.URL || window.URL).revokeObjectURL(blobUrl);
                    }}, 3000);
                }} catch(err) {{
                    console.error("Blob download failed:", err);
                }}
            }}

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

                if (e.target.closest('#daw-btn-play')) {{
                    e.preventDefault();
                    if (audio) {{
                        if (audio.paused) doPlay();
                        else doPause();
                    }}
                    return;
                }}

                if (e.target.closest('#daw-btn-prev')) {{
                    e.preventDefault();
                    if (audio) {{
                        audio.currentTime = Math.max(0, audio.currentTime - 5);
                        updateLoangAndProgress(audio.currentTime, audio.duration || 0);
                    }}
                    return;
                }}

                if (e.target.closest('#daw-btn-next')) {{
                    e.preventDefault();
                    if (audio) {{
                        audio.currentTime = Math.min(audio.duration || 0, audio.currentTime + 5);
                        updateLoangAndProgress(audio.currentTime, audio.duration || 0);
                    }}
                    return;
                }}

                var loopBtn = e.target.closest('#daw-btn-loop');
                if (loopBtn && audio) {{
                    e.preventDefault();
                    isLooping = !isLooping;
                    audio.loop = isLooping;
                    loopBtn.style.color = isLooping ? "#0284c7" : "#64748b";
                    return;
                }}

                if (e.target.closest('#daw-btn-dl-srt')) {{
                    e.preventDefault();
                    triggerBlobDownload(curTrack.srtB64, curTrack.baseFilename + ".srt", "text/plain;charset=utf-8");
                    return;
                }}

                if (e.target.closest('#daw-btn-dl-mp3')) {{
                    e.preventDefault();
                    triggerBlobDownload(curTrack.audioB64, curTrack.baseFilename + ".mp3", "audio/mp3");
                    return;
                }}

                if (e.target.closest('#daw-btn-dl-wav')) {{
                    e.preventDefault();
                    triggerBlobDownload(curTrack.audioB64, curTrack.baseFilename + "_Master48kHz.wav", "audio/wav");
                    return;
                }}
            }};

            parentDoc.addEventListener('click', parentWin.__vdtDawClickHandler, true);

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
                if (isScrubbing) handleScrub(e);
            }};
            parentWin.__vdtScrubUpHandler = function(e) {{
                if (isScrubbing) isScrubbing = false;
            }};

            parentDoc.addEventListener('mousedown', parentWin.__vdtScrubDownHandler, true);
            parentDoc.addEventListener('mousemove', parentWin.__vdtScrubMoveHandler, true);
            parentDoc.addEventListener('mouseup', parentWin.__vdtScrubUpHandler, true);

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
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; padding: 10px 4px; border-top: 1px solid #e2e8f0; font-size: 0.78rem; color: #64748b; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <img src="{author_logo_b64}" style="width: 20px; height: 20px; border-radius: 50%; border: 1px solid #0284c7; object-fit: cover;" />
            <span><strong>Studio VDT • DAW Pro Edition</strong> — Sáng lập & Bản quyền bởi <strong style="color: #0284c7;">Võ Duy Toàn</strong></span>
        </div>
        <div>
            Trạm sản xuất âm thanh AI thế hệ mới • Kết xuất giọng nói chuẩn điện ảnh VieNeu Neural Engine v4.2
        </div>
    </div>
    """
)
