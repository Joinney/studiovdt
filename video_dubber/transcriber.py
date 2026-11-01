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
                    resolved_device = "cpu"

            resolved_compute = self.compute_type
            if resolved_compute == "default":
                resolved_compute = "float16" if resolved_device == "cuda" else "int8"

            logger.info(
                f"Loading Whisper model '{self.model_size}' on {resolved_device} ({resolved_compute})..."
            )
            self._model = WhisperModel(
                self.model_size,
                device=resolved_device,
                compute_type=resolved_compute,
            )
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

        raw_segments, info = model.transcribe(
            str(audio_path),
            language=whisper_lang,
            beam_size=5,
            vad_filter=True,  # Filter out silence/noise
            vad_parameters=dict(min_silence_duration_ms=500),
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
            seg = Segment(
                id=idx,
                start=round(s.start, 2),
                end=round(s.end, 2),
                text=text,
            )
            segments.append(seg)

        logger.info(f"Generated {len(segments)} timed segments.")
        return segments, detected_lang
