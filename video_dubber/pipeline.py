"""
Complete End-to-End Video Dubbing Pipeline
"""
import json
import logging
from pathlib import Path
from typing import Callable, Optional, Union

from config import DubbingConfig
from .extractor import extract_audio
from .transcriber import Transcriber, Segment
from .translator import Translator
from .tts import TTSService
from .synchronizer import AudioSynchronizer
from .merger import VideoMerger

logger = logging.getLogger(__name__)


def format_srt_time(seconds: float) -> str:
    millis = int((seconds % 1) * 1000)
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    secs = secs % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def export_srt(segments: list, srt_path: Path, use_translated: bool = True):
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            text = seg.translated_text if (use_translated and seg.translated_text) else seg.text
            start = format_srt_time(seg.start)
            end = format_srt_time(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")


class VideoDubberPipeline:
    def __init__(self, config: Optional[DubbingConfig] = None):
        self.config = config or DubbingConfig()
        self.transcriber = Transcriber(
            model_size=self.config.whisper_model,
            device=self.config.device,
            compute_type=self.config.compute_type,
        )
        self.translator = Translator(
            target_lang=self.config.target_language,
            source_lang=self.config.source_language,
        )
        self.tts = TTSService(
            voice=self.config.tts_voice,
            rate=self.config.tts_rate,
            volume=self.config.tts_volume,
        )
        self.synchronizer = AudioSynchronizer(
            max_speed_factor=self.config.max_speed_factor,
            min_speed_factor=self.config.min_speed_factor,
        )
        self.merger = VideoMerger(
            original_audio_volume=self.config.original_audio_volume
        )

    def process(
        self,
        video_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Path:
        """
        Executes complete dubbing workflow from input video to output video.
        progress_callback(status_message, progress_fraction [0.0 - 1.0])
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Input video not found: {video_path}")

        def notify(msg: str, progress: float):
            logger.info(f"[{int(progress*100)}%] {msg}")
            if progress_callback:
                progress_callback(msg, progress)

        stem = video_path.stem
        work_dir = self.config.temp_dir / stem
        work_dir.mkdir(parents=True, exist_ok=True)

        if output_path is None:
            output_path = self.config.output_dir / f"{stem}_dubbed_{self.config.target_language}.mp4"
        else:
            output_path = Path(output_path)

        # Step 1: Extract Audio
        notify("Trích xuất âm thanh từ video gốc...", 0.10)
        orig_audio_path = work_dir / "original_audio.wav"
        extract_audio(video_path, orig_audio_path)

        # Get total video duration
        from pydub import AudioSegment
        full_audio = AudioSegment.from_file(orig_audio_path)
        total_duration = len(full_audio) / 1000.0

        # Step 2: Speech Recognition (Transcription)
        notify("Nhận diện giọng nói và tách mốc thời gian (Whisper ASR)...", 0.25)
        segments, detected_lang = self.transcriber.transcribe(
            orig_audio_path,
            language=None if self.config.source_language == "auto" else self.config.source_language,
        )

        if not segments:
            raise ValueError("Không nhận diện được giọng nói nào trong video!")

        # Step 3: Translation
        notify(f"Dịch nội dung sang ngôn ngữ đích ({self.config.target_language})...", 0.45)
        self.translator.source_lang = detected_lang
        segments = self.translator.translate_segments(segments)

        # Save metadata and subtitle
        srt_path = output_path.with_suffix(".srt")
        export_srt(segments, srt_path, use_translated=True)
        json_path = work_dir / "segments.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([seg.__dict__ for seg in segments], f, ensure_ascii=False, indent=2)

        # Step 4: TTS Generation
        notify("Sinh giọng đọc AI lồng tiếng mới (Edge-TTS)...", 0.65)
        tts_dir = work_dir / "tts_segments"
        segments = self.tts.generate_speech(segments, tts_dir)

        # Step 5: Audio Synchronization
        notify("Đồng bộ thời gian và khớp khẩu hình âm thanh...", 0.80)
        dubbed_voice_path = work_dir / "dubbed_assembled.wav"
        self.synchronizer.align_and_assemble(
            segments=segments,
            total_duration_seconds=total_duration,
            output_file=dubbed_voice_path,
        )

        # Step 6: Audio Mixing & Video Merging
        notify("Hòa âm nhạc nền và ghép video lồng tiếng hoàn thiện...", 0.90)
        mixed_audio_path = work_dir / "mixed_final.wav"
        self.merger.mix_audios(
            original_audio_path=orig_audio_path,
            dubbed_audio_path=dubbed_voice_path,
            output_mixed_audio_path=mixed_audio_path,
        )

        final_video = self.merger.merge_video(
            video_path=video_path,
            audio_path=mixed_audio_path,
            output_video_path=output_path,
        )

        notify("Hoàn thành lồng tiếng video!", 1.0)
        return final_video
