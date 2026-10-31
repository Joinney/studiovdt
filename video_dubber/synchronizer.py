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
    Adjust audio speed (tempo) without changing pitch using pydub.effects.speedup.
    speed > 1.0: faster
    speed < 1.0: slower
    """
    if abs(speed - 1.0) < 0.05:
        return sound

    if speed > 1.0:
        # Pydub speedup requires speed >= 1.0
        from pydub.effects import speedup
        # speedup parameter: playback_speed
        try:
            return speedup(sound, playback_speed=speed)
        except Exception as e:
            logger.warning(f"Speedup effect failed: {e}, using frame_rate fallback")
            # fallback: change frame rate
            new_frame_rate = int(sound.frame_rate * speed)
            return sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(sound.frame_rate)
    else:
        # Slow down by altering frame rate
        new_frame_rate = int(sound.frame_rate * speed)
        return sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate}).set_frame_rate(sound.frame_rate)


class AudioSynchronizer:
    def __init__(
        self,
        max_speed_factor: float = 1.35,
        min_speed_factor: float = 0.8,
    ):
        self.max_speed_factor = max_speed_factor
        self.min_speed_factor = min_speed_factor

    def align_and_assemble(
        self,
        segments: List[Segment],
        total_duration_seconds: float,
        output_file: Union[str, Path],
    ) -> Path:
        """
        Creates a complete synchronous audio track matching the duration of the original video.
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        total_duration_ms = int(total_duration_seconds * 1000)
        # Create a blank silence canvas for the entire video duration
        master_track = AudioSegment.silent(duration=total_duration_ms)

        logger.info(
            f"Assembling audio track for {len(segments)} segments (total length: {total_duration_seconds:.2f}s)..."
        )

        for seg in segments:
            if not seg.tts_audio_path or not Path(seg.tts_audio_path).exists():
                continue

            try:
                clip = AudioSegment.from_file(seg.tts_audio_path)
            except Exception as e:
                logger.warning(f"Could not read audio clip {seg.tts_audio_path}: {e}")
                continue

            orig_duration_ms = int((seg.end - seg.start) * 1000)
            actual_duration_ms = len(clip)

            if orig_duration_ms <= 0:
                orig_duration_ms = actual_duration_ms

            # Compute speed adjustment factor
            ratio = actual_duration_ms / orig_duration_ms

            if ratio > 1.05:
                # Speech is longer than original segment: speed up to fit
                target_speed = min(ratio, self.max_speed_factor)
                adjusted_clip = change_audio_speed(clip, speed=target_speed)
                # If still slightly exceeds segment end, trim to avoid clashing with next dialogue
                max_allowed_len = orig_duration_ms + 300  # allow 300ms overlap max
                if len(adjusted_clip) > max_allowed_len:
                    adjusted_clip = adjusted_clip[:max_allowed_len]
            elif ratio < 0.75:
                # Speech is much shorter: slow down slightly for natural cadence
                target_speed = max(ratio, self.min_speed_factor)
                adjusted_clip = change_audio_speed(clip, speed=target_speed)
            else:
                adjusted_clip = clip

            start_pos_ms = int(seg.start * 1000)
            # Overlay onto master track
            master_track = master_track.overlay(adjusted_clip, position=start_pos_ms)

        # Export assembled dubbed voice track
        master_track.export(str(output_file), format="wav")
        logger.info(f"Synchronized audio track exported to: {output_file}")
        return output_file
