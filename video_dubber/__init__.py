"""
Video Dubber - AI Automated Video Dubbing Pipeline in Python
"""

from .pipeline import VideoDubberPipeline
from .extractor import extract_audio
from .transcriber import Transcriber, Segment
from .translator import Translator
from .tts import TTSService
from .synchronizer import AudioSynchronizer
from .merger import VideoMerger

__all__ = [
    "VideoDubberPipeline",
    "extract_audio",
    "Transcriber",
    "Segment",
    "Translator",
    "TTSService",
    "AudioSynchronizer",
    "VideoMerger",
]
