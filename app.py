"""
AI Studio: Video Dubbing & Multi-Voice Text-to-Speech
Clean, Modern & Intuitive User Interface (No Broken DOM, Smooth Caret Insertion)
"""
import asyncio
from datetime import datetime
from pathlib import Path
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
)

# 2. Modern Clean Header
st.title("🎙️ AI Audio & Video Studio")
st.caption("Studio lồng tiếng video & chuyển văn bản thành giọng đọc AI (Hỗ trợ giọng Adam Tốp Tốp & Chèn cảm xúc tức thì tại con trỏ chuột)")

# 3. Main Navigation
tab_tts, tab_dubbing = st.tabs([
    "🎙️ Tạo Giọng Nói AI (Văn bản ➡️ Âm thanh)",
    "🎬 Lồng Tiếng Video (Video Dubbing)",
])


# ==============================================================================
# TAB 1: TEXT-TO-SPEECH (TTS STUDIO)
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


def apply_sample_preset():
    chosen = st.session_state.get("sample_preset_choice")
    if chosen and chosen in sample_options:
        st.session_state["tts_main_text"] = sample_options[chosen]


# HTML & JS for Instant Caret Insertion (Using native st.html without iframe)
toolbar_html = """
<div style="margin-bottom: 8px;">
    <style>
        .emo-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
            background: #20222a;
            border: 1px solid #363945;
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 8px;
        }
        .emo-label {
            font-size: 13px;
            font-weight: 700;
            color: #ff9800;
            margin-right: 4px;
        }
        .emo-chip {
            background: #2b2d38;
            color: #f1f1f1;
            border: 1px solid #484b59;
            border-radius: 6px;
            padding: 4px 9px;
            font-size: 12.5px;
            cursor: pointer;
            transition: all 0.15s ease;
            user-select: none;
        }
        .emo-chip:hover {
            background: #ff4b4b;
            border-color: #ff4b4b;
            color: #ffffff;
            transform: translateY(-1px);
        }
        .emo-chip:active {
            transform: translateY(1px);
        }
        .emo-select-wrap {
            display: flex;
            gap: 6px;
            align-items: center;
            margin-top: 4px;
            width: 100%;
        }
        .emo-dropdown {
            background: #2b2d38;
            color: #ffffff;
            border: 1px solid #484b59;
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12.5px;
            flex-grow: 1;
            max-width: 340px;
            outline: none;
            cursor: pointer;
        }
        .emo-add-btn {
            background: #ff4b4b;
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 4px 12px;
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
        }
        .emo-add-btn:hover {
            background: #e03b3b;
        }
    </style>

    <div class="emo-bar">
        <span class="emo-label">🎯 Chèn tại con trỏ:</span>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[cười]')">😄 Cười</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[sighs]')">😮‍💨 Thở dài</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[clears throat]')">🗣️ Hắng giọng</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[laughing]')">😂 Cười to</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[crying]')">😭 Khóc</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[shocked]')">😱 Sốc/Trời ơi</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[thinking]')">🤔 Hmmm</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[panicked]')">🏃 Chết rồi!</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[angry]')">😡 Tức quá</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[nghỉ 0.5s]')">⏸️ Nghỉ 0.5s</button>
        <button type="button" class="emo-chip" onclick="window.insertCaretTag('[nghỉ 1s]')">⏳ Nghỉ 1s</button>

        <div class="emo-select-wrap">
            <span class="emo-label">📚 Kho 50+ thẻ:</span>
            <select id="caretSelectTag" class="emo-dropdown">
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
            <button type="button" class="emo-add-btn" onclick="window.insertCaretDropdown()">➕ Chèn tại con trỏ</button>
        </div>
    </div>

    <script>
        window.insertCaretTag = function(tag) {
            const textarea = document.querySelector('textarea');
            if (!textarea) return;

            const start = textarea.selectionStart !== undefined ? textarea.selectionStart : textarea.value.length;
            const end = textarea.selectionEnd !== undefined ? textarea.selectionEnd : start;
            const val = textarea.value;

            const prefix = (start > 0 && val[start - 1] !== ' ' && val[start - 1] !== '\\n') ? ' ' : '';
            const suffix = (end < val.length && val[end] !== ' ' && val[end] !== '\\n') ? ' ' : ' ';
            const insertStr = prefix + tag + suffix;

            const newVal = val.substring(0, start) + insertStr + val.substring(end);

            const nativeSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
            if (nativeSetter) {
                nativeSetter.call(textarea, newVal);
            } else {
                textarea.value = newVal;
            }

            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            const nextPos = start + insertStr.length;
            textarea.setSelectionRange(nextPos, nextPos);
            textarea.focus();
        };

        window.insertCaretDropdown = function() {
            const sel = document.getElementById('caretSelectTag');
            if (sel && sel.value) {
                window.insertCaretTag(sel.value);
            }
        };
    </script>
</div>
"""

with tab_tts:
    # 2 Cards Layout: Left (Input), Right (Settings)
    col_input, col_settings = st.columns([1.2, 0.8], gap="medium")

    with col_input:
        with st.container(border=True):
            st.markdown("### 📝 Bước 1: Nhập văn bản")

            # Caret Toolbar (Direct DOM, No Iframe)
            st.html(toolbar_html)

            # Main text area
            st.text_area(
                "Nội dung văn bản:",
                key="tts_main_text",
                height=180,
                placeholder="Nhập hoặc dán văn bản vào đây. Đặt con trỏ chuột tại bất kỳ vị trí nào rồi bấm nút cảm xúc ở trên...",
                label_visibility="collapsed",
            )

            col_preset, col_file = st.columns([1.2, 0.8])
            with col_preset:
                st.selectbox(
                    "Mẫu câu có sẵn:",
                    options=["(Chọn mẫu câu tham khảo)"] + list(sample_options.keys()),
                    index=0,
                    key="sample_preset_choice",
                    on_change=apply_sample_preset,
                )
            with col_file:
                uploaded_txt = st.file_uploader("Hoặc tải file .txt:", type=["txt"], key="txt_upload", label_visibility="collapsed")
                if uploaded_txt:
                    content_str = uploaded_txt.read().decode("utf-8")
                    if content_str != st.session_state["tts_main_text"]:
                        st.session_state["tts_main_text"] = content_str
                        st.rerun()

    with col_settings:
        with st.container(border=True):
            st.markdown("### 🎙️ Bước 2: Chọn Giọng & Tốc độ")

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
                index=0,  # Adam bựa is first
            )
            selected_voice_id = voices_dict[selected_voice_label]

            st.markdown("**Tốc độ đọc (Tempo):**")
            sp_c1, sp_c2, sp_c3 = st.columns(3)
            with sp_c1:
                if st.button("1.0x (Vừa)", use_container_width=True):
                    st.session_state["slider_speed_val"] = 0
                    st.rerun()
            with sp_c2:
                if st.button("🔥 1.15x (Tốp Tốp)", use_container_width=True):
                    st.session_state["slider_speed_val"] = 15
                    st.rerun()
            with sp_c3:
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

            # Generate button inside card
            btn_generate_tts = st.button(
                "🚀 Tạo Giọng Đọc AI Ngay",
                type="primary",
                use_container_width=True,
            )

    # Output Box
    if btn_generate_tts:
        text_to_speak = st.session_state["tts_main_text"].strip()
        if not text_to_speak:
            st.warning("⚠️ Vui lòng nhập nội dung văn bản trước khi tạo giọng đọc!")
        else:
            tts_output_dir = Path("./output/tts")
            tts_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            with st.spinner("⏳ Đang tổng hợp âm thanh giọng đọc AI chuẩn Studio..."):
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
                            )

                except Exception as err:
                    st.error(f"❌ Có lỗi xảy ra trong quá trình tạo âm thanh: {err}")


# ==============================================================================
# TAB 2: VIDEO DUBBING
# ==============================================================================
with tab_dubbing:
    col_dub_in, col_dub_set = st.columns([1, 1], gap="medium")

    with col_dub_in:
        with st.container(border=True):
            st.markdown("### 🎬 Bước 1: Tải lên Video gốc")
            uploaded_video = st.file_uploader(
                "Chọn video cần lồng tiếng (mp4, mkv, mov, webm):",
                type=["mp4", "mkv", "mov", "avi", "webm"],
                key="dub_video_uploader",
            )
            if uploaded_video:
                st.video(uploaded_video)

    with col_dub_set:
        with st.container(border=True):
            st.markdown("### ⚙️ Bước 2: Cài đặt Lồng tiếng")

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

            with st.expander("🛠️ Cài đặt nâng cao (Nhạc nền & Whisper ASR)", expanded=False):
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
                    "Âm lượng nhạc nền gốc (Audio Ducking):",
                    min_value=0.0,
                    max_value=0.5,
                    value=0.15,
                    step=0.05,
                    help="Giữ lại 15% tiếng động cơ, gió, nhạc nền gốc để video tự nhiên.",
                    key="dub_bg_vol",
                )

            if uploaded_video:
                btn_start_dub = st.button("🚀 Bắt đầu Lồng tiếng Video", type="primary", use_container_width=True, key="btn_dub")
            else:
                btn_start_dub = False

    # Video Dubbing Execution
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
                status_text.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {e}")
                st.exception(e)
