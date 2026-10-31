"""
Audio Extraction module from input video
"""
import logging
import subprocess
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def extract_audio(
    video_path: Union[str, Path],
    output_audio_path: Union[str, Path],
    sample_rate: int = 16000,
) -> Path:
    """
    Extracts audio track from a video file and converts it into 16kHz mono WAV.
    Tries ffmpeg CLI first, falls back to MoviePy if ffmpeg CLI is unavailable.
    """
    video_path = Path(video_path)
    output_audio_path = Path(output_audio_path)
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    logger.info(f"Extracting audio from {video_path.name} -> {output_audio_path.name}...")

    # Method 1: Try ffmpeg command directly
    try:
        cmd = [
            "ffmpeg",
            "-y",  # overwrite output
            "-i", str(video_path),
            "-vn",  # no video
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",  # mono
            str(output_audio_path),
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        logger.info("Audio extracted successfully using FFmpeg CLI.")
        return output_audio_path
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.info("FFmpeg CLI not found or failed, falling back to MoviePy...")

    # Method 2: Fallback to MoviePy
    try:
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(str(video_path))
        if video.audio is None:
            raise ValueError(f"The video '{video_path.name}' has no audio track!")
        
        video.audio.write_audiofile(
            str(output_audio_path),
            fps=sample_rate,
            nbytes=2,
            codec="pcm_s16le",
            ffmpeg_params=["-ac", "1"],
            logger=None,
        )
        video.close()
        logger.info("Audio extracted successfully using MoviePy.")
        return output_audio_path
    except Exception as e:
        logger.error(f"Failed to extract audio with MoviePy: {e}")
        raise RuntimeError(
            f"Could not extract audio from {video_path}. Make sure FFmpeg is installed or MoviePy is working."
        ) from e
