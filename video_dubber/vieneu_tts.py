"""
VieNeu-TTS Integration Module (High-Fidelity Turbo & Nano)
Supports full set of Adam voices:
- 'Adam bựa': Nam · Bắc · Phong cách Review phim / Meme TikTok đỉnh cao
- 'Adam': Nam · Nam · Giọng đọc tự nhiên, cuốn hút
"""
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

_VIENEU_TURBO_INSTANCE = None
_VIENEU_NANO_INSTANCE = None


def get_vieneu_engine(mode: str = "v3turbo"):
    """
    Singleton getter for Vieneu instance.
    Prefers v3turbo for 48kHz audio and all 25 voices including 'Adam bựa'.
    Falls back to v3nano if turbo fails.
    """
    global _VIENEU_TURBO_INSTANCE, _VIENEU_NANO_INSTANCE
    from vieneu import Vieneu

    if mode == "v3turbo":
        if _VIENEU_TURBO_INSTANCE is None:
            try:
                logger.info("Initializing VieNeu-TTS Turbo (48kHz, 25 preset voices)...")
                _VIENEU_TURBO_INSTANCE = Vieneu(mode="v3turbo")
            except Exception as e:
                logger.warning(f"Failed to initialize VieNeu Turbo ({e}), falling back to v3nano.")
                return get_vieneu_engine(mode="v3nano")
        return _VIENEU_TURBO_INSTANCE
    else:
        if _VIENEU_NANO_INSTANCE is None:
            logger.info("Initializing VieNeu-TTS Nano (24kHz)...")
            _VIENEU_NANO_INSTANCE = Vieneu(mode="v3nano")
        return _VIENEU_NANO_INSTANCE


def list_vieneu_voices() -> List[Tuple[str, str]]:
    """
    Returns list of (label, voice_id) available in VieNeu-TTS.
    """
    engine = get_vieneu_engine()
    return engine.list_preset_voices()


def generate_vieneu_speech(
    text: str,
    voice: str = "Adam bựa",
    output_path: Union[str, Path] = "output.wav",
) -> Path:
    """
    Synthesizes Vietnamese speech using VieNeu-TTS.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clean_voice = voice.replace("vieneu:", "").strip()
    if not clean_voice:
        clean_voice = "Adam bựa"

    engine = get_vieneu_engine(mode="v3turbo")
    logger.info(f"Synthesizing text with VieNeu-TTS voice '{clean_voice}'...")
    audio = engine.infer(text, voice=clean_voice)

    # Save as WAV
    wav_path = output_path.with_suffix(".wav")
    engine.save(audio, str(wav_path))

    # Convert to MP3 if requested
    if output_path.suffix.lower() == ".mp3":
        from pydub import AudioSegment
        sound = AudioSegment.from_wav(str(wav_path))
        sound.export(str(output_path), format="mp3")
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass
        return output_path

    return wav_path
