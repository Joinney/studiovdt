"""
Video and Audio Merging Module
Combines the synchronized dubbed audio with video, with background audio ducking.
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, Union
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class VideoMerger:
    def __init__(self, original_audio_volume: float = 0.15):
        """
        original_audio_volume: 0.0 means mute original audio entirely.
                               0.15 keeps original audio at 15% volume as background ambiance/music.
        """
        self.original_audio_volume = max(0.0, min(1.0, original_audio_volume))

    def mix_audios(
        self,
        original_audio_path: Union[str, Path],
        dubbed_audio_path: Union[str, Path],
        output_mixed_audio_path: Union[str, Path],
    ) -> Path:
        """
        Mixes original audio (attenuated for ducking) with dubbed audio.
        """
        output_mixed_audio_path = Path(output_mixed_audio_path)
        output_mixed_audio_path.parent.mkdir(parents=True, exist_ok=True)

        dubbed_sound = AudioSegment.from_file(dubbed_audio_path)

        if self.original_audio_volume <= 0.01:
            # Pure dubbed track without original audio
            dubbed_sound.export(str(output_mixed_audio_path), format="wav")
            return output_mixed_audio_path

        try:
            original_sound = AudioSegment.from_file(original_audio_path)
            # Volume reduction in dB: 20 * log10(volume_fraction)
            import math
            gain_reduction_db = 20 * math.log10(self.original_audio_volume)
            attenuated_orig = original_sound + gain_reduction_db

            # Overlay dubbed voice over attenuated background
            mixed = attenuated_orig.overlay(dubbed_sound)
            mixed.export(str(output_mixed_audio_path), format="wav")
            logger.info("Mixed background audio with dubbed voice successfully.")
            return output_mixed_audio_path
        except Exception as e:
            logger.warning(f"Audio mixing failed ({e}), using dubbed audio only.")
            dubbed_sound.export(str(output_mixed_audio_path), format="wav")
            return output_mixed_audio_path

    def merge_video(
        self,
        video_path: Union[str, Path],
        audio_path: Union[str, Path],
        output_video_path: Union[str, Path],
    ) -> Path:
        """
        Merges final mixed audio into the original video container.
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        output_video_path = Path(output_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Merging final audio into {video_path.name} -> {output_video_path.name}...")

        # Method 1: Try ffmpeg directly (fastest, preserves video quality without re-encoding)
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",       # Stream copy video without re-encoding
                "-c:a", "aac",        # AAC audio codec
                "-b:a", "192k",
                "-map", "0:v:0",      # Video from first input
                "-map", "1:a:0",      # Audio from second input
                "-shortest",
                str(output_video_path),
            ]
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info("Video and audio merged successfully using FFmpeg CLI.")
            return output_video_path
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.info("FFmpeg CLI not available or failed, falling back to MoviePy...")

        # Method 2: MoviePy fallback
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip

            video = VideoFileClip(str(video_path))
            new_audio = AudioFileClip(str(audio_path))

            final_video = video.set_audio(new_audio)
            final_video.write_videofile(
                str(output_video_path),
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            video.close()
            new_audio.close()
            final_video.close()
            logger.info("Video and audio merged successfully using MoviePy.")
            return output_video_path
        except Exception as e:
            logger.error(f"Failed to merge video with MoviePy: {e}")
            raise RuntimeError(f"Could not merge video and audio: {e}") from e
