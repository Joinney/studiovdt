"""
AI Studio: Video Dubbing & Multi-Voice Text-to-Speech
Mobile-First Fully Responsive Design (Tương thích 100% điện thoại di động & máy tính)
"""
import asyncio
import base64
from datetime import datetime
from pathlib import Path
import urllib.parse
import streamlit as st
import edge_tts

from config import DEFAULT_VOICES, LANGUAGE_NAMES, VOICES_CATALOG, DubbingConfig
from video_dubber.pipeline import VideoDubberPipeline
from video_dubber.vieneu_tts import generate_vieneu_speech, EMOTION_SOUND_MAP

# 1. Page Configuration
st.set_page_config(
    page_title="AI Audio & Video Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Mobile-First Responsive CSS
st.html(
    """
    <style>
    /* Adjust Streamlit top header bar */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.5rem !important;
        z-index: 10;
    }

    /* Global Container Padding with safe top clearance */
    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1200px;
    }

    /* Studio Header */
    .mobile-header {
        text-align: center;
        padding: 5px 0 15px 0;
        margin-top: 5px;
        margin-bottom: 5px;
    }
    .mobile-title {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff4b4b, #ff8c00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    .mobile-subtitle {
        color: #9ea3b0;
        font-size: 0.9rem;
    }

    /* Mobile Enhancements for Phones (< 768px) */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 3.8rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
        .mobile-title {
            font-size: 1.45rem !important;
        }
        .mobile-subtitle {
            font-size: 0.8rem !important;
        }
        /* Buttons larger touch target for thumbs */
        button[kind="primary"], button[kind="secondary"] {
            min-height: 42px !important;
            font-size: 14px !important;
        }
        /* Tab labels font size */
        div[data-baseweb="tab-list"] button {
            font-size: 13.5px !important;
            padding: 8px 10px !important;
        }
    }
    </style>
    """
)

def get_author_logo_base64():
    logo_path = Path(__file__).parent / "assets" / "author.png"
    if logo_path.exists():
        encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    return "https://github.com/Joinney.png"

author_logo_b64 = get_author_logo_base64()

# Header with Author Branding
st.markdown(
    f"""
    <div class="mobile-header">
        <div style="display: inline-flex; align-items: center; justify-content: center; gap: 14px; margin-bottom: 6px; flex-wrap: wrap;">
            <img src="{author_logo_b64}" alt="Võ Duy Toàn" style="width: 62px; height: 62px; border-radius: 50%; border: 2.5px solid #ff4b4b; box-shadow: 0 0 16px rgba(255, 75, 75, 0.45); object-fit: cover;" />
            <div style="text-align: left;">
                <div class="mobile-title" style="margin: 0; line-height: 1.15;">Studio VDT • AI Dubbing & TTS</div>
                <div style="font-size: 0.88rem; color: #ff8c00; font-weight: 600; margin-top: 3px;">
                    ✨ Tác giả: <span style="color: #ffffff; font-weight: 700;">Võ Duy Toàn</span>
                </div>
            </div>
        </div>
        <div class="mobile-subtitle">Kho 31 giọng VieNeu-TTS chuẩn Studio 48kHz • 50+ thẻ cảm xúc • Lồng tiếng Video tự động</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Navigation Tabs
tab_tts, tab_dubbing = st.tabs([
    "🎙️ Tạo Giọng Nói AI",
    "🎬 Lồng Tiếng Video",
])


# ==============================================================================
# TAB 1: TEXT-TO-SPEECH (TTS STUDIO - MOBILE OPTIMIZED)
# ==============================================================================
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


# Initialize session state
if "tts_main_text" not in st.session_state:
    st.session_state["tts_main_text"] = (
        "Khoan đã... [clears throat] các bạn có biết chuyện gì vừa xảy ra không? "
        "Hắn nghĩ mình đã an toàn [laughing], nhưng [thinking] bất ngờ thay [shocked] "
        "cánh cửa mở toang [panicked]! [sighs] Mọi chuyện coi như kết thúc."
    )

sample_options = {
    "🔥 Adam Review Phim Gốc (Chuẩn Tốp Tốp)": (
        "Hello các con vợ, hôm nay Adam lại lên đồ ngon cho cả nhà đây! [cười] "
        "Coi hết clip rồi hãy lướt nha!"
    ),
    "🎬 Adam Review Phim Kịch Tính": (
        "Khoan đã... [clears throat] các bạn có biết chuyện gì vừa xảy ra không? "
        "Hắn nghĩ mình đã an toàn [laughing], nhưng [thinking] bất ngờ thay [shocked] "
        "cánh cửa mở toang [panicked]! [sighs] Mọi chuyện coi như kết thúc."
    ),
    "😂 Meme Hài Hước / Đời Sống": (
        "Trời ơi là trời [frustrated]! [coughs] Tôi vừa thấy cái gì thế này? [awkward laugh] "
        "Tưởng thế nào, hóa ra là như thế [snickers]! [smug] Biết ngay mà!"
    ),
    "😭 Cảnh Xúc Động / Buồn Bã": (
        "Đừng đi mà... [crying] Em biết em sai rồi [apologetic]. [groans] "
        "Tại sao mọi chuyện lại ra nông nỗi này? [sad] Anh hãy ở lại đi mà [pleading]!"
    ),
    "📖 Kể Chuyện Nhẹ Nhàng": (
        "Đêm đó trời mưa rả rích ngoài hiên. [sighs] "
        "Anh ấy nhìn tôi rồi mỉm cười nói: 'Đừng lo, mọi chuyện rồi sẽ qua thôi' [chuckles]."
    ),
}


def apply_sample_preset():
    chosen = st.session_state.get("sample_preset_choice")
    if chosen and chosen in sample_options:
        st.session_state["tts_main_text"] = sample_options[chosen]


# Dynamic Script Injection for Cursor/Caret Insertion Engine
caret_js_code = """
(function() {
    window.__vdtLastPos = null;

    function getTa() {
        var el = document.activeElement;
        if (el && el.tagName === 'TEXTAREA') return el;
        return document.querySelector('div[data-testid="stTextArea"] textarea') || document.querySelector('textarea');
    }

    function savePos() {
        var ta = getTa();
        if (ta && typeof ta.selectionStart === 'number') {
            window.__vdtLastPos = {
                start: ta.selectionStart,
                end: ta.selectionEnd
            };
        }
    }

    ['focus', 'click', 'keyup', 'mouseup', 'select', 'input', 'touchend'].forEach(function(evt) {
        document.addEventListener(evt, function(e) {
            if (e.target && e.target.tagName === 'TEXTAREA') {
                savePos();
            }
        }, true);
    });

    document.addEventListener('selectionchange', function() {
        var el = document.activeElement;
        if (el && el.tagName === 'TEXTAREA') {
            savePos();
        }
    });

    window.insertCaretTag = function(tag) {
        var ta = getTa();
        if (!ta) return;

        ta.focus();

        var start = (window.__vdtLastPos && typeof window.__vdtLastPos.start === 'number') 
            ? window.__vdtLastPos.start 
            : (typeof ta.selectionStart === 'number' ? ta.selectionStart : (ta.value ? ta.value.length : 0));
        var end = (window.__vdtLastPos && typeof window.__vdtLastPos.end === 'number') 
            ? window.__vdtLastPos.end 
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
            inserted = document.execCommand('insertText', false, insertStr);
        } catch (e) {
            inserted = false;
        }

        if (!inserted) {
            var newVal = val.substring(0, start) + insertStr + val.substring(end);
            var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
            if (setter && setter.set) {
                setter.set.call(ta, newVal);
            } else {
                ta.value = newVal;
            }
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            ta.dispatchEvent(new Event('change', { bubbles: true }));
            var nextPos = start + insertStr.length;
            ta.setSelectionRange(nextPos, nextPos);
            window.__vdtLastPos = { start: nextPos, end: nextPos };
        } else {
            window.__vdtLastPos = { start: ta.selectionStart, end: ta.selectionEnd };
        }
    };

    window.insertCaretDropdown = function() {
        var sel = document.getElementById('caretSelectTag');
        if (sel && sel.value) {
            window.insertCaretTag(sel.value);
        }
    };
})();
"""

encoded_caret_js = urllib.parse.quote(caret_js_code)

# Mobile-Optimized Caret Toolbar HTML
mobile_toolbar_html = f"""
<div style="margin-bottom: 6px;">
    <style>
        .m-bar {{
            background: #1e2028;
            border: 1px solid #363a47;
            border-radius: 8px;
            padding: 8px 10px;
            margin-bottom: 6px;
        }}
        .m-title {{
            font-size: 12.5px;
            font-weight: 700;
            color: #ff9800;
            margin-bottom: 6px;
            display: block;
        }}
        .m-buttons-wrap {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 6px;
        }}
        .m-chip {{
            background: #2b2e3b;
            color: #ffffff;
            border: 1px solid #484d5f;
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.15s ease;
            user-select: none;
            touch-action: manipulation;
        }}
        .m-chip:active, .m-chip:hover {{
            background: #ff4b4b;
            border-color: #ff4b4b;
            color: #ffffff;
        }}
        .m-dropdown-row {{
            display: flex;
            gap: 6px;
            align-items: center;
            width: 100%;
        }}
        .m-dropdown {{
            background: #2b2e3b;
            color: #ffffff;
            border: 1px solid #484d5f;
            border-radius: 6px;
            padding: 5px 8px;
            font-size: 12px;
            flex-grow: 1;
            outline: none;
            cursor: pointer;
            height: 34px;
        }}
        .m-insert-btn {{
            background: #ff4b4b;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 0 12px;
            height: 34px;
            font-size: 12.5px;
            font-weight: bold;
            cursor: pointer;
            white-space: nowrap;
            touch-action: manipulation;
        }}
        .m-insert-btn:active {{
            background: #d83535;
        }}

        @media (max-width: 480px) {{
            .m-chip {{
                padding: 6px 8px;
                font-size: 11.5px;
            }}
            .m-dropdown-row {{
                flex-direction: column;
                align-items: stretch;
            }}
            .m-insert-btn {{
                width: 100%;
            }}
        }}
    </style>

    <div class="m-bar">
        <span class="m-title">🎯 Bấm chèn cảm xúc tại vị trí con trỏ:</span>
        <div class="m-buttons-wrap">
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[cười]')">😄 Cười</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[sighs]')">😮‍💨 Thở dài</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[clears throat]')">🗣️ Hắng giọng</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[laughing]')">😂 Cười to</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[crying]')">😭 Khóc</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[shocked]')">😱 Sốc</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[thinking]')">🤔 Hmmm</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[panicked]')">🏃 Chết rồi!</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[angry]')">😡 Tức quá</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[nghỉ 0.5s]')">⏸️ Nghỉ 0.5s</button>
            <button type="button" class="m-chip" onmousedown="event.preventDefault();" onclick="window.insertCaretTag('[nghỉ 1s]')">⏳ Nghỉ 1s</button>
        </div>

        <div class="m-dropdown-row">
            <select id="caretSelectTag" class="m-dropdown">
                <option value="[crying]">😭 [crying] - hu hu (khóc)</option>
                <option value="[coughs]">😷 [coughs] - khụ khụ (ho)</option>
                <option value="[lip smacks]">😋 [lip smacks] - chẹp chẹp</option>
                <option value="[annoyed]">😤 [annoyed] - chậc (khó chịu)</option>
                <option value="[screaming]">😱 [screaming] - áaaaa (hét)</option>
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
                <option value="[snickers]">😼 [snickers] - khì khì (cười khẩy)</option>
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
            </select>
            <button type="button" class="m-insert-btn" onmousedown="event.preventDefault();" onclick="window.insertCaretDropdown()">➕ Chèn tại con trỏ</button>
        </div>
    </div>

    <!-- Active dynamic injection triggering execution in React DOM -->
    <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" style="display:none;" onload="if(!window.insertCaretTag){{var s=document.createElement('script');s.id='caret-script';s.text=decodeURIComponent('{encoded_caret_js}');document.head.appendChild(s);}}" onerror="this.onload()" />
</div>
"""

with tab_tts:
    # Responsive Columns (auto stacks on mobile)
    col_input, col_settings = st.columns([1.15, 0.85], gap="medium")

    with col_input:
        with st.container(border=True):
            st.markdown("#### 📝 Bước 1: Nhập văn bản")

            # Mobile-friendly Caret Toolbar
            st.html(mobile_toolbar_html)

            # Text Area
            st.text_area(
                "Nội dung văn bản:",
                key="tts_main_text",
                height=160,
                placeholder="Nhập hoặc dán văn bản vào đây. Nhấp chuột vào bất kỳ vị trí nào rồi bấm nút cảm xúc...",
                label_visibility="collapsed",
            )

            # Fallback 1-click emotion insert
            c_tag1, c_tag2 = st.columns([0.72, 0.28])
            with c_tag1:
                st.selectbox(
                    "Thêm nhanh thẻ cảm xúc:",
                    options=[
                        "[cười] - Cười vui vẻ",
                        "[sighs] - Thở dài ngao ngán",
                        "[clears throat] - Hắng giọng",
                        "[laughing] - Cười to ha ha",
                        "[crying] - Khóc hu hu",
                        "[shocked] - Sốc, kinh ngạc",
                        "[thinking] - Hmmm suy nghĩ",
                        "[panicked] - Chết rồi!",
                        "[angry] - Tức giận",
                        "[nghỉ 0.5s] - Tạm dừng 0.5s",
                        "[nghỉ 1s] - Tạm dừng 1s",
                    ],
                    key="quick_tag_choice",
                    label_visibility="collapsed",
                )
            with c_tag2:
                if st.button("➕ Thêm thẻ", key="btn_quick_add_tag", help="Thêm thẻ cảm xúc đã chọn vào văn bản"):
                    clean_code = st.session_state["quick_tag_choice"].split(" - ")[0]
                    cur = st.session_state.get("tts_main_text", "")
                    st.session_state["tts_main_text"] = cur + f" {clean_code}"
                    st.rerun()

            c_preset, c_upload = st.columns([1.1, 0.9])
            with c_preset:
                st.selectbox(
                    "Mẫu câu:",
                    options=["(Chọn mẫu câu tham khảo)"] + list(sample_options.keys()),
                    index=0,
                    key="sample_preset_choice",
                    on_change=apply_sample_preset,
                    label_visibility="collapsed",
                )
            with c_upload:
                uploaded_txt = st.file_uploader("File .txt", type=["txt"], key="txt_upload", label_visibility="collapsed")
                if uploaded_txt:
                    content_str = uploaded_txt.read().decode("utf-8")
                    if content_str != st.session_state["tts_main_text"]:
                        st.session_state["tts_main_text"] = content_str
                        st.rerun()

    with col_settings:
        with st.container(border=True):
            st.markdown("#### 🎙️ Bước 2: Chọn Giọng & Tốc độ")

            tts_lang = st.selectbox(
                "Ngôn ngữ:",
                options=list(LANGUAGE_NAMES.keys()),
                index=0,
                format_func=lambda code: LANGUAGE_NAMES.get(code, code),
                key="tts_lang_select",
            )

            voices_dict = VOICES_CATALOG.get(tts_lang, VOICES_CATALOG["vi"])

            selected_voice_label = st.selectbox(
                "Giọng đọc AI:",
                options=list(voices_dict.keys()),
                index=0,  # Adam
            )
            selected_voice_id = voices_dict[selected_voice_label]

            st.markdown("**Tốc độ nói (Tempo):**")
            sp1, sp2, sp3 = st.columns(3)
            with sp1:
                if st.button("1.0x", use_container_width=True):
                    st.session_state["slider_speed_val"] = 0
                    st.rerun()
            with sp2:
                if st.button("🔥 1.15x", use_container_width=True):
                    st.session_state["slider_speed_val"] = 15
                    st.rerun()
            with sp3:
                if st.button("1.25x", use_container_width=True):
                    st.session_state["slider_speed_val"] = 25
                    st.rerun()

            current_speed = st.session_state.get("slider_speed_val", 15)
            tts_rate_val = st.slider(
                "Tùy chỉnh tốc độ %:",
                min_value=-50,
                max_value=100,
                value=current_speed,
                step=5,
                format="%d%%",
                key="slider_speed_widget",
            )
            st.session_state["slider_speed_val"] = tts_rate_val

            speed_factor = 1.0 + (tts_rate_val / 100.0)
            rate_str = f"{'+' if tts_rate_val >= 0 else ''}{tts_rate_val}%"

            # Primary Big Action Button
            btn_generate_tts = st.button(
                "🚀 Tạo Giọng Đọc AI Ngay",
                type="primary",
                use_container_width=True,
            )

    # Result Box
    if btn_generate_tts:
        text_to_speak = st.session_state["tts_main_text"].strip()
        if not text_to_speak:
            st.warning("⚠️ Vui lòng nhập nội dung văn bản trước khi tạo giọng đọc!")
        else:
            tts_output_dir = Path("./output/tts")
            tts_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            with st.spinner("⏳ Đang tổng hợp âm thanh giọng đọc AI..."):
                try:
                    if selected_voice_id.startswith("vieneu:"):
                        clean_v = selected_voice_id.replace("vieneu:", "")
                        out_file = tts_output_dir / f"tts_vieneu_{clean_v}_{timestamp}.mp3"
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

                    with st.container(border=True):
                        st.success("🎉 Đã tạo giọng nói thành công!")
                        st.markdown(f"**Giọng đọc:** `{selected_voice_label}` | **Tốc độ:** `{speed_factor:.2f}x`")
                        st.audio(str(out_file), format="audio/mp3")

                        with open(out_file, "rb") as f:
                            st.download_button(
                                label="⬇️ Tải file âm thanh MP3 về máy",
                                data=f,
                                file_name=out_file.name,
                                mime="audio/mpeg",
                                type="primary",
                                use_container_width=True,
                            )

                except Exception as err:
                    st.error(f"❌ Có lỗi xảy ra trong quá trình tạo âm thanh: {err}")


# ==============================================================================
# TAB 2: VIDEO DUBBING (MOBILE OPTIMIZED)
# ==============================================================================
with tab_dubbing:
    col_dub_in, col_dub_set = st.columns([1, 1], gap="medium")

    with col_dub_in:
        with st.container(border=True):
            st.markdown("#### 🎬 Bước 1: Tải lên Video gốc")
            uploaded_video = st.file_uploader(
                "Chọn video (mp4, mkv, mov, webm):",
                type=["mp4", "mkv", "mov", "avi", "webm"],
                key="dub_video_uploader",
            )
            if uploaded_video:
                st.video(uploaded_video)

    with col_dub_set:
        with st.container(border=True):
            st.markdown("#### ⚙️ Bước 2: Cài đặt Lồng tiếng")

            dub_target_lang = st.selectbox(
                "Ngôn ngữ lồng tiếng đích:",
                options=list(LANGUAGE_NAMES.keys()),
                index=0,
                format_func=lambda code: LANGUAGE_NAMES.get(code, code),
                key="dub_target_lang",
            )

            catalog_for_target = VOICES_CATALOG.get(dub_target_lang, VOICES_CATALOG["vi"])
            selected_dub_voice_label = st.selectbox(
                "Giọng đọc AI lồng tiếng:",
                options=list(catalog_for_target.keys()),
                index=0,
                key="dub_voice_select",
            )
            selected_dub_voice = catalog_for_target[selected_dub_voice_label]

            with st.expander("🛠️ Cài đặt nâng cao (Nhạc nền & Whisper)", expanded=False):
                dub_source_lang = st.selectbox(
                    "Ngôn ngữ gốc của video:",
                    options=["auto"] + list(LANGUAGE_NAMES.keys()),
                    index=0,
                    format_func=lambda code: "Tự động phát hiện" if code == "auto" else LANGUAGE_NAMES.get(code, code),
                    key="dub_source_lang",
                )
                whisper_model = st.selectbox(
                    "Model Whisper nhận diện:",
                    options=["tiny", "base", "small", "medium", "large-v3"],
                    index=1,
                    key="dub_whisper_model",
                )
                bg_vol = st.slider(
                    "Âm lượng nhạc nền gốc (Ducking):",
                    min_value=0.0,
                    max_value=0.5,
                    value=0.15,
                    step=0.05,
                    help="Giữ lại 15% tiếng động cơ, gió, nhạc nền gốc.",
                    key="dub_bg_vol",
                )

            if uploaded_video:
                btn_start_dub = st.button("🚀 Bắt đầu Lồng tiếng Video", type="primary", use_container_width=True, key="btn_dub")
            else:
                btn_start_dub = False

    # Video Dubbing Processing
    if btn_start_dub and uploaded_video:
        with st.container(border=True):
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            temp_input = Path("./temp") / uploaded_video.name
            temp_input.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_input, "wb") as f:
                f.write(uploaded_video.getbuffer())

            output_video_path = Path("./output") / f"{temp_input.stem}_dubbed_{dub_target_lang}.mp4"

            cfg = DubbingConfig(
                whisper_model=whisper_model,
                source_language=dub_source_lang,
                target_language=dub_target_lang,
                tts_voice=selected_dub_voice,
                original_audio_volume=bg_vol,
            )

            pipeline = VideoDubberPipeline(cfg)

            def on_progress(msg: str, frac: float):
                status_text.info(f"⏳ {msg}")
                progress_bar.progress(frac)

            try:
                result_path = pipeline.process(
                    video_path=temp_input,
                    output_path=output_video_path,
                    progress_callback=on_progress,
                )

                status_text.success("🎉 Đã hoàn thành lồng tiếng video thành công!")
                progress_bar.progress(1.0)
                st.video(str(result_path))

                c_down1, c_down2 = st.columns(2)
                with c_down1:
                    with open(result_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Tải Video (.mp4)",
                            data=f,
                            file_name=result_path.name,
                            mime="video/mp4",
                            type="primary",
                            use_container_width=True,
                        )
                with c_down2:
                    srt_file = result_path.with_suffix(".srt")
                    if srt_file.exists():
                        with open(srt_file, "r", encoding="utf-8") as f:
                            st.download_button(
                                label="📄 Tải Phụ đề (.srt)",
                                data=f.read(),
                                file_name=srt_file.name,
                                mime="text/plain",
                                use_container_width=True,
                            )
            except Exception as e:
                status_text.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {e}")
                st.exception(e)

# Footer
st.markdown(
    f"""
    <div style="text-align: center; margin-top: 40px; padding: 18px 10px 10px 10px; border-top: 1px solid rgba(255, 255, 255, 0.08); color: #8a8f9d; font-size: 0.84rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap;">
            <img src="{author_logo_b64}" style="width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid #ff4b4b; object-fit: cover;" />
            <span style="font-weight: 700; color: #ffffff;">Studio VDT</span> — Sáng lập & Bản quyền bởi <span style="color: #ff4b4b; font-weight: 800;">Võ Duy Toàn</span>
        </div>
        <div style="font-size: 0.78rem; color: #6b7280;">
            Hệ thống lồng tiếng video & tạo giọng đọc AI đa cảm xúc • Tích hợp trọn bộ 31 giọng VieNeu-TTS
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
