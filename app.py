"""
AI Studio: Video Dubbing & Multi-Voice Text-to-Speech (Edge-TTS + VieNeu-TTS with Emotion Tags)
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
st.caption("Lồng tiếng video tự động & Chuyển đổi văn bản thành giọng nói (Hỗ trợ giọng Adam Tốp Tốp & Thẻ cảm xúc [cười], [thở dài], [hắng giọng])")

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
# TAB 2: TEXT-TO-SPEECH (TTS STUDIO WITH EMOTIONS)
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


with tab_tts:
    st.subheader("🎙️ Chuyển đổi Văn bản thành Giọng nói AI (Đa giọng đọc & Cảm xúc)")
    st.caption("Hỗ trợ giọng Adam Tốp Tốp, Hoài My, Nam Minh và các thẻ biểu cảm [cười], [thở dài], [hắng giọng].")

    # Initialize session state for text input if not present
    if "tts_editor_text" not in st.session_state:
        st.session_state["tts_editor_text"] = (
            "Chào các bạn đã quay trở lại với kênh Tốp Tốp của tôi! [hắng giọng] "
            "Hôm nay chúng ta sẽ cùng review một bộ phim cực kỳ kịch tính [cười]. "
            "Các bạn sẵn sàng chưa nào? [thở dài] Đừng quên bấm theo dõi nhé!"
        )

    col_tts_left, col_tts_right = st.columns([1.2, 0.8])

    with col_tts_left:
        st.markdown("##### 📝 1. Nhập văn bản cần đọc:")

        # Quick emotion buttons (Exactly as requested)
        st.markdown(
            """
            <style>
            div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
                padding: 0.25rem 0.75rem;
                border-radius: 8px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col_emo_lbl, col_btn_cuoi, col_btn_tho, col_btn_hang, _ = st.columns([1.1, 1.2, 1.4, 1.6, 2])

        with col_emo_lbl:
            st.markdown("<p style='padding-top: 8px; font-weight: bold;'>Cảm xúc:</p>", unsafe_allow_html=True)

        with col_btn_cuoi:
            if st.button("😄 Cười", key="btn_emo_cuoi", help="Chèn thẻ [cười] - tạo tiếng cười tự nhiên"):
                st.session_state["tts_editor_text"] = st.session_state["tts_editor_text"].rstrip() + " [cười] "
                st.rerun()

        with col_btn_tho:
            if st.button("😮‍💨 Thở dài", key="btn_emo_tho", help="Chèn thẻ [thở dài] - tạo tiếng thở dài trầm ngâm"):
                st.session_state["tts_editor_text"] = st.session_state["tts_editor_text"].rstrip() + " [thở dài] "
                st.rerun()

        with col_btn_hang:
            if st.button("🗣️ Hắng giọng", key="btn_emo_hang", help="Chèn thẻ [hắng giọng] - tạo tiếng e hèm lấy giọng"):
                st.session_state["tts_editor_text"] = st.session_state["tts_editor_text"].rstrip() + " [hắng giọng] "
                st.rerun()

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

        col_sample, _ = st.columns([2, 1])
        with col_sample:
            chosen_sample = st.selectbox(
                "Chèn nhanh văn bản mẫu:",
                options=["(Tùy chọn mẫu)"] + list(sample_texts.keys()),
                index=0,
            )
            if chosen_sample != "(Tùy chọn mẫu)":
                if st.session_state.get("last_sample") != chosen_sample:
                    st.session_state["tts_editor_text"] = sample_texts[chosen_sample]
                    st.session_state["last_sample"] = chosen_sample
                    st.rerun()

        tts_input_text = st.text_area(
            "Nội dung văn bản (có thể bấm các nút Cảm xúc ở trên để chèn trực tiếp):",
            value=st.session_state["tts_editor_text"],
            height=160,
            key="tts_text_area",
            placeholder="Nhập đoạn văn bản bạn muốn chuyển đổi...",
        )
        # Keep session state in sync when user edits directly
        st.session_state["tts_editor_text"] = tts_input_text

        uploaded_txt = st.file_uploader("Hoặc tải lên file văn bản (.txt):", type=["txt"], key="tts_txt_uploader")
        if uploaded_txt:
            uploaded_content = uploaded_txt.read().decode("utf-8")
            st.session_state["tts_editor_text"] = uploaded_content
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
                index=0,
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

        col_param1, col_param2, col_param3 = st.columns(3)
        with col_param1:
            tts_rate_val = st.slider("Tốc độ (Speed):", min_value=-50, max_value=100, value=0, step=5, format="%d%%")
        with col_param2:
            tts_pitch_val = st.slider("Cao độ (Pitch):", min_value=-50, max_value=50, value=0, step=5, format="%dHz")
        with col_param3:
            tts_vol_val = st.slider("Âm lượng (Volume):", min_value=-50, max_value=50, value=0, step=5, format="%d%%")

        rate_str = f"{'+' if tts_rate_val >= 0 else ''}{tts_rate_val}%"
        pitch_str = f"{'+' if tts_pitch_val >= 0 else ''}{tts_pitch_val}Hz"
        vol_str = f"{'+' if tts_vol_val >= 0 else ''}{tts_vol_val}%"

        btn_generate_tts = st.button("🔊 Tạo Giọng Đọc AI Ngay", type="primary", use_container_width=True)

    # Output Section for TTS
    st.divider()
    st.markdown("##### 🎧 3. Kết quả âm thanh:")

    if btn_generate_tts:
        text_to_speak = st.session_state["tts_editor_text"].strip()
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
                            # VieNeu-TTS Engine (Supports [cười], [thở dài], [hắng giọng])
                            clean_v = voice_id.replace("vieneu:", "")
                            out_filename = f"tts_vieneu_{clean_v}_{timestamp}.mp3"
                            out_path = tts_output_dir / out_filename
                            generate_vieneu_speech(
                                text=text_to_speak,
                                voice=clean_v,
                                output_path=out_path,
                            )
                        else:
                            # Edge-TTS Engine (strips emotion tags cleanly so they are not read literally)
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
                                    pitch=pitch_str,
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
                    st.markdown(f"**Giọng đọc:** `{lbl}`")
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
                            st.info(f"🎙️ **{lbl}**")
                            st.audio(str(file_p), format="audio/mp3")
                            with open(file_p, "rb") as f:
                                st.download_button(
                                    label=f"⬇️ Tải MP3 ({file_p.stem})",
                                    data=f,
                                    file_name=file_p.name,
                                    mime="audio/mpeg",
                                    key=f"dl_{idx}_{vid}",
                                )
