"""
Audio Synchronization and Time-Stretching Module
Aligns generated speech with the original speech timestamps.
"""
import logging
from pathlib import Path
from typing import List, Union
from pydub import AudioSegment
from .transcriber import Segment

logger = logging.getLogger(__name__)


def change_audio_speed(sound: AudioSegment, speed: float = 1.0) -> AudioSegment:
    """
    Adjust audio speed (tempo) cleanly without altering pitch or timbre.
    Strictly preserves the actor's natural voice pitch, brightness, and character timbre.
    NEVER slows down speech or drops pitch (eliminates deep/muffled 'giọng trầm').
    """
    if speed <= 1.03:
        # Keep 100% natural speed and pitch
        return sound

    # Speed up cleanly using pitch-preserving time stretch
    from pydub.effects import speedup
    try:
        # chunk_size=50ms and crossfade=25ms minimizes phase artifacts and avoids double-voice
        return speedup(sound, playback_speed=speed, chunk_size=50, crossfade=25)
    except Exception as e:
        logger.warning(f"Speedup note: {e}, keeping natural cadence")
        return sound


class AudioSynchronizer:
    def __init__(
        self,
        max_speed_factor: float = 1.35,
        min_speed_factor: float = 1.0,
    ):
        self.max_speed_factor = max(1.05, min(2.0, max_speed_factor))
        self.min_speed_factor = 1.0  # Luôn giữ tối thiểu 1.0x, tuyệt đối không kéo chậm làm tụt tông/trầm giọng

    def align_and_assemble(
        self,
        segments: List[Segment],
        total_duration_seconds: float,
        output_file: Union[str, Path],
    ) -> Path:
        """
        Assembles synchronous voice track with 100% authentic character timbre and bright tone.
        Guarantees that voices speak at natural cadence without pitch-drop or sluggish drag.
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        total_duration_ms = int(total_duration_seconds * 1000)
        master_track = AudioSegment.silent(duration=total_duration_ms)

        logger.info(
            f"Assembling audio track for {len(segments)} segments (total length: {total_duration_seconds:.2f}s)..."
        )

        for idx, seg in enumerate(segments):
            if not seg.tts_audio_path or not Path(seg.tts_audio_path).exists():
                continue

            try:
                clip = AudioSegment.from_file(seg.tts_audio_path)
            except Exception as e:
                logger.warning(f"Could not read audio clip {seg.tts_audio_path}: {e}")
                continue

            # Mốc bắt đầu của câu thoại kế tiếp để tránh đè tiếng
            if idx + 1 < len(segments):
                next_start = segments[idx + 1].start
            else:
                next_start = total_duration_seconds

            available_window_s = max(0.3, next_start - seg.start - 0.08)
            clip_len_s = len(clip) / 1000.0

            # Chỉ tăng tốc nhẹ nếu câu đọc dài hơn khoảng trống tới câu tiếp theo
            # Tuyệt đối KHÔNG bao giờ kéo chậm (slowing down) làm trầm giọng, méo tiếng
            if clip_len_s > available_window_s:
                needed_speed = clip_len_s / available_window_s
                target_speed = min(needed_speed, self.max_speed_factor)
                adjusted_clip = change_audio_speed(clip, speed=target_speed)
                max_allowed_len = int((available_window_s + 0.05) * 1000)
                if len(adjusted_clip) > max_allowed_len:
                    adjusted_clip = adjusted_clip[:max_allowed_len]
            else:
                # Giữ nguyên 100% giọng chuẩn phòng thu tự nhiên, trong sáng của nhân vật
                adjusted_clip = clip

            # Mốc kết thúc phụ đề chuẩn xác: Đúng thời điểm giọng đọc dứt câu là phụ đề ẩn đi ngay lập tức
            actual_spoken_len_s = round(len(adjusted_clip) / 1000.0, 3)
            seg.sub_end = round(seg.start + actual_spoken_len_s, 3)
            if seg.sub_end > next_start:
                seg.sub_end = next_start

            start_pos_ms = int(seg.start * 1000)
            master_track = master_track.overlay(adjusted_clip, position=start_pos_ms)

        # Đảm bảo phụ đề câu trước không chồng lấn vào mốc bắt đầu của câu sau
        for i in range(len(segments) - 1):
            if hasattr(segments[i], "sub_end") and segments[i].sub_end > segments[i + 1].start:
                segments[i].sub_end = segments[i + 1].start

        master_track.export(str(output_file), format="wav")
        logger.info(f"Synchronized audio track exported to: {output_file}")
        return output_file
