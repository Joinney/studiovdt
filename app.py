"""
AI Studio: Video Dubbing & Multi-Voice Text-to-Speech (Edge-TTS + VieNeu-TTS with 50+ Rich Emotion FX)
Run with: streamlit run app.py
"""
import asyncio
from datetime import datetime
from pathlib import Path
import streamlit as st
import edge_tts

from config import DEFAULT_VOICES, LANGUAGE_NAMES, VOICES_CATALOG, DubbingConfig
from video_dubber.pipeline import VideoDubberPipeline
from video_dubber.vieneu_tts import generate_vieneu_speech, EMOTION_SOUND_MAP

st.set_page_config(
    page_title="AI Dubbing & TTS Studio",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ AI Audio & Video Studio")
st.caption("Lồng tiếng video tự động & Chuyển đổi văn bản thành giọng nói (Hỗ trợ kho 50+ Thẻ cảm xúc & Giọng Adam Tốp Tốp)")

tab_dubbing, tab_tts = st.tabs([
    "🎬 Lồng tiếng Video (Video Dubbing)",
    "🎙️ Văn bản sang Âm thanh (Text to Speech - Đa giọng đọc & 50+ Cảm xúc)",
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
# TAB 2: TEXT-TO-SPEECH (TTS STUDIO WITH 50+ RICH EMOTION CUES)
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
        "Khoan đã... [clears throat] các bạn có biết chuyện gì vừa xảy ra không? "
        "Tên sát thủ tưởng như đã trốn thoát [laughing], nhưng [pause] hắn không hề biết rằng [shocked] "
        "toàn bộ căn phòng đã bị bao vây [sighs]. [panicked] Chuyện này kết thúc thế nào đây?!"
    )


def insert_emotion_callback(tag: str):
    """Callback to instantly append emotion tag to the textarea state."""
    current_text = st.session_state.get("tts_content_box", "")
    st.session_state["tts_content_box"] = current_text.rstrip() + f" {tag} "


def apply_sample_callback():
    sample_key = st.session_state.get("sample_selector")
    if sample_key and sample_key in sample_texts:
        st.session_state["tts_content_box"] = sample_texts[sample_key]


sample_texts = {
    "🔥 Giọng Adam Review phim (Kết hợp đa cảm xúc)": (
        "Khoan đã... [clears throat] các bạn có biết chuyện gì vừa xảy ra không? "
        "Hắn nghĩ mình đã an toàn [laughing], nhưng [thinking] bất ngờ thay [shocked] "
        "cánh cửa mở toang [panicked]! [sighs] Mọi chuyện coi như chấm hết."
    ),
    "😭 Cảnh xúc động / Buồn bã": (
        "Đừng đi mà... [crying] Em biết em sai rồi [apologetic]. [groans] "
        "Tại sao mọi chuyện lại ra nông nỗi này? [sad] Anh hãy ở lại đi mà [pleading]!"
    ),
    "😂 Hài hước / Meme TikTok": (
        "Trời ơi là trời [frustrated]! [coughs] Tôi vừa thấy cái gì thế này? [awkward laugh] "
        "Tưởng thế nào, hóa ra là như thế [snickers]! [smug] Biết ngay mà!"
    ),
    "😱 Giật gân / Kinh dị": (
        "Trong bóng tối tĩnh mịch... [whispering] Có tiếng bước chân lại gần [gasps]. "
        "Cái bóng đen đó là ai [screaming]?! [panicked] Chạy mau lên!"
    ),
}

# Grouped emotions for selectbox
ALL_EMOTIONS_CATALOG = {
    "🎭 Cười & Vui vẻ": [
        ("[cười]", "[cười] - Tiếng cười nhẹ"),
        ("[laughing]", "[laughing] - Cười to (hahaha)"),
        ("[chuckles]", "[chuckles] - Cười khúc khích (he he he)"),
        ("[giggles]", "[giggles] - Cười rúc rích (hí hí hí)"),
        ("[snickers]", "[snickers] - Cười khẩy (khì khì)"),
        ("[awkward laugh]", "[awkward laugh] - Cười gượng (hơ hơ hơ)"),
        ("[happy]", "[happy] - Vui sướng (vui quá)"),
        ("[cheering]", "[cheering] - Reo hò (yeahhhh)"),
        ("[celebrating]", "[celebrating] - Ăn mừng (yooooo)"),
    ],
    "😮‍💨 Thở dài & Phản xạ cơ thể": [
        ("[sighs]", "[sighs] - Thở dài (haizzz)"),
        ("[clears throat]", "[clears throat] - Hắng giọng (hèm hèm)"),
        ("[coughs]", "[coughs] - Ho (khụ khụ)"),
        ("[sneezes]", "[sneezes] - Hắt xì (ách xì)"),
        ("[yawns]", "[yawns] - Ngáp (ngáppp)"),
        ("[lip smacks]", "[lip smacks] - Chẹp miệng (chẹp chẹp)"),
        ("[relieved]", "[relieved] - Thở phào nhẹ nhõm (phùuu)"),
        ("[gasps]", "[gasps] - Thở gấp / hụt hơi (hự)"),
        ("[grunts]", "[grunts] - Gắng sức (hự! Cố lên)"),
    ],
    "😱 Bất ngờ, Sốc & Kịch tính": [
        ("[shocked]", "[shocked] - Sốc kinh hoàng (trời ơi!)"),
        ("[surprised]", "[surprised] - Ngạc nhiên (á há)"),
        ("[amazed]", "[amazed] - Kinh ngạc (ôi wow)"),
        ("[excited gasp]", "[excited gasp] - Thốt lên (ôiiii không)"),
        ("[panicked]", "[panicked] - Hoảng loạn (chết chết chết!)"),
        ("[screaming]", "[screaming] - Hét thất thanh (áaaaa)"),
        ("[shouting]", "[shouting] - Hét vang (gôôôôô)"),
        ("[yelling]", "[yelling] - Gọi lớn (Êeeee)"),
    ],
    "😢 Buồn bã & Khóc lóc": [
        ("[crying]", "[crying] - Khóc nức nở (hu hu)"),
        ("[sad]", "[sad] - Buồn bã (buồn ghê)"),
        ("[disappointed]", "[disappointed] - Thất vọng (ôi thôi rồi)"),
        ("[groans]", "[groans] - Than vãn (ôi trời ơi...)"),
        ("[worried]", "[worried] - Lo lắng (chết rồi)"),
        ("[apologetic]", "[apologetic] - Xin lỗi (anh xin lỗi nhé)"),
        ("[pleading]", "[pleading] - Năn nỉ (làm ơn đi)"),
    ],
    "😡 Tức giận & Khó chịu": [
        ("[angry]", "[angry] - Tức giận (tức quá)"),
        ("[annoyed]", "[annoyed] - Bực dọc (chậc)"),
        ("[frustrated]", "[frustrated] - Bực bội (trời đất ơi)"),
        ("[embarrassed]", "[embarrassed] - Ngượng ngùng (ôi ngại quá)"),
    ],
    "🤔 Thái độ, Suy nghĩ & Diễn đạt": [
        ("[thinking]", "[thinking] - Đang suy nghĩ (hmmm)"),
        ("[hesitant]", "[hesitant] - Do dự (ừm...)"),
        ("[smug]", "[smug] - Đắc ý (biết ngay mà)"),
        ("[sarcastic]", "[sarcastic] - Mỉa mai (ghê chưa)"),
        ("[curious]", "[curious] - Tò mò (ủa?)"),
        ("[confused]", "[confused] - Bối rối (hả?)"),
        ("[doubtful]", "[doubtful] - Nghi ngờ (thật không vậy?)"),
        ("[whispering]", "[whispering] - Thì thầm (psst...)"),
        ("[affirmative]", "[affirmative] - Khẳng định (ừ hứ)"),
        ("[realization]", "[realization] - Nhận ra (ôooo)"),
        ("[agreeing]", "[agreeing] - Đồng tình (đúng rồi)"),
        ("[disagreeing]", "[disagreeing] - Phản đối (không đâu)"),
        ("[teasing]", "[teasing] - Trêu chọc (ê nhaaa)"),
        ("[proud]", "[proud] - Tự hào (tuyệt vời)"),
        ("[confident]", "[confident] - Tự tin (chắc chắn luôn)"),
        ("[determined]", "[determined] - Quyết tâm (nhất định rồi)"),
        ("[applause]", "[applause] - Vỗ tay (bốp bốp bốp)"),
    ],
}


with tab_tts:
    st.subheader("🎙️ Chuyển đổi Văn bản thành Giọng nói AI (Đa giọng đọc & 50+ Thẻ Cảm Xúc)")
    st.caption("Kho cảm xúc đầy đủ 50+ thẻ âm thanh: [crying], [sighs], [clears throat], [laughing], [panicked], [shocked]...")

    col_tts_left, col_tts_right = st.columns([1.2, 0.8])

    with col_tts_left:
        st.markdown("##### 📝 1. Nhập văn bản & Thêm cảm xúc:")

        # Quick common buttons row 1
        st.markdown("**⚡ Chèn nhanh các cảm xúc phổ biến:**")
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns(6)
        with r1_c1:
            st.button("😄 [cười]", on_click=insert_emotion_callback, args=("[cười]",), use_container_width=True)
        with r1_c2:
            st.button("😮‍💨 [sighs]", on_click=insert_emotion_callback, args=("[sighs]",), use_container_width=True)
        with r1_c3:
            st.button("🗣️ [hắng giọng]", on_click=insert_emotion_callback, args=("[clears throat]",), use_container_width=True)
        with r1_c4:
            st.button("😭 [crying]", on_click=insert_emotion_callback, args=("[crying]",), use_container_width=True)
        with r1_c5:
            st.button("😱 [shocked]", on_click=insert_emotion_callback, args=("[shocked]",), use_container_width=True)
        with r1_c6:
            st.button("😡 [angry]", on_click=insert_emotion_callback, args=("[angry]",), use_container_width=True)

        # Quick common buttons row 2
        r2_c1, r2_c2, r2_c3, r2_c4, r2_c5, r2_c6 = st.columns(6)
        with r2_c1:
            st.button("😂 [laughing]", on_click=insert_emotion_callback, args=("[laughing]",), use_container_width=True)
        with r2_c2:
            st.button("🤔 [thinking]", on_click=insert_emotion_callback, args=("[thinking]",), use_container_width=True)
        with r2_c3:
            st.button("🏃 [panicked]", on_click=insert_emotion_callback, args=("[panicked]",), use_container_width=True)
        with r2_c4:
            st.button("🤧 [sneezes]", on_click=insert_emotion_callback, args=("[sneezes]",), use_container_width=True)
        with r2_c5:
            st.button("🥱 [yawns]", on_click=insert_emotion_callback, args=("[yawns]",), use_container_width=True)
        with r2_c6:
            st.button("😏 [smug]", on_click=insert_emotion_callback, args=("[smug]",), use_container_width=True)

        # Full Emotion Catalog Dropdown Picker
        with st.expander("📚 Mở Kho 50+ Thẻ Cảm Xúc Mở Rộng", expanded=False):
            col_grp, col_item, col_add = st.columns([1.2, 2, 0.8])
            with col_grp:
                selected_group = st.selectbox("Chọn nhóm:", options=list(ALL_EMOTIONS_CATALOG.keys()))
            with col_item:
                items_in_grp = ALL_EMOTIONS_CATALOG[selected_group]
                selected_item_tag = st.selectbox(
                    "Chọn cảm xúc cụ thể:",
                    options=[t[0] for t in items_in_grp],
                    format_func=lambda x: dict(items_in_grp).get(x, x),
                )
            with col_add:
                st.write("")
                st.write("")
                st.button(
                    "➕ Chèn thẻ",
                    on_click=insert_emotion_callback,
                    args=(selected_item_tag,),
                    use_container_width=True,
                )

        col_sample, _ = st.columns([2, 1])
        with col_sample:
            st.selectbox(
                "Chèn nhanh văn bản mẫu diễn xuất:",
                options=["(Tùy chọn mẫu)"] + list(sample_texts.keys()),
                index=0,
                key="sample_selector",
                on_change=apply_sample_callback,
            )

        # The Text Area directly binded with session state
        st.text_area(
            "Nội dung văn bản (hỗ trợ nhập bất kỳ thẻ nào trong bảng 50+ cảm xúc):",
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
                            # VieNeu-TTS Engine (Supports full 50+ emotion cues + speed multiplier)
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
                            # Edge-TTS Engine (cleanly converts emotion tags to text or removes them)
                            clean_text_for_edge = text_to_speak
                            for emo_tag in EMOTION_SOUND_MAP.keys():
                                clean_text_for_edge = clean_text_for_edge.replace(f"[{emo_tag}]", "")

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
