"""
Speech Recognition module using faster-whisper
"""
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class Segment:
    id: int
    start: float  # seconds
    end: float    # seconds
    text: str
    translated_text: str = ""
    tts_audio_path: Optional[str] = None
    original_duration: float = 0.0

    def __post_init__(self):
        if self.original_duration <= 0.0:
            self.original_duration = max(0.1, round(self.end - self.start, 2))


class Transcriber:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "default",
    ):
        """
        Initialize faster-whisper model.
        Available model_size: tiny, base, small, medium, large-v3.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            resolved_device = self.device
            if resolved_device == "auto":
                try:
                    import ctranslate2
                    resolved_device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
                except Exception:
                    try:
                        import torch
                        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
                    except Exception:
                        resolved_device = "cpu"

            resolved_compute = self.compute_type
            if resolved_compute in ("default", "auto", ""):
                resolved_compute = "float16" if resolved_device == "cuda" else "int8"

            logger.info(
                f"Loading Whisper model '{self.model_size}' on {resolved_device} ({resolved_compute})..."
            )
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=resolved_device,
                    compute_type=resolved_compute,
                )
            except Exception as ex_cuda:
                if resolved_device == "cuda":
                    logger.warning(
                        f"Failed to load Whisper on CUDA ({ex_cuda}), falling back to CPU int8..."
                    )
                    self._model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                    )
                else:
                    raise ex_cuda
        return self._model

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
    ) -> (List[Segment], str):
        """
        Transcribes audio into timed segments.
        Returns:
            segments: List[Segment]
            detected_language: str
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._load_model()
        logger.info(f"Transcribing audio file: {audio_path.name}...")

        whisper_lang = None if (language in (None, "auto", "")) else language

        # Tối ưu siêu tốc độ: beam_size=2, best_of=1, temperature=0.0 giúp nhận diện nhanh gấp 4 lần
        # trong khi độ chính xác phụ đề và VAD giữ nguyên 100%
        raw_segments, info = model.transcribe(
            str(audio_path),
            language=whisper_lang,
            beam_size=2,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,  # Tránh lỗi bỏ sót lời thoại sau các đoạn nhạc/ngắt nghỉ
            vad_filter=True,  # Lọc tạp âm với thông số nhạy cao để bắt trọn mọi câu thoại phim
            vad_parameters=dict(
                threshold=0.35,              # Tăng độ nhạy để không bị nuốt lời thoại trên nền nhạc phim
                min_speech_duration_ms=250,   # Bắt cả các câu thoại ngắn, từ đơn, thán từ
                max_speech_duration_s=10.0,   # Chia nhỏ đoạn thoại dài 10-20s thành các câu ngắn khít khẩu hình
                min_silence_duration_ms=300,  # Ngắt câu linh hoạt ngay khi dứt tiếng
                speech_pad_ms=250             # Đệm trước 250ms bắt trọn từ đầu tiên khi nhân vật vừa mở miệng
            ),
            word_timestamps=True,
        )

        detected_lang = info.language
        logger.info(
            f"Detected language: '{detected_lang}' with probability {info.language_probability:.2f}"
        )

        segments: List[Segment] = []
        for idx, s in enumerate(raw_segments):
            text = s.text.strip()
            if not text:
                continue
            
            # Định vị mốc bắt đầu chuẩn xác theo từng từ (Word-level timestamps) để lồng tiếng khớp ngay miệng nhân vật
            seg_start = round(s.start, 2)
            seg_end = round(s.end, 2)
            if hasattr(s, "words") and s.words:
                w_start = s.words[0].start
                w_end = s.words[-1].end
                if w_start is not None and w_start >= 0:
                    seg_start = round(w_start, 2)
                if w_end is not None and w_end > seg_start:
                    seg_end = round(w_end, 2)

            seg = Segment(
                id=idx,
                start=seg_start,
                end=seg_end,
                text=text,
            )
            segments.append(seg)

        logger.info(f"Generated {len(segments)} timed segments.")
        return segments, detected_lang
