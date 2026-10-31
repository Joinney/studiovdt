"""
AI Studio: Video Dubbing & Multi-Voice Text-to-Speech (Edge-TTS + VieNeu-TTS with Instant Emotion Tags)
Run with: streamlit run app.py
"""
import asyncio
from datetime import datetime
from pathlib import Path
import streamlit as st
import edge_tts

from config import DEFAULT_VOICES, LANGUAGE_NAMES, VOICES_CATALOG, DubbingConfig
from video_dubber.pipeline import VideoDubberPipeline
from video_dubber.vieneu_tts import generate_vieneu_speech

st.set_page_config(
    page_title="AI Dubbing & TTS Studio",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ AI Audio & Video Studio")
st.caption("Lồng tiếng video tự động & Chuyển đổi văn bản thành giọng nói (Hỗ trợ giọng Adam Tốp Tốp & Thẻ cảm xúc tức thì)")

tab_dubbing, tab_tts = st.tabs([
    "🎬 Lồng tiếng Video (Video Dubbing)",
    "🎙️ Văn bản sang Âm thanh (Text to Speech - Đa giọng đọc & Cảm xúc)",
])


# ==============================================================================
# TAB 1: VIDEO DUBBING
# ==============================================================================
with tab_dubbing:
    st.subheader("🎬 Quy trình lồng tiếng Video tự động")
    st.write("Tách âm thanh gốc ➡️ Nhận diện giọng nói (Whisper) ➡️ Dịch thuật ➡️ Sinh giọng đọc AI (Adam / Hoài My...) ➡️ Đồng bộ thời gian ➡️ Hòa âm video.")

    with st.expander("⚙️ Tùy chỉnh tham số Lồng tiếng", expanded=True):
        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)

        with col_cfg1:
            dub_target_lang = st.selectbox(
                "Ngôn ngữ lồng tiếng đích:",
                options=list(LANGUAGE_NAMES.keys()),
                index=0,
                format_func=lambda code: LANGUAGE_NAMES.get(code, code),
                key="dub_target_lang",
            )
            dub_source_lang = st.selectbox(
                "Ngôn ngữ gốc của video:",
                options=["auto"] + list(LANGUAGE_NAMES.keys()),
                index=0,
                format_func=lambda code: "Tự động nhận diện (Auto-detect)" if code == "auto" else LANGUAGE_NAMES.get(code, code),
                key="dub_source_lang",
            )

        with col_cfg2:
            catalog_for_target = VOICES_CATALOG.get(dub_target_lang, VOICES_CATALOG["vi"])
            selected_dub_voice_label = st.selectbox(
                "Giọng đọc AI lồng tiếng:",
                options=list(catalog_for_target.keys()),
                index=0,
                key="dub_voice_select",
            )
            selected_dub_voice = catalog_for_target[selected_dub_voice_label]

            whisper_model = st.selectbox(
                "Mô hình Whisper (ASR):",
                options=["tiny", "base", "small", "medium", "large-v3"],
                index=1,
                help="Model càng lớn thì nhận diện càng chính xác nhưng xử lý lâu hơn.",
                key="dub_whisper_model",
            )

        with col_cfg3:
            bg_vol = st.slider(
                "Âm lượng nhạc nền gốc (Audio Ducking):",
                min_value=0.0,
                max_value=0.5,
                value=0.15,
                step=0.05,
                help="0: Tắt hẳn tiếng gốc. 0.15: Giữ lại 15% tiếng động cơ, gió, nhạc nền gốc.",
                key="dub_bg_vol",
            )

    col_dub_in, col_dub_out = st.columns(2)

    with col_dub_in:
        uploaded_video = st.file_uploader(
            "Chọn file video cần lồng tiếng:",
            type=["mp4", "mkv", "mov", "avi", "webm"],
            key="dub_video_uploader",
        )
        if uploaded_video:
            st.video(uploaded_video)
            btn_start_dub = st.button("🚀 Bắt đầu Lồng tiếng Video", type="primary", use_container_width=True, key="btn_dub")
        else:
            btn_start_dub = False

    with col_dub_out:
        if btn_start_dub and uploaded_video:
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

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    with open(result_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Tải Video đã lồng tiếng (.mp4)",
                            data=f,
                            file_name=result_path.name,
                            mime="video/mp4",
                            use_container_width=True,
                        )
                with col_d2:
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


# ==============================================================================
# TAB 2: TEXT-TO-SPEECH (TTS STUDIO WITH INSTANT EMOTIONS & SPEED CONTROL)
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


# Session state initialization for instant reaction
if "tts_content_box" not in st.session_state:
    st.session_state["tts_content_box"] = (
        "Chào các bạn đã quay trở lại với kênh Tốp Tốp của tôi! [hắng giọng] "
        "Hôm nay chúng ta sẽ cùng review một bộ phim cực kỳ kịch tính [cười]. "
        "Cái kết làm ai cũng ngỡ ngàng [thở dài]. Đừng quên bấm theo dõi nhé!"
    )


def insert_emotion_callback(tag: str):
    """Callback to instantly append emotion tag to the textarea state before rerender."""
    current_text = st.session_state.get("tts_content_box", "")
    st.session_state["tts_content_box"] = current_text.rstrip() + f" {tag} "


def apply_sample_callback():
    sample_key = st.session_state.get("sample_selector")
    if sample_key and sample_key in sample_texts:
        st.session_state["tts_content_box"] = sample_texts[sample_key]


sample_texts = {
    "🔥 Giọng Adam Tốp Tốp (Review phim/Meme)": (
        "Chào các bạn đã đến với kênh Tốp Tốp của tôi! [hắng giọng] "
        "Hôm nay chúng ta cùng xem một câu chuyện cực kỳ gay cấn [cười]. "
        "Cái kết làm ai cũng ngỡ ngàng [thở dài]."
    ),
    "Tiếng Việt (Kể chuyện/Tâm sự)": (
        "Đêm đó trời mưa rả rích ngoài hiên. [thở dài] "
        "Anh ấy nhìn tôi rồi mỉm cười nói: 'Đừng lo, mọi chuyện rồi sẽ qua thôi' [cười]."
    ),
    "English (Business)": (
        "Welcome to our AI Audio Studio! You can convert any text into lifelike speech with multiple natural voices."
    ),
}


with tab_tts:
    st.subheader("🎙️ Chuyển đổi Văn bản thành Giọng nói AI (Đa giọng đọc & Cảm xúc)")
    st.caption("Hỗ trợ giọng Adam Tốp Tốp, Hoài My, Nam Minh và các thẻ biểu cảm [cười], [thở dài], [hắng giọng] áp dụng tức thì.")

    col_tts_left, col_tts_right = st.columns([1.2, 0.8])

    with col_tts_left:
        st.markdown("##### 📝 1. Nhập văn bản cần đọc:")

        # Instant Emotion Tag Buttons using on_click callbacks
        st.markdown("**Bấm để chèn cảm xúc tức thì vào văn bản:**")
        col_emo_lbl, col_b1, col_b2, col_b3, _ = st.columns([1.1, 1.3, 1.4, 1.6, 2])

        with col_emo_lbl:
            st.markdown("<p style='padding-top: 6px; font-weight: bold;'>Cảm xúc:</p>", unsafe_allow_html=True)

        with col_b1:
            st.button(
                "😄 [cười]",
                key="btn_tag_cuoi",
                on_click=insert_emotion_callback,
                args=("[cười]",),
                help="Bấm để chèn tiếng cười tự nhiên",
            )

        with col_b2:
            st.button(
                "😮‍💨 [thở dài]",
                key="btn_tag_tho",
                on_click=insert_emotion_callback,
                args=("[thở dài]",),
                help="Bấm để chèn tiếng thở dài",
            )

        with col_b3:
            st.button(
                "🗣️ [hắng giọng]",
                key="btn_tag_hang",
                on_click=insert_emotion_callback,
                args=("[hắng giọng]",),
                help="Bấm để chèn tiếng e hèm lấy giọng",
            )

        col_sample, _ = st.columns([2, 1])
        with col_sample:
            st.selectbox(
                "Chèn nhanh văn bản mẫu:",
                options=["(Tùy chọn mẫu)"] + list(sample_texts.keys()),
                index=0,
                key="sample_selector",
                on_change=apply_sample_callback,
            )

        # The Text Area directly binded with session state
        st.text_area(
            "Nội dung văn bản:",
            key="tts_content_box",
            height=160,
            placeholder="Nhập đoạn văn bản bạn muốn chuyển đổi...",
        )

        uploaded_txt = st.file_uploader("Hoặc tải lên file văn bản (.txt):", type=["txt"], key="tts_txt_uploader")
        if uploaded_txt:
            uploaded_str = uploaded_txt.read().decode("utf-8")
            if uploaded_str != st.session_state["tts_content_box"]:
                st.session_state["tts_content_box"] = uploaded_str
                st.rerun()

    with col_tts_right:
        st.markdown("##### ⚙️ 2. Tùy chỉnh giọng & âm thanh:")

        tts_lang = st.selectbox(
            "Chọn ngôn ngữ:",
            options=list(LANGUAGE_NAMES.keys()),
            index=0,
            format_func=lambda code: LANGUAGE_NAMES.get(code, code),
            key="tts_lang_select",
        )

        available_voices = VOICES_CATALOG.get(tts_lang, VOICES_CATALOG["vi"])

        voice_mode = st.radio(
            "Chế độ giọng đọc:",
            options=["1 Giọng đọc cụ thể", "Đa giọng đọc (Tạo & So sánh nhiều giọng cùng lúc)"],
            horizontal=True,
        )

        if voice_mode == "1 Giọng đọc cụ thể":
            selected_voice_label = st.selectbox(
                "Chọn giọng đọc AI:",
                options=list(available_voices.keys()),
                index=0,  # Adam bựa
            )
            selected_voices = [available_voices[selected_voice_label]]
            selected_labels = [selected_voice_label]
        else:
            multi_selected_labels = st.multiselect(
                "Chọn các giọng đọc bạn muốn tạo cùng lúc:",
                options=list(available_voices.keys()),
                default=list(available_voices.keys())[:3],
            )
            selected_voices = [available_voices[lbl] for lbl in multi_selected_labels]
            selected_labels = multi_selected_labels

        st.markdown("**⚡ Tinh chỉnh tốc độ nói (Tempo):**")
        col_speed_preset1, col_speed_preset2, col_speed_preset3 = st.columns(3)
        with col_speed_preset1:
            if st.button("Bình thường (1.0x)", use_container_width=True):
                st.session_state["slider_speed_val"] = 0
                st.rerun()
        with col_speed_preset2:
            if st.button("🔥 Review Tốp Tốp (1.15x)", use_container_width=True, help="Tốc độ dồn dập chuẩn review phim"):
                st.session_state["slider_speed_val"] = 15
                st.rerun()
        with col_speed_preset3:
            if st.button("🚀 Nhanh (1.25x)", use_container_width=True):
                st.session_state["slider_speed_val"] = 25
                st.rerun()

        default_speed = st.session_state.get("slider_speed_val", 15)

        col_param1, col_param2 = st.columns(2)
        with col_param1:
            tts_rate_val = st.slider(
                "Tốc độ đọc (Speed / Rate):",
                min_value=-50,
                max_value=100,
                value=default_speed,
                step=5,
                format="%d%%",
                key="slider_speed_widget",
            )
            st.session_state["slider_speed_val"] = tts_rate_val

        with col_param2:
            tts_vol_val = st.slider("Âm lượng (Volume):", min_value=-50, max_value=50, value=0, step=5, format="%d%%")

        # Compute speed multiplier
        speed_factor = 1.0 + (tts_rate_val / 100.0)
        rate_str = f"{'+' if tts_rate_val >= 0 else ''}{tts_rate_val}%"
        vol_str = f"{'+' if tts_vol_val >= 0 else ''}{tts_vol_val}%"

        btn_generate_tts = st.button("🔊 Tạo Giọng Đọc AI Ngay", type="primary", use_container_width=True)

    # Output Section for TTS
    st.divider()
    st.markdown("##### 🎧 3. Kết quả âm thanh:")

    if btn_generate_tts:
        text_to_speak = st.session_state["tts_content_box"].strip()
        if not text_to_speak:
            st.warning("⚠️ Vui lòng nhập văn bản trước khi tạo âm thanh!")
        elif not selected_voices:
            st.warning("⚠️ Vui lòng chọn ít nhất một giọng đọc!")
        else:
            tts_output_dir = Path("./output/tts")
            tts_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            with st.spinner("Đang tổng hợp giọng nói AI..."):
                results = []
                for voice_id, label in zip(selected_voices, selected_labels):
                    try:
                        if voice_id.startswith("vieneu:"):
                            # VieNeu-TTS Engine (Supports [cười], [thở dài], [hắng giọng] + speed multiplier)
                            clean_v = voice_id.replace("vieneu:", "")
                            out_filename = f"tts_vieneu_{clean_v}_{timestamp}.mp3"
                            out_path = tts_output_dir / out_filename
                            generate_vieneu_speech(
                                text=text_to_speak,
                                voice=clean_v,
                                speed=speed_factor,
                                output_path=out_path,
                            )
                        else:
                            # Edge-TTS Engine (strips emotion tags cleanly)
                            clean_text_for_edge = text_to_speak
                            for emo_tag in ["[cười]", "[thở dài]", "[hắng giọng]", "[chuckle]", "[sigh]", "[clear throat]"]:
                                clean_text_for_edge = clean_text_for_edge.replace(emo_tag, "")

                            out_filename = f"tts_edge_{voice_id}_{timestamp}.mp3"
                            out_path = tts_output_dir / out_filename
                            asyncio.run(
                                generate_single_tts_edge(
                                    text=clean_text_for_edge,
                                    voice=voice_id,
                                    rate=rate_str,
                                    volume=vol_str,
                                    pitch="+0Hz",
                                    output_path=out_path,
                                )
                            )
                        results.append((label, voice_id, out_path))
                    except Exception as err:
                        st.error(f"Lỗi khi tạo giọng {label}: {err}")

            if results:
                st.success(f"🎉 Đã tạo thành công {len(results)} bản thu âm giọng đọc!")

                if len(results) == 1:
                    lbl, vid, file_p = results[0]
                    st.markdown(f"**Giọng đọc:** `{lbl}` | **Tốc độ:** `{speed_factor:.2f}x`")
                    st.audio(str(file_p), format="audio/mp3")
                    with open(file_p, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Tải file âm thanh ({file_p.name})",
                            data=f,
                            file_name=file_p.name,
                            mime="audio/mpeg",
                        )
                else:
                    cols_grid = st.columns(min(len(results), 2))
                    for idx, (lbl, vid, file_p) in enumerate(results):
                        with cols_grid[idx % 2]:
                            st.info(f"🎙️ **{lbl}** ({speed_factor:.2f}x)")
                            st.audio(str(file_p), format="audio/mp3")
                            with open(file_p, "rb") as f:
                                st.download_button(
                                    label=f"⬇️ Tải MP3 ({file_p.stem})",
                                    data=f,
                                    file_name=file_p.name,
                                    mime="audio/mpeg",
                                    key=f"dl_{idx}_{vid}",
                                )
