"""
AI Studio: Video Dubbing & Multi-Voice Text-to-Speech
Clean, Modern & Intuitive User Interface (Easy-to-use UX)
"""
import asyncio
from datetime import datetime
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import edge_tts

from config import DEFAULT_VOICES, LANGUAGE_NAMES, VOICES_CATALOG, DubbingConfig
from video_dubber.pipeline import VideoDubberPipeline
from video_dubber.vieneu_tts import generate_vieneu_speech, EMOTION_SOUND_MAP

# Page Configuration
st.set_page_config(
    page_title="AI Audio & Video Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Modern Custom CSS for Clean, Polished Studio Look
st.markdown(
    """
    <style>
    /* Global styles */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }
    
    /* Studio Header */
    .studio-header {
        text-align: center;
        padding: 10px 0 20px 0;
    }
    .studio-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff4b4b, #ff8c00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .studio-subtitle {
        color: #a0a0a0;
        font-size: 1rem;
    }

    /* Card styling */
    .step-card {
        background: #1e1e24;
        border: 1px solid #323541;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .step-badge {
        display: inline-block;
        background: #ff4b4b;
        color: white;
        font-size: 12px;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 20px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Result Box */
    .result-box {
        background: #18191f;
        border: 1px solid #2ecc71;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="studio-header">
        <div class="studio-title">🎙️ AI Audio & Video Studio</div>
        <div class="studio-subtitle">Lồng tiếng Video tự động & Tạo giọng đọc AI chuẩn Studio (Giọng Adam Tốp Tốp & Kho Cảm Xúc)</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Tabs
tab_tts, tab_dubbing = st.tabs([
    "🎙️ Tạo Giọng Nói AI (Văn bản ➡️ Âm thanh)",
    "🎬 Lồng Tiếng Video (Video Dubbing)",
])

# ==============================================================================
# TAB 1: TEXT-TO-SPEECH (TTS STUDIO - CLEAN & INTUITIVE)
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


# Initialize text in session state
if "tts_content_box" not in st.session_state:
    st.session_state["tts_content_box"] = (
        "Khoan đã... [clears throat] các bạn có biết chuyện gì vừa xảy ra không? "
        "Hắn nghĩ mình đã an toàn [laughing], nhưng [thinking] bất ngờ thay [shocked] "
        "cánh cửa mở toang [panicked]! [sighs] Mọi chuyện coi như kết thúc."
    )

sample_presets = {
    "🔥 Adam Review Phim Kịch Tính": (
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


def apply_sample_text():
    chosen = st.session_state.get("quick_sample_key")
    if chosen and chosen in sample_presets:
        st.session_state["tts_content_box"] = sample_presets[chosen]


# Clean HTML Toolbar with Instant Caret Insertion
ALL_EMOTION_ITEMS = [
    ("[cười]", "😄 [cười] - Cười mỉm nhẹ"),
    ("[laughing]", "😂 [laughing] - Cười to (hahaha)"),
    ("[chuckles]", "😆 [chuckles] - Cười khúc khích"),
    ("[giggles]", "🤭 [giggles] - Cười rúc rích"),
    ("[snickers]", "😼 [snickers] - Cười khẩy"),
    ("[awkward laugh]", "😅 [awkward laugh] - Cười gượng"),
    ("[sighs]", "😮‍💨 [sighs] - Thở dài (haizzz)"),
    ("[clears throat]", "🗣️ [clears throat] - Hắng giọng (e hèm)"),
    ("[crying]", "😭 [crying] - Khóc nức nở (hu hu)"),
    ("[sad]", "😢 [sad] - Buồn ghê"),
    ("[shocked]", "😱 [shocked] - Trời ơi! (sốc)"),
    ("[surprised]", "😲 [surprised] - Á há (ngạc nhiên)"),
    ("[panicked]", "🏃 [panicked] - Chết chết chết!"),
    ("[screaming]", "😱 [screaming] - Áaaaa (hét)"),
    ("[angry]", "😡 [angry] - Tức quá!"),
    ("[annoyed]", "😤 [annoyed] - Chậc (khó chịu)"),
    ("[frustrated]", "😫 [frustrated] - Trời đất ơi"),
    ("[thinking]", "🤔 [thinking] - Hmmm..."),
    ("[hesitant]", "🤐 [hesitant] - Ừm... (ngập ngừng)"),
    ("[smug]", "😎 [smug] - Biết ngay mà"),
    ("[sarcastic]", "😏 [sarcastic] - Ghê chưa"),
    ("[coughs]", "😷 [coughs] - Khụ khụ (ho)"),
    ("[sneezes]", "🤧 [sneezes] - Ách xì"),
    ("[yawns]", "🥱 [yawns] - Ngáppp"),
    ("[whispering]", "🤫 [whispering] - Psst... (thì thầm)"),
    ("[relieved]", "😌 [relieved] - Phùuu (thở phào)"),
    ("[excited]", "🤩 [excited] - Wowww"),
    ("[cheering]", "🎉 [cheering] - Yeahhhh!"),
    ("[happy]", "😄 [happy] - Vui quá"),
    ("[curious]", "🧐 [curious] - Ủa?"),
    ("[confused]", "🤨 [confused] - Hả?"),
    ("[nghỉ 0.5s]", "⏸️ [nghỉ 0.5s] - Ngắt nhịp lửng lơ"),
    ("[nghỉ 1s]", "⏳ [nghỉ 1s] - Khoảng lặng kịch tính"),
]


def render_cursor_toolbar():
    options_html = "".join([f'<option value="{tag}">{lbl}</option>' for tag, lbl in ALL_EMOTION_ITEMS])

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0; padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: transparent; color: #fff;
            }}
            .toolbar {{
                display: flex; flex-direction: column; gap: 8px;
                padding-bottom: 8px;
            }}
            .btn-row {{
                display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
            }}
            .tag-title {{
                font-size: 13px; font-weight: 700; color: #ff9800; margin-right: 6px;
            }}
            .tag-btn {{
                background: #2a2c36; color: #f0f0f0;
                border: 1px solid #454854; border-radius: 6px;
                padding: 4px 10px; font-size: 12.5px; cursor: pointer;
                transition: all 0.15s ease;
            }}
            .tag-btn:hover {{
                background: #ff4b4b; border-color: #ff4b4b; color: #fff;
                transform: translateY(-1px);
            }}
            .more-row {{
                display: flex; gap: 8px; align-items: center; margin-top: 2px;
            }}
            .tag-select {{
                background: #2a2c36; color: #fff; border: 1px solid #454854;
                border-radius: 6px; padding: 5px 10px; font-size: 12.5px;
                flex-grow: 1; max-width: 320px; outline: none; cursor: pointer;
            }}
            .insert-btn {{
                background: #ff4b4b; color: white; border: none;
                border-radius: 6px; padding: 5px 12px; font-size: 12.5px;
                font-weight: 600; cursor: pointer;
            }}
            .insert-btn:hover {{ background: #e03e3e; }}
        </style>
    </head>
    <body>
        <div class="toolbar">
            <div class="btn-row">
                <span class="tag-title">🎯 Cảm xúc nhanh:</span>
                <button class="tag-btn" onclick="insertTag('[cười]')">😄 Cười</button>
                <button class="tag-btn" onclick="insertTag('[sighs]')">😮‍💨 Thở dài</button>
                <button class="tag-btn" onclick="insertTag('[clears throat]')">🗣️ Hắng giọng</button>
                <button class="tag-btn" onclick="insertTag('[laughing]')">😂 Cười to</button>
                <button class="tag-btn" onclick="insertTag('[crying]')">😭 Khóc</button>
                <button class="tag-btn" onclick="insertTag('[shocked]')">😱 Sốc/Trời ơi</button>
                <button class="tag-btn" onclick="insertTag('[thinking]')">🤔 Hmmm</button>
                <button class="tag-btn" onclick="insertTag('[panicked]')">🏃 Chết rồi!</button>
                <button class="tag-btn" onclick="insertTag('[angry]')">😡 Tức quá</button>
                <button class="tag-btn" onclick="insertTag('[nghỉ 0.5s]')">⏸️ Nghỉ 0.5s</button>
            </div>
            <div class="more-row">
                <span class="tag-title">📚 Kho 50+ thẻ khác:</span>
                <select id="dropTag" class="tag-select">
                    {options_html}
                </select>
                <button class="insert-btn" onclick="insertFromDropdown()">➕ Chèn tại con trỏ</button>
            </div>
        </div>

        <script>
            function insertTag(tag) {{
                try {{
                    const parentDoc = window.parent.document;
                    const textarea = parentDoc.querySelector('textarea');
                    if (!textarea) return;

                    const start = textarea.selectionStart !== undefined ? textarea.selectionStart : textarea.value.length;
                    const end = textarea.selectionEnd !== undefined ? textarea.selectionEnd : start;
                    const val = textarea.value;

                    const prefix = (start > 0 && val[start - 1] !== ' ' && val[start - 1] !== '\\n') ? ' ' : '';
                    const suffix = (end < val.length && val[end] !== ' ' && val[end] !== '\\n') ? ' ' : ' ';
                    const insertVal = prefix + tag + suffix;

                    const newVal = val.substring(0, start) + insertVal + val.substring(end);

                    const nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, "value").set;
                    if (nativeSetter) {{
                        nativeSetter.call(textarea, newVal);
                    }} else {{
                        textarea.value = newVal;
                    }}

                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    const newPos = start + insertVal.length;
                    textarea.setSelectionRange(newPos, newPos);
                    textarea.focus();
                }} catch(e) {{
                    console.error(e);
                }}
            }}

            function insertFromDropdown() {{
                const d = document.getElementById('dropTag');
                if (d && d.value) insertTag(d.value);
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=75)


with tab_tts:
    # 2 Column layout: Left (Input), Right (Voice Settings)
    col_input, col_settings = st.columns([1.3, 0.7], gap="medium")

    with col_input:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-badge">Bước 1</span> **Nhập nội dung văn bản**', unsafe_allow_html=True)

        # Caret toolbar
        render_cursor_toolbar()

        # Text area
        st.text_area(
            "Nội dung văn bản:",
            key="tts_content_box",
            height=180,
            placeholder="Gõ hoặc dán văn bản vào đây. Nhấp chuột vào bất kỳ chỗ nào rồi bấm các nút cảm xúc ở trên...",
            label_visibility="collapsed",
        )

        col_sample_sel, col_upload = st.columns([1.2, 0.8])
        with col_sample_sel:
            st.selectbox(
                "Chèn mẫu câu review/diễn xuất:",
                options=["(Chọn mẫu văn bản nhanh)"] + list(sample_presets.keys()),
                index=0,
                key="quick_sample_key",
                on_change=apply_sample_text,
            )
        with col_upload:
            uploaded_txt = st.file_uploader("Tải file .txt:", type=["txt"], key="txt_upload", label_visibility="collapsed")
            if uploaded_txt:
                txt_data = uploaded_txt.read().decode("utf-8")
                if txt_data != st.session_state["tts_content_box"]:
                    st.session_state["tts_content_box"] = txt_data
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col_settings:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-badge">Bước 2</span> **Chọn Giọng đọc & Tốc độ**', unsafe_allow_html=True)

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
            index=0,  # Adam bựa default
            help="Giọng Adam bựa rất thích hợp cho review phim và video meme.",
        )
        selected_voice_id = voices_dict[selected_voice_label]

        st.markdown("**Tốc độ nói (Tempo):**")
        col_sp1, col_sp2, col_sp3 = st.columns(3)
        with col_sp1:
            if st.button("1.0x (Vừa)", use_container_width=True):
                st.session_state["slider_speed_val"] = 0
                st.rerun()
        with col_sp2:
            if st.button("🔥 1.15x (Tốp Tốp)", use_container_width=True):
                st.session_state["slider_speed_val"] = 15
                st.rerun()
        with col_sp3:
            if st.button("1.25x (Nhanh)", use_container_width=True):
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

        st.markdown("</div>", unsafe_allow_html=True)

        # Big Generate Button
        btn_generate_tts = st.button(
            "🚀 Tạo Giọng Đọc AI Ngay",
            type="primary",
            use_container_width=True,
        )

    # Result Box
    if btn_generate_tts:
        text_to_speak = st.session_state["tts_content_box"].strip()
        if not text_to_speak:
            st.warning("⚠️ Vui lòng nhập nội dung văn bản trước khi tạo giọng đọc!")
        else:
            tts_output_dir = Path("./output/tts")
            tts_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            with st.spinner("⏳ Đang tổng hợp giọng nói AI chuẩn Studio..."):
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

                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.success("🎉 Đã tạo giọng nói thành công!")
                    st.markdown(f"**Giọng đọc:** `{selected_voice_label}` | **Tốc độ:** `{speed_factor:.2f}x`")
                    st.audio(str(out_file), format="audio/mp3")

                    with open(out_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Tải file âm thanh MP3",
                            data=f,
                            file_name=out_file.name,
                            mime="audio/mpeg",
                            type="primary",
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

                except Exception as err:
                    st.error(f"❌ Có lỗi xảy ra: {err}")


# ==============================================================================
# TAB 2: VIDEO DUBBING (CLEAN & INTUITIVE)
# ==============================================================================
with tab_dubbing:
    col_dub_step1, col_dub_step2 = st.columns([1, 1], gap="large")

    with col_dub_step1:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-badge">Bước 1</span> **Tải lên Video gốc**', unsafe_allow_html=True)

        uploaded_video = st.file_uploader(
            "Chọn file video (mp4, mkv, mov, webm):",
            type=["mp4", "mkv", "mov", "avi", "webm"],
            key="dub_video_uploader",
        )
        if uploaded_video:
            st.video(uploaded_video)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_dub_step2:
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown('<span class="step-badge">Bước 2</span> **Cài đặt Lồng tiếng**', unsafe_allow_html=True)

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
                "Ngôn ngữ gốc video:",
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
                help="Giữ lại 15% nhạc nền gốc giúp video sống động và tự nhiên.",
                key="dub_bg_vol",
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if uploaded_video:
            btn_start_dub = st.button("🚀 Bắt đầu Lồng tiếng Video", type="primary", use_container_width=True, key="btn_dub")
        else:
            btn_start_dub = False

    # Video Dubbing Processing & Output
    if btn_start_dub and uploaded_video:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
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

            status_text.success("🎉 Lồng tiếng Video hoàn tất thành công!")
            progress_bar.progress(1.0)
            st.video(str(result_path))

            col_down1, col_down2 = st.columns(2)
            with col_down1:
                with open(result_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Tải Video đã lồng tiếng (.mp4)",
                        data=f,
                        file_name=result_path.name,
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True,
                    )
            with col_down2:
                srt_file = result_path.with_suffix(".srt")
                if srt_file.exists():
                    with open(srt_file, "r", encoding="utf-8") as f:
                        st.download_button(
                            label="📄 Tải Phụ đề lồng tiếng (.srt)",
                            data=f.read(),
                            file_name=srt_file.name,
                            mime="text/plain",
                            use_container_width=True,
                        )
        except Exception as e:
            status_text.error(f"❌ Quá trình lồng tiếng bị lỗi: {e}")
            st.exception(e)
        st.markdown("</div>", unsafe_allow_html=True)
